"""
Runs the Fraud/Anomaly Risk Signals Dify app across every claim that's already
been assessed (assessment_logs), persisting each result to fraud_risk_checks —
the same table the Audit Log's "Check for fraud signals" button writes to.

Unlike the production *_Assess_Claim workflows, the Fraud app doesn't persist
its own output — that's done entirely by the frontend (Audit Log button ->
runFraudRiskCheck -> createFraudRiskCheck), so this script does both steps
itself: call Dify, then POST the parsed result to MCP's /fraud-risk-checks.

Uses run_evaluation.py's streaming-mode Dify call (_call_dify_workflow) rather
than blocking mode — the Fraud workflow chains ~5 nodes (fetch claim, resolve
ID, fetch history, LLM, serialize), enough to intermittently exceed an
intermediate proxy's idle-read timeout in blocking mode, same issue already
hit and fixed for the "combined" assessment pipeline.

Usage:
    python evaluation/backfill_fraud_checks.py            # real run
    python evaluation/backfill_fraud_checks.py --dry-run  # print the plan only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402
from evaluation.run_evaluation import _call_dify_workflow  # noqa: E402

ENV_FILE = REPO_ROOT / "mcp_server" / ".env"
load_dotenv(ENV_FILE)

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000")
DIFY_FRAUD_KEY = os.getenv("DIFY_FRAUD_KEY", "")


def _http_get_json(path: str) -> list[dict]:
    with urllib.request.urlopen(f"{MCP_BASE_URL}{path}") as r:
        return json.load(r)


def _http_post_json(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{MCP_BASE_URL}{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def run_fraud_check(claim_id: str, timeout: int = 120) -> dict:
    resp = _call_dify_workflow(DIFY_FRAUD_KEY, claim_id, timeout=timeout)
    data = resp.get("data", {})
    if data.get("status") != "succeeded":
        raise RuntimeError(data.get("error") or f"workflow status={data.get('status')}")
    return json.loads(data["outputs"]["answer"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill fraud_risk_checks across all already-assessed claims")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan, don't call Dify")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to sleep between calls")
    args = parser.parse_args()

    if not DIFY_FRAUD_KEY and not args.dry_run:
        print("DIFY_FRAUD_KEY is not set in mcp_server/.env — aborting.")
        return

    assessed = _http_get_json("/assessment-logs?limit=1000")
    assessed_ids = sorted({d["claim_id"] for d in assessed if d.get("claim_id")})

    already_checked = _http_get_json("/fraud-risk-checks?limit=1000")
    checked_ids = {d["claim_id"] for d in already_checked if d.get("claim_id")}

    plan = [cid for cid in assessed_ids if cid not in checked_ids]
    print(f"Assessed claims: {len(assessed_ids)}, already fraud-checked: {len(checked_ids)}")
    print(f"Planned: {len(plan)} new fraud checks\n")

    if args.dry_run:
        for cid in plan:
            print(f"  {cid}")
        return

    ok, failed = 0, 0
    for i, claim_id in enumerate(plan, start=1):
        print(f"[{i}/{len(plan)}] {claim_id}...", end=" ", flush=True)
        try:
            result = run_fraud_check(claim_id)
            _http_post_json("/fraud-risk-checks", {
                "claim_id": claim_id,
                "risk_level": result["risk_level"],
                "flags": result.get("flags", []),
                "recommended_action": result.get("recommended_action"),
                "checked_by": "backfill_fraud_checks_script",
            })
            print(f"{result['risk_level']} ({result.get('recommended_action')})")
            ok += 1
        except Exception as exc:
            print(f"FAILED: {exc}")
            failed += 1
        time.sleep(args.delay)

    print(f"\n{'=' * 60}")
    print(f"  Done: {ok} succeeded, {failed} failed, out of {len(plan)} planned")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
