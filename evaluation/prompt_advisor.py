"""
Maps the weakest-scoring LLM-as-Judge dimension (from recent assessment_logs, the real
production audit trail — not the research-study MLflow runs, which don't log judge scores)
to a likely responsible node, drafts an improved prompt, and submits it for governance
approval via the existing DSL Change Management flow. Never auto-applies.

No live LLM call drafts the improvement — there's no OpenAI key available, and none of the
6 Dify apps built tonight are suited for free-form prompt-authoring (they're all hardcoded
for claim assessment or research tasks, not general text generation). Instead, this applies
a deterministic, heuristic-based augmentation per weak dimension — the same kind of targeted
fix applied by hand throughout tonight's build (see the plan file), just automated. This still
fully respects the governance design: the suggestion lands as a PENDING row in change_approvals
requiring a human sign-off, exactly like any other tracked change.

Usage:
    python evaluation/prompt_advisor.py --workflow life_assess_claim
    python evaluation/prompt_advisor.py --workflow all
    python evaluation/prompt_advisor.py --workflow life_assess_claim --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402
from dsl_manager.parser import hash_content  # noqa: E402
from dsl_manager.diff import compute_diff  # noqa: E402

ENV_FILE = REPO_ROOT / "mcp_server" / ".env"
load_dotenv(ENV_FILE)

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8000")

WORKFLOW_DIFY_NAMES = {
    "life_assess_claim": "Life_Assess_Claim",
    "health_assess_claim": "Health_Assess_Claim",
    "ci_assess_claim": "CI_Assess_Claim",
    "disability_assess_claim": "Disability_Assess_Claim",
}

JUDGE_SCORE_FIELDS = {
    "completeness": "judge_completeness_score",
    "consistency": "judge_consistency_score",
    "hallucination_risk": "judge_hallucination_risk_score",
    "clarity": "judge_clarity_score",
}

DIMENSION_TO_NODES = {
    "hallucination_risk": ["rule_by_rule_eligibility_check", "policy_document_analysis"],
    "clarity": ["format_final_report"],
    "completeness": ["synthesize_final_verdict"],
    "consistency": ["synthesize_final_verdict"],
}

DIMENSION_AUGMENTATIONS = {
    "hallucination_risk": (
        "\n\nAdditional guardrail (auto-suggested by prompt_advisor.py — weakest judged "
        "dimension: hallucination_risk): cite only rule IDs, clause references, and document "
        "types that literally appear in the provided input data — never invent, infer, or "
        "assume an identifier that isn't explicitly present."
    ),
    "clarity": (
        "\n\nAdditional guardrail (auto-suggested by prompt_advisor.py — weakest judged "
        "dimension: clarity): use short, plain-language sentences in the summary sections "
        "meant for a human reader, and avoid unnecessary jargon or dense clause-numbering."
    ),
    "completeness": (
        "\n\nAdditional guardrail (auto-suggested by prompt_advisor.py — weakest judged "
        "dimension: completeness): explicitly address every mandatory rule and every key "
        "data field provided — do not omit a rule or field from your rationale just because "
        "it passed without issue."
    ),
    "consistency": (
        "\n\nAdditional guardrail (auto-suggested by prompt_advisor.py — weakest judged "
        "dimension: consistency): before finalizing, double-check that your stated "
        "recommendation, cited rule failures, and summary counts are mutually consistent "
        "with each other and with the upstream rule-check output."
    ),
}


def _get(path: str) -> list | dict:
    with urllib.request.urlopen(f"{MCP_BASE_URL}{path}") as r:
        return json.load(r)


def _post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{MCP_BASE_URL}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def _init_mlflow():
    import mlflow
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("DATABRICKS_HOST / DATABRICKS_TOKEN missing from mcp_server/.env")
    os.environ["DATABRICKS_HOST"] = host
    os.environ["DATABRICKS_TOKEN"] = token
    mlflow.set_tracking_uri("databricks")


def find_weakest_dimension(workflow_type: str, limit: int = 20) -> tuple[str, float, dict]:
    """Averages the 4 judge scores across recent assessment_logs for this workflow_type,
    returns the weakest dimension name, its average, and all 4 averages for context."""
    logs = _get(f"/assessment-logs?workflow_type={workflow_type}&limit={limit}")
    if not logs:
        raise RuntimeError(f"No assessment_logs found for workflow_type={workflow_type}")

    averages = {}
    for dim, field in JUDGE_SCORE_FIELDS.items():
        values = [log[field] for log in logs if log.get(field) is not None]
        averages[dim] = sum(values) / len(values) if values else None

    scored = {d: v for d, v in averages.items() if v is not None}
    if not scored:
        raise RuntimeError(f"No judge scores found in assessment_logs for workflow_type={workflow_type}")

    weakest = min(scored, key=scored.get)
    return weakest, scored[weakest], averages


def find_node_id(workflow_name: str, node_name: str) -> str | None:
    nodes = _get(f"/workflow-nodes?workflow_name={workflow_name}&node_type=llm")
    for n in nodes:
        if n["node_name"] == node_name:
            return n["node_id"]
    return None


def draft_improved_prompt(workflow_type: str, node_name: str, dimension: str, dry_run: bool) -> dict:
    import mlflow.genai as genai
    from mlflow.tracking import MlflowClient

    prompt_name = f"workspace.default.{workflow_type}_{node_name}_v1_0"

    # load_prompt(name) with no version tries to resolve an implicit "latest" alias, which
    # isn't set on these prompts (Databricks UC doesn't create one automatically on
    # register_prompt) — it raises a RestException rather than returning None, so
    # allow_missing doesn't help here. Look up the actual latest version number first.
    try:
        versions = MlflowClient().search_prompt_versions(prompt_name)
    except Exception:
        return {"node_name": node_name, "skipped": "prompt not found in registry"}
    if not versions:
        return {"node_name": node_name, "skipped": "prompt not found in registry"}
    latest_version = max(v.version for v in versions)

    current = genai.load_prompt(prompt_name, version=latest_version)

    old_content = current.template
    new_content = old_content + DIMENSION_AUGMENTATIONS[dimension]
    new_hash = hash_content(new_content)
    diff = compute_diff(old_content, new_content, node_name, "llm")

    workflow_name = WORKFLOW_DIFY_NAMES[workflow_type]
    node_id = find_node_id(workflow_name, node_name)

    result = {
        "node_name": node_name,
        "workflow_name": workflow_name,
        "prompt_registry_source": f"{prompt_name} (v{current.version})",
        "node_id_found": node_id is not None,
        "diff_preview": diff[:500],
    }

    if dry_run:
        result["dry_run"] = True
        return result

    approval = _post("/change-approvals", {
        "node_id": node_id,
        "workflow_name": workflow_name,
        "node_name": node_name,
        "node_type": "llm",
        "changed_by": "prompt_advisor_agent",
        "diff_content": diff,
        "new_content": new_content,
        "new_hash": new_hash,
    })
    result["approval_id"] = approval.get("approval_id")
    result["status"] = approval.get("status")
    return result


def run_for_workflow(workflow_type: str, dry_run: bool) -> None:
    print(f"\n{'=' * 60}\n  {workflow_type}\n{'=' * 60}")
    weakest, score, all_scores = find_weakest_dimension(workflow_type)
    print(f"  Judge score averages: {all_scores}")
    print(f"  Weakest dimension: {weakest} (avg {score:.2f}/5.0)")

    nodes = DIMENSION_TO_NODES[weakest]
    print(f"  Mapped to node(s): {nodes}")

    for node_name in nodes:
        result = draft_improved_prompt(workflow_type, node_name, weakest, dry_run)
        print(f"\n  --- {node_name} ---")
        for k, v in result.items():
            print(f"    {k}: {v}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest a targeted prompt improvement based on judge scores")
    parser.add_argument("--workflow", required=True, choices=list(WORKFLOW_DIFY_NAMES) + ["all"])
    parser.add_argument("--dry-run", action="store_true", help="Preview without submitting to change_approvals")
    args = parser.parse_args()

    if not args.dry_run:
        _init_mlflow()
    else:
        # load_prompt still needs a tracking URI even to read, just not Databricks creds validation upfront
        _init_mlflow()

    workflows = list(WORKFLOW_DIFY_NAMES) if args.workflow == "all" else [args.workflow]
    for wf in workflows:
        try:
            run_for_workflow(wf, args.dry_run)
        except Exception as exc:
            print(f"\n  FAILED for {wf}: {exc}")


if __name__ == "__main__":
    main()
