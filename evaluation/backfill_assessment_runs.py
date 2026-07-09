"""
Runs a batch of previously-never-assessed claims through the real production
*_Assess_Claim Dify workflows, so assessment_logs (and therefore the Audit Log
and Dashboard) reflects more than the ~16 claims that got heavily re-tested
during earlier iterative debugging this session (148 rows, only 16 distinct
claim_ids). Each of the 4 production workflows writes to assessment_logs
itself via its own write_assessment_log node — this script only needs to
trigger the workflow, not parse/score/log anything separately.

Reuses run_evaluation.py's Dify-calling (_call_dify_workflow, streaming mode)
and combined-output-parsing (_parse_combined) logic rather than reimplementing
it — same reasoning as dsl_manager's "one implementation, multiple entry
points" convention.

Usage:
    python evaluation/backfill_assessment_runs.py --per-domain 30            # real run
    python evaluation/backfill_assessment_runs.py --per-domain 30 --dry-run  # print the plan only
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402
from evaluation.run_evaluation import _call_dify_workflow, _parse_combined, DOMAIN_KEYS  # noqa: E402

ENV_FILE = REPO_ROOT / "mcp_server" / ".env"
load_dotenv(ENV_FILE)

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000")

CLAIM_TYPES = ["life", "health", "critical_illness", "disability"]

random.seed(42)  # reproducible sample, matches generate_data.py's convention


def _http_get_json(path: str) -> list[dict]:
    with urllib.request.urlopen(f"{MCP_BASE_URL}{path}") as r:
        return json.load(r)


def already_assessed_claim_ids() -> set[str]:
    logs = _http_get_json("/assessment-logs?limit=1000")
    return {log["claim_id"] for log in logs if log.get("claim_id")}


def pick_claims(claim_type: str, n: int, exclude: set[str]) -> list[str]:
    claims = _http_get_json(f"/claims?claim_type={claim_type}&limit=1000")
    candidates = [c["claim_id"] for c in claims if c["claim_id"] not in exclude]
    random.shuffle(candidates)
    return candidates[:n]


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill assessment_logs with previously-unassessed claims")
    parser.add_argument("--per-domain", type=int, default=30, help="How many new claims to assess per domain")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan, don't call Dify")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to sleep between calls")
    args = parser.parse_args()

    exclude = already_assessed_claim_ids()
    print(f"Already assessed: {len(exclude)} distinct claims — excluding from selection.\n")

    plan: list[tuple[str, str]] = []
    for claim_type in CLAIM_TYPES:
        picked = pick_claims(claim_type, args.per_domain, exclude)
        print(f"{claim_type}: {len(picked)} new claims selected (requested {args.per_domain})")
        plan.extend((claim_type, cid) for cid in picked)

    print(f"\nTotal planned: {len(plan)} claims\n")
    if args.dry_run:
        for claim_type, cid in plan:
            print(f"  {claim_type}: {cid}")
        return

    ok, failed = 0, 0
    for i, (claim_type, claim_id) in enumerate(plan, start=1):
        api_key = os.getenv(DOMAIN_KEYS[claim_type])
        if not api_key:
            print(f"[{i}/{len(plan)}] {claim_id} ({claim_type}) — SKIPPED, no {DOMAIN_KEYS[claim_type]} set")
            failed += 1
            continue
        print(f"[{i}/{len(plan)}] {claim_id} ({claim_type})...", end=" ", flush=True)
        try:
            resp = _call_dify_workflow(api_key, claim_id, timeout=150)
            data = resp.get("data", {})
            if data.get("status") != "succeeded":
                print(f"WORKFLOW ERROR: {data.get('error')}")
                failed += 1
                continue
            rec, _, _, conf = _parse_combined(data.get("outputs", {}))
            print(f"{rec or '?'} ({conf or '?'})")
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
