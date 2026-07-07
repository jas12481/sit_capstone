"""
Runs the 3 product-capability apps (Missing_Documentation_Advisor, Fraud_Anomaly_Risk_Signals,
Explain_Assessment_Reasoning Mode A) against product_test_cases.json, scores each via
product_metrics.py, and logs every run to MLflow under a separate tag from the research study
(Claims_Assessment_Prompting_Study experiment stays the same — these are tagged
"product_capabilities_evaluation" to keep them distinguishable, not a different experiment,
since a separate experiment isn't clearly warranted for 15 runs and MLflowTracker is already
wired to one experiment name).

Reuses _call_dify_workflow from run_evaluation.py (streaming mode, browser User-Agent — same
Cloudflare bot-block and gateway-timeout fixes apply here, since these are also Workflow-mode
Dify apps) rather than duplicating that logic.

Usage:
    python evaluation/run_product_evaluation.py                 # all 15 cases
    python evaluation/run_product_evaluation.py --app fraud      # only one app's cases
    python evaluation/run_product_evaluation.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402
from mlflow_tracker import MLflowTracker  # noqa: E402
from evaluation.run_evaluation import _call_dify_workflow  # noqa: E402
from evaluation.product_metrics import (  # noqa: E402
    missing_docs_precision_recall,
    all_requirements_met_correct,
    fraud_risk_level_correct,
    fraud_flag_precision_recall,
    explanation_faithfulness,
)

ENV_FILE = REPO_ROOT / "mcp_server" / ".env"
load_dotenv(ENV_FILE)

APP_KEYS = {
    "missing_docs": "DIFY_MISSING_DOCS_KEY",
    "fraud": "DIFY_FRAUD_KEY",
    "explain": "DIFY_EXPLAIN_KEY",
}
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"


def _run_app(app: str, claim_id: str, dry_run: bool) -> dict:
    api_key = os.getenv(APP_KEYS[app])
    if dry_run:
        return {"dry_run": True, "key_set": bool(api_key)}
    if not api_key:
        raise RuntimeError(f"{APP_KEYS[app]} not set in mcp_server/.env")
    resp = _call_dify_workflow(api_key, claim_id, timeout=180)
    return resp.get("data", {}).get("outputs", {}) or {}


def _parse_json_answer(outputs: dict) -> dict:
    raw = outputs.get("answer", "") or ""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def run_missing_docs_case(case: dict, dry_run: bool) -> dict:
    result = {"test_id": case["test_id"], "app": "missing_docs", "claim_id": case["claim_id"]}
    if dry_run:
        result.update(_run_app("missing_docs", case["claim_id"], dry_run=True))
        return result

    outputs = _run_app("missing_docs", case["claim_id"], dry_run=False)
    parsed = _parse_json_answer(outputs)
    predicted_missing = [d.get("document_type") for d in parsed.get("missing_documents", []) if d.get("document_type")]

    pr = missing_docs_precision_recall(predicted_missing, case["expected_missing_document_types"])
    met_correct = all_requirements_met_correct(parsed.get("all_requirements_met"), case["expected_all_requirements_met"])

    result.update({
        "predicted_missing": predicted_missing,
        "expected_missing": case["expected_missing_document_types"],
        "precision": pr["precision"], "recall": pr["recall"],
        "all_requirements_met_correct": met_correct,
        "raw_response": json.dumps(parsed),
    })
    return result


def run_fraud_case(case: dict, dry_run: bool) -> dict:
    result = {"test_id": case["test_id"], "app": "fraud", "claim_id": case["claim_id"]}
    if dry_run:
        result.update(_run_app("fraud", case["claim_id"], dry_run=True))
        return result

    outputs = _run_app("fraud", case["claim_id"], dry_run=False)
    parsed = _parse_json_answer(outputs)
    predicted_risk = parsed.get("risk_level")
    predicted_flags = parsed.get("flags", [])

    risk_correct = fraud_risk_level_correct(predicted_risk, case["expected_risk_level"])
    flag_pr = fraud_flag_precision_recall(predicted_flags, case.get("expected_signal_keywords", []))

    result.update({
        "predicted_risk_level": predicted_risk,
        "expected_risk_level": case["expected_risk_level"],
        "risk_level_correct": risk_correct,
        "flag_precision": flag_pr["precision"], "flag_recall": flag_pr["recall"],
        "raw_response": json.dumps(parsed),
    })
    return result


def run_explain_case(case: dict, dry_run: bool) -> dict:
    result = {"test_id": case["test_id"], "app": "explain", "claim_id": case["claim_id"]}
    if dry_run:
        result.update(_run_app("explain", case["claim_id"], dry_run=True))
        return result

    outputs = _run_app("explain", case["claim_id"], dry_run=False)
    explanation = outputs.get("explanation_existing", "") or ""
    mode_b_fired = bool(outputs.get("explanation_fresh")) and not explanation

    faithfulness = explanation_faithfulness(
        explanation, case["expected_recommendation"], case["expected_mandatory_rules_failed"]
    )

    result.update({
        "mode_b_fired_unexpectedly": mode_b_fired,
        "is_faithful": faithfulness["is_faithful"],
        "recommendation_mentioned": faithfulness["recommendation_mentioned"],
        "no_contradicting_recommendation": faithfulness["no_contradicting_recommendation"],
        "raw_response": explanation,
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 3 product-capability evaluations")
    parser.add_argument("--app", choices=["missing_docs", "fraud", "explain"], help="Only run this app's cases")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(REPO_ROOT / "evaluation" / "product_test_cases.json") as f:
        data = json.load(f)

    runners = [
        ("missing_docs", data["missing_documentation_advisor_cases"], run_missing_docs_case),
        ("fraud", data["fraud_anomaly_cases"], run_fraud_case),
        ("explain", data["explain_assessment_reasoning_mode_a_cases"], run_explain_case),
    ]
    if args.app:
        runners = [r for r in runners if r[0] == args.app]

    tracker = None
    if not args.dry_run:
        tracker = MLflowTracker()
        tracker.initialize()

    results = []
    planned = sum(len(cases) for _, cases, _ in runners)
    done = 0

    for app_name, cases, run_fn in runners:
        for case in cases:
            done += 1
            print(f"[{done}/{planned}] {case['test_id']}...", end=" ")
            try:
                r = run_fn(case, args.dry_run)
                results.append(r)
                if args.dry_run:
                    print(f"DRY RUN (key {'SET' if r.get('key_set') else 'MISSING'})")
                else:
                    print("done")
                    if tracker:
                        run_name = f"product_{r['test_id']}"
                        metrics = {k: v for k, v in r.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
                        params = {k: str(v) for k, v in r.items() if isinstance(v, (str, bool)) and k != "raw_response"}
                        tracker.log_evaluation_run(
                            run_name=run_name,
                            params={**params, "policy_type": "product_evaluation"},
                            metrics=metrics,
                            artifacts={"raw_response": r.get("raw_response", "")},
                            tags={"app": app_name, "eval_type": "product_capabilities_evaluation"},
                        )
            except Exception as exc:
                print(f"FAILED: {exc}")
                results.append({"test_id": case["test_id"], "app": app_name, "error": str(exc)})

    if args.dry_run:
        print(f"\n{planned} cases planned (dry run, nothing executed).")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = RESULTS_DIR / f"product_run_{stamp}.json"
    csv_path = RESULTS_DIR / f"product_run_{stamp}.csv"

    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted({k for r in results for k in r.keys()}))
        writer.writeheader()
        writer.writerows(results)

    n_failed = sum(1 for r in results if "error" in r)
    print(f"\n{'=' * 60}")
    print(f"  Total cases: {len(results)} | Failed calls: {n_failed}")
    for app_name, cases, _ in runners:
        app_results = [r for r in results if r.get("app") == app_name and "error" not in r]
        if app_name == "missing_docs":
            n = sum(1 for r in app_results if r.get("all_requirements_met_correct"))
            print(f"    missing_docs: {n}/{len(app_results)} all_requirements_met correct")
        elif app_name == "fraud":
            n = sum(1 for r in app_results if r.get("risk_level_correct"))
            print(f"    fraud: {n}/{len(app_results)} risk_level correct")
        elif app_name == "explain":
            n = sum(1 for r in app_results if r.get("is_faithful"))
            print(f"    explain: {n}/{len(app_results)} faithful")
    print(f"  Results written to {json_path} and {csv_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
