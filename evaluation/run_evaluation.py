"""
Runs the 4-strategy (Direct/CoT/Structured/Combined) recommendation-accuracy study across
the 20 test_claims.json claims, scores each via metrics.py, and logs every run to MLflow.

Design notes (see PROJECT_CONTEXT.md §12/§17 and the plan file for full background):
- Direct_Research/CoT_Research/Structured_Research take {claim_id, query} as inputs and fetch
  claim/policy/rules themselves internally (via their own HTTP node) — this script does NOT
  fetch that data to hand to Dify, it only fetches it separately for *scoring* purposes
  (real eligibility_rules / policy_text to check for hallucinated citations).
- "combined" calls the actual per-domain production *_Assess_Claim workflow directly (bypassing
  the orchestrator), using a domain-specific key — DIFY_LIFE_ASSESS_KEY etc.
- domain_mismatch test cases (4 of the 20) are only meaningful for "combined" — see
  applicable_strategies in test_claims.json. Calling the wrong domain's workflow doesn't 404
  (the claim_id is real) — it just checks the claim against the wrong policy_type's rules,
  which should produce a graceful REJECT rather than a clean approval. An actual HTTP/network
  failure is also accepted (recorded as "ERROR").
- Real run count is 16*4 + 4*1 = 68, not a round 80 — the mismatch entries only run once each
  (combined only), not once per strategy.

Usage:
    python evaluation/run_evaluation.py                      # full 68-run study
    python evaluation/run_evaluation.py --claim life_approve  # single test_id, all applicable strategies
    python evaluation/run_evaluation.py --dry-run             # print what would run, no Dify/MLflow calls
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402
from mlflow_tracker import MLflowTracker  # noqa: E402
from evaluation.metrics import (  # noqa: E402
    check_recommendation_correct,
    confidence_to_numeric,
    count_hallucinated_rules,
    extract_cited_rule_ids_from_text,
    extract_recommendation_from_text,
)

ENV_FILE = REPO_ROOT / "mcp_server" / ".env"
load_dotenv(ENV_FILE)

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000")
DIFY_API_BASE = os.getenv("DIFY_URL", "https://api.dify.ai")

STRATEGY_KEYS = {
    "direct": "DIFY_DIRECT_RESEARCH_KEY",
    "cot": "DIFY_COT_RESEARCH_KEY",
    "structured": "DIFY_STRUCTURED_RESEARCH_KEY",
}
DOMAIN_KEYS = {
    "life": "DIFY_LIFE_ASSESS_KEY",
    "health": "DIFY_HEALTH_ASSESS_KEY",
    "critical_illness": "DIFY_CI_ASSESS_KEY",
    "disability": "DIFY_DISABILITY_ASSESS_KEY",
}
PROMPT_VERSION_LABELS = {
    "direct": "direct_research_v1_0",
    "cot": "cot_research_v1_0",
    "structured": "structured_research_v1_0",
    "combined": "combined_v1_0",
}
STRATEGIES = ["direct", "cot", "structured", "combined"]

RESULTS_DIR = REPO_ROOT / "evaluation" / "results"


def _http_get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{MCP_BASE_URL}{path}") as r:
        return json.load(r)


def _call_dify_workflow(api_key: str, claim_id: str, timeout: int = 120) -> dict:
    """POST to Dify's workflow API (not chat-messages — these are Workflow-mode apps)."""
    body = json.dumps({
        "inputs": {"claim_id": claim_id, "query": "assess this claim"},
        "response_mode": "blocking",
        "user": "run_evaluation_script",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{DIFY_API_BASE}/v1/workflows/run",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Cloudflare (fronting api.dify.ai) blocks urllib's default User-Agent as a bot
            # signature (403, "error code: 1010") — a normal browser-like UA avoids that.
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _parse_direct_or_cot(outputs: dict) -> tuple[str | None, list[str], str]:
    text = outputs.get("answer", "") or ""
    return extract_recommendation_from_text(text), extract_cited_rule_ids_from_text(text), text


def _parse_structured(outputs: dict) -> tuple[str | None, list[str], str, str | None]:
    raw = outputs.get("answer", "") or ""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, [], raw, None
    return parsed.get("recommendation"), parsed.get("cited_rule_ids", []), raw, parsed.get("confidence")


def _parse_combined(outputs: dict) -> tuple[str | None, list[str], str, str | None]:
    raw = outputs.get("final_report", "") or ""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, [], raw, None
    verdict = parsed.get("answer", {}).get("verdict", {}) if isinstance(parsed.get("answer"), dict) else {}
    rule_summary = parsed.get("answer", {}).get("rule_summary", "") if isinstance(parsed.get("answer"), dict) else ""
    cited = extract_cited_rule_ids_from_text(rule_summary)
    return verdict.get("recommendation"), cited, raw, verdict.get("confidence_level")


def run_one(test_case: dict, strategy: str, real_rules_cache: dict, dry_run: bool) -> dict:
    claim_id = test_case["claim_id"]
    policy_type = test_case["policy_type"]

    if strategy == "combined":
        domain = test_case.get("assess_via_domain", policy_type)
        key_name = DOMAIN_KEYS[domain]
    else:
        key_name = STRATEGY_KEYS[strategy]

    api_key = os.getenv(key_name)
    run_name = f"{strategy}_{policy_type}_{claim_id}"

    if dry_run:
        print(f"[DRY RUN] {run_name} -> key={key_name} ({'SET' if api_key else 'MISSING'})")
        return {"test_id": test_case["test_id"], "strategy": strategy, "run_name": run_name, "dry_run": True}

    if not api_key:
        raise RuntimeError(f"{key_name} not set in mcp_server/.env")

    raw_text = ""
    actual_confidence = None
    cited_rule_ids: list[str] = []
    try:
        # combined chains ~7 sequential LLM calls (rule check -> policy analysis -> verdict
        # synthesis -> judge -> report formatting -> suggestion context) vs. 1 for the other
        # strategies — a single direct call took ~37s, so give combined real headroom.
        call_timeout = 480 if strategy == "combined" else 120
        resp = _call_dify_workflow(api_key, claim_id, timeout=call_timeout)
        outputs = resp.get("data", {}).get("outputs", {}) or {}
        if strategy in ("direct", "cot"):
            actual_rec, cited_rule_ids, raw_text = _parse_direct_or_cot(outputs)
        elif strategy == "structured":
            actual_rec, cited_rule_ids, raw_text, actual_confidence = _parse_structured(outputs)
        else:
            actual_rec, cited_rule_ids, raw_text, actual_confidence = _parse_combined(outputs)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        actual_rec = "ERROR"
        raw_text = str(exc)

    expected_rec = test_case["expected_recommendation"]
    correct = check_recommendation_correct(actual_rec, expected_rec)

    real_rule_ids = real_rules_cache.setdefault(
        policy_type, [r["rule_id"] for r in _http_get_json(f"/eligibility-rules?policy_type={policy_type}")]
    )
    hallucinated = count_hallucinated_rules(cited_rule_ids, real_rule_ids)

    metrics = {
        "recommendation_correct": 1.0 if correct else 0.0,
        "hallucinated_rule_count": float(hallucinated),
        "cited_rule_count": float(len(cited_rule_ids)),
    }
    conf_numeric = confidence_to_numeric(actual_confidence)
    if conf_numeric is not None:
        metrics["confidence_numeric"] = conf_numeric

    params = {
        "policy_type": policy_type,
        "claim_id": claim_id,
        "strategy": strategy,
        "prompt_version": PROMPT_VERSION_LABELS[strategy],
        "expected_recommendation": expected_rec,
        "actual_recommendation": actual_rec or "PARSE_FAILED",
    }
    tags = {"test_id": test_case["test_id"], "scenario": test_case["scenario"][:250]}
    artifacts = {"raw_response": raw_text, "cited_rule_ids": cited_rule_ids}

    result = {
        "test_id": test_case["test_id"], "strategy": strategy, "run_name": run_name,
        "claim_id": claim_id, "policy_type": policy_type,
        "expected": expected_rec, "actual": actual_rec, "correct": correct,
        "hallucinated_rule_count": hallucinated, "confidence": actual_confidence,
    }

    tracker = run_one._tracker  # type: ignore[attr-defined]
    mlflow_run_id = tracker.log_evaluation_run(run_name=run_name, params=params, metrics=metrics,
                                                artifacts=artifacts, tags=tags)
    result["mlflow_run_id"] = mlflow_run_id
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 4-strategy recommendation-accuracy study")
    parser.add_argument("--claim", help="Only run this test_id (e.g. life_approve)")
    parser.add_argument("--strategy", choices=STRATEGIES, help="Only run this strategy (e.g. combined)")
    parser.add_argument("--dry-run", action="store_true", help="Print planned runs, no Dify/MLflow calls")
    args = parser.parse_args()

    with open(REPO_ROOT / "evaluation" / "test_claims.json") as f:
        test_claims = json.load(f)["test_claims"]
    if args.claim:
        test_claims = [t for t in test_claims if t["test_id"] == args.claim]
        if not test_claims:
            print(f"No test_id matching '{args.claim}'")
            return

    tracker = None
    if not args.dry_run:
        tracker = MLflowTracker()
        tracker.initialize()
        run_one._tracker = tracker  # type: ignore[attr-defined]

    real_rules_cache: dict[str, list[str]] = {}
    results = []
    strategies_per_test = [
        [s for s in t["applicable_strategies"] if not args.strategy or s == args.strategy]
        for t in test_claims
    ]
    planned = sum(len(s) for s in strategies_per_test)
    done = 0

    for t, strategies in zip(test_claims, strategies_per_test):
        for strategy in strategies:
            done += 1
            print(f"[{done}/{planned}] {t['test_id']} / {strategy}...", end=" ")
            try:
                r = run_one(t, strategy, real_rules_cache, args.dry_run)
                results.append(r)
                if not args.dry_run:
                    mark = "OK" if r["correct"] else "MISS"
                    print(f"{mark} (expected={r['expected']}, actual={r['actual']})")
            except Exception as exc:
                print(f"FAILED: {exc}")
                results.append({"test_id": t["test_id"], "strategy": strategy, "error": str(exc)})

    if args.dry_run:
        print(f"\n{planned} runs planned (dry run, nothing executed).")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = RESULTS_DIR / f"run_{stamp}.json"
    csv_path = RESULTS_DIR / f"run_{stamp}.csv"

    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted({k for r in results for k in r.keys()}))
        writer.writeheader()
        writer.writerows(results)

    n_correct = sum(1 for r in results if r.get("correct"))
    n_scored = sum(1 for r in results if "correct" in r)
    n_failed = sum(1 for r in results if "error" in r)
    by_strategy: dict[str, list[bool]] = {}
    for r in results:
        if "correct" in r:
            by_strategy.setdefault(r["strategy"], []).append(r["correct"])

    print(f"\n{'=' * 60}")
    print(f"  Overall accuracy: {n_correct}/{n_scored}")
    for strat, vals in by_strategy.items():
        print(f"    {strat:12s}: {sum(vals)}/{len(vals)} correct")
    print(f"  Failed calls: {n_failed}")
    print(f"  Results written to {json_path} and {csv_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
