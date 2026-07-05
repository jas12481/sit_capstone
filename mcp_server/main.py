from fastapi import FastAPI, Query, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from pathlib import Path
import os
import sys

# dsl_manager lives at the repo root, one level up from this file. Add it to
# sys.path so parsing/hashing/diffing logic has a single implementation
# shared by this server-side scan and the `dsl_manager` CLI — do not
# reimplement node extraction here.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dsl_manager.parser import parse_workflow, hash_content  # noqa: E402
from dsl_manager.diff import compute_diff  # noqa: E402

load_dotenv()

app = FastAPI(title="AIA Capstone MCP Server", version="2.1.0")

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "AIA MCP Server", "version": "2.1.0"}

# ── CLAIMS ────────────────────────────────────────────────────────────────────

@app.get("/claims")
def get_claims(
    claim_id: Optional[str] = Query(None),
    policy_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_officer: Optional[str] = Query(None),
    claim_type: Optional[str] = Query(None),
    limit: int = Query(50)
):
    query = supabase.table("claims").select("*")
    if claim_id:
        query = query.eq("claim_id", claim_id)
    if policy_id:
        query = query.eq("policy_id", policy_id)
    if customer_id:
        query = query.eq("customer_id", customer_id)
    if status:
        query = query.eq("status", status)
    if assigned_officer:
        query = query.eq("assigned_officer", assigned_officer)
    if claim_type:
        query = query.eq("claim_type", claim_type)
    query = query.limit(limit)
    response = query.execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="No claims found")
    return response.data

# ── POLICIES ──────────────────────────────────────────────────────────────────

@app.get("/policies")
def get_policies(
    policy_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    policy_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50)
):
    query = supabase.table("policies").select("*")
    if policy_id:
        query = query.eq("policy_id", policy_id)
    if customer_id:
        query = query.eq("customer_id", customer_id)
    if policy_type:
        query = query.eq("policy_type", policy_type)
    if status:
        query = query.eq("status", status)
    query = query.limit(limit)
    response = query.execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="No policies found")
    return response.data

# ── CLAIM DOMAIN LOOKUP ───────────────────────────────────────────────────────

@app.get("/claims/domain")
def get_claim_domain(claim_id: str = Query(...)):
    response = (
        supabase.table("claims")
        .select("claim_type, policy_id")
        .eq("claim_id", claim_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    claim = response.data[0]
    return {
        "claim_id": claim_id,
        "domain": claim["claim_type"],
        "linked_policy_id": claim["policy_id"]
    }

# ── ELIGIBILITY RULES ─────────────────────────────────────────────────────────

@app.get("/eligibility-rules")
def get_eligibility_rules(
    policy_type: Optional[str] = Query(None),
    is_mandatory: Optional[bool] = Query(None)
):
    query = supabase.table("eligibility_rules").select("*")
    if policy_type:
        query = query.eq("policy_type", policy_type)
    if is_mandatory is not None:
        query = query.eq("is_mandatory", is_mandatory)
    response = query.execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="No eligibility rules found")
    return response.data

# ── ASSESSMENT (combined claim + policy + rules) ──────────────────────────────

@app.get("/assessment")
def get_assessment_data(claim_id: str = Query(...)):
    claim_response = supabase.table("claims").select("*").eq("claim_id", claim_id).execute()
    if not claim_response.data:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    claim = claim_response.data[0]

    policy_response = supabase.table("policies").select("*").eq("policy_id", claim["policy_id"]).execute()
    if not policy_response.data:
        raise HTTPException(status_code=404, detail=f"Policy {claim['policy_id']} not found")
    policy = policy_response.data[0]

    rules_response = supabase.table("eligibility_rules").select("*").eq("policy_type", claim["claim_type"]).execute()

    return {
        "claim": claim,
        "policy": policy,
        "eligibility_rules": rules_response.data
    }

# ── CLAIM DOCUMENTS ───────────────────────────────────────────────────────────

@app.get("/claim-documents")
def get_claim_documents(
    claim_id: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None)
):
    query = supabase.table("claim_documents").select("*")
    if claim_id:
        query = query.eq("claim_id", claim_id)
    if document_type:
        query = query.eq("document_type", document_type)
    response = query.execute()
    # Unlike other list endpoints, an empty result is a legitimate state here
    # (a claim with no documents yet submitted) — return [] rather than 404.
    return response.data or []

# ── ASSESSMENT LOGS ───────────────────────────────────────────────────────────

class AssessmentLogCreate(BaseModel):
    claim_id: Optional[str] = None
    workflow_type: Optional[str] = None
    recommendation: Optional[str] = None
    confidence_level: Optional[str] = None
    mandatory_rules_failed: Optional[int] = None
    total_rules_passed: Optional[int] = None
    coverage_conclusion: Optional[str] = None
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    mlflow_run_id: Optional[str] = None
    judge_completeness_score: Optional[float] = None
    judge_consistency_score: Optional[float] = None
    judge_hallucination_risk_score: Optional[float] = None
    judge_clarity_score: Optional[float] = None
    judge_overall_score: Optional[float] = None


@app.post("/assessment-logs")
def create_assessment_log(log: AssessmentLogCreate):
    data = {k: v for k, v in log.dict().items() if v is not None}
    response = supabase.table("assessment_logs").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to write assessment log")
    return response.data[0]


@app.get("/assessment-logs")
def get_assessment_logs(
    workflow_type: Optional[str] = Query(None),
    recommendation: Optional[str] = Query(None),
    confidence_level: Optional[str] = Query(None),
    claim_id: Optional[str] = Query(None),
    limit: int = Query(100)
):
    query = supabase.table("assessment_logs").select("*")
    if workflow_type:
        query = query.eq("workflow_type", workflow_type)
    if recommendation:
        query = query.eq("recommendation", recommendation)
    if confidence_level:
        query = query.eq("confidence_level", confidence_level)
    if claim_id:
        query = query.eq("claim_id", claim_id)
    query = query.order("assessed_at", desc=True).limit(limit)
    response = query.execute()
    return response.data or []

# ── WORKFLOW NODES ────────────────────────────────────────────────────────────

class WorkflowNodeCreate(BaseModel):
    workflow_name: str
    workflow_version: Optional[str] = None
    node_type: str
    node_name: str
    node_content: str
    content_hash: str
    committed_by: Optional[str] = None
    git_commit_hash: Optional[str] = None


@app.get("/workflow-nodes")
def get_workflow_nodes(
    workflow_name: Optional[str] = Query(None),
    node_type: Optional[str] = Query(None)
):
    query = supabase.table("workflow_nodes").select("*")
    if workflow_name:
        query = query.eq("workflow_name", workflow_name)
    if node_type:
        query = query.eq("node_type", node_type)
    query = query.order("committed_at", desc=True)
    response = query.execute()
    return response.data or []


@app.post("/workflow-nodes")
def create_workflow_node(node: WorkflowNodeCreate):
    data = {k: v for k, v in node.dict().items() if v is not None}
    response = supabase.table("workflow_nodes").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to store workflow node")
    return response.data[0]

# ── CHANGE APPROVALS ──────────────────────────────────────────────────────────

class ChangeApprovalCreate(BaseModel):
    node_id: Optional[str] = None
    workflow_name: str
    node_name: str
    node_type: Optional[str] = None
    changed_by: str
    diff_content: str
    # Populated by both the dsl_manager CLI and the /dsl/scan endpoint so the
    # approve endpoint below can promote to workflow_nodes uniformly
    # regardless of which path created the pending approval.
    new_content: Optional[str] = None
    new_hash: Optional[str] = None


class ApproveRejectBody(BaseModel):
    actioned_by: str
    reason: str
    git_commit_hash: Optional[str] = None


@app.get("/change-approvals")
def get_change_approvals(
    status: Optional[str] = Query(None),
    workflow_name: Optional[str] = Query(None),
    limit: int = Query(50)
):
    query = supabase.table("change_approvals").select("*")
    if status:
        query = query.eq("status", status)
    if workflow_name:
        query = query.eq("workflow_name", workflow_name)
    query = query.order("created_at", desc=True).limit(limit)
    response = query.execute()
    return response.data or []


@app.post("/change-approvals")
def create_change_approval(approval: ChangeApprovalCreate):
    data = {k: v for k, v in approval.dict().items() if v is not None}
    data["status"] = "pending"
    response = supabase.table("change_approvals").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create change approval")
    return response.data[0]


@app.post("/change-approvals/{approval_id}/approve")
def approve_change(approval_id: str, body: ApproveRejectBody):
    # Fetch the approval first so we can promote new_content → workflow_nodes
    fetch = (
        supabase.table("change_approvals")
        .select("*")
        .eq("approval_id", approval_id)
        .single()
        .execute()
    )
    if not fetch.data:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval = fetch.data

    update_data = {
        "status": "approved",
        "approved_by": body.actioned_by,
        "change_reason": body.reason,
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    if body.git_commit_hash:
        update_data["git_commit_hash"] = body.git_commit_hash

    response = (
        supabase.table("change_approvals")
        .update(update_data)
        .eq("approval_id", approval_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Approval update failed")

    # Promote new content to workflow_nodes
    new_content = approval.get("new_content")
    new_hash = approval.get("new_hash")
    if new_content and new_hash:
        supabase.table("workflow_nodes").update({
            "node_content": new_content,
            "content_hash": new_hash,
            "committed_by": body.actioned_by,
            "committed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("workflow_name", approval["workflow_name"]).eq("node_name", approval["node_name"]).execute()

    return response.data[0]


@app.post("/change-approvals/{approval_id}/reject")
def reject_change(approval_id: str, body: ApproveRejectBody):
    update_data = {
        "status": "rejected",
        "approved_by": body.actioned_by,
        "change_reason": body.reason,
    }
    response = (
        supabase.table("change_approvals")
        .update(update_data)
        .eq("approval_id", approval_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Approval not found")
    return response.data[0]


# ── DSL SCAN ──────────────────────────────────────────────────────────────────
# Reads every .yml in dify-data/, parses LLM/code/agent nodes, compares
# SHA256 hashes against workflow_nodes table, and:
#   - First-seen nodes  → stored directly as baseline (no approval needed)
#   - Changed nodes     → pending change_approval created (unless one already pending)
# ─────────────────────────────────────────────────────────────────────────────

DIFY_DATA_DIR = Path(__file__).parent.parent / "dify-data"


@app.get("/dsl/status")
def dsl_status():
    """
    Return summary of what .yml files are in dify-data/ and how many
    nodes are stored per workflow in workflow_nodes.
    """
    if not DIFY_DATA_DIR.exists():
        raise HTTPException(status_code=404, detail="dify-data/ folder not found next to mcp_server/")

    files = sorted(p.name for p in DIFY_DATA_DIR.glob("*.yml"))

    stored_resp = supabase.table("workflow_nodes").select("workflow_name, node_name, content_hash, committed_at").execute()
    stored_by_workflow: dict[str, list] = {}
    for row in (stored_resp.data or []):
        wf = row["workflow_name"]
        stored_by_workflow.setdefault(wf, []).append(row)

    pending_resp = (
        supabase.table("change_approvals")
        .select("workflow_name, node_name")
        .eq("status", "pending")
        .execute()
    )
    pending_set = {(r["workflow_name"], r["node_name"]) for r in (pending_resp.data or [])}

    return {
        "dify_data_dir": str(DIFY_DATA_DIR),
        "files_in_folder": files,
        "stored_workflows": {wf: len(nodes) for wf, nodes in stored_by_workflow.items()},
        "pending_approvals": len(pending_set),
    }


@app.post("/dsl/scan")
def dsl_scan(submitted_by: str = Query(..., description="Name of the person triggering the scan")):
    """
    Scan all .yml files in dify-data/.
    - First-seen nodes  → stored as baseline in workflow_nodes (no approval)
    - Changed nodes     → pending change_approval created (skipped if one already pending)
    - Unchanged nodes   → skipped
    Returns a full summary of the scan.
    """
    if not DIFY_DATA_DIR.exists():
        raise HTTPException(status_code=404, detail="dify-data/ folder not found next to mcp_server/")

    yaml_files = sorted(DIFY_DATA_DIR.glob("*.yml"))
    if not yaml_files:
        raise HTTPException(status_code=404, detail="No YAML files found in dify-data/")

    # Load all stored nodes keyed by (workflow_name, node_name)
    stored_resp = supabase.table("workflow_nodes").select("*").execute()
    stored: dict[tuple, dict] = {}
    for row in (stored_resp.data or []):
        stored[(row["workflow_name"], row["node_name"])] = row

    # Load all existing pending approvals to avoid duplicates
    pending_resp = (
        supabase.table("change_approvals")
        .select("workflow_name, node_name")
        .eq("status", "pending")
        .execute()
    )
    already_pending = {(r["workflow_name"], r["node_name"]) for r in (pending_resp.data or [])}

    summary = {
        "scanned_files": [],
        "new_nodes": [],       # baselined immediately, no approval needed
        "changed_nodes": [],   # pending approval created
        "already_pending": [], # skipped — approval already exists
        "unchanged_nodes": [],
        "errors": [],
    }

    for yaml_file in yaml_files:
        summary["scanned_files"].append(yaml_file.name)
        try:
            nodes = parse_workflow(yaml_file)
        except Exception as exc:
            summary["errors"].append({"file": yaml_file.name, "error": str(exc)})
            continue

        for node in nodes:
            key = (node["workflow_name"], node["node_name"])
            existing = stored.get(key)

            if existing is None:
                # Brand new node — store as baseline
                supabase.table("workflow_nodes").insert({
                    "workflow_name": node["workflow_name"],
                    "workflow_version": "v1.0",
                    "node_type": node["node_type"],
                    "node_name": node["node_name"],
                    "node_content": node["content"],
                    "content_hash": node["content_hash"],
                    "committed_by": submitted_by,
                }).execute()
                summary["new_nodes"].append({
                    "workflow": node["workflow_name"],
                    "node": node["node_name"],
                    "type": node["node_type"],
                })

            elif existing["content_hash"] == node["content_hash"]:
                summary["unchanged_nodes"].append({
                    "workflow": node["workflow_name"],
                    "node": node["node_name"],
                })

            elif key in already_pending:
                summary["already_pending"].append({
                    "workflow": node["workflow_name"],
                    "node": node["node_name"],
                })

            else:
                # Hash changed — create pending approval
                diff = compute_diff(
                    existing.get("node_content", ""),
                    node["content"],
                    node["node_name"],
                    node["node_type"],
                )
                supabase.table("change_approvals").insert({
                    "workflow_name": node["workflow_name"],
                    "node_name": node["node_name"],
                    "node_type": node["node_type"],
                    # change_approvals.node_id is a UUID FK to workflow_nodes.node_id —
                    # existing["node_id"] is that real stored UUID. node["node_id"] is
                    # Dify's own internal node identifier (not a UUID) and must not go here.
                    "node_id": existing["node_id"],
                    "new_content": node["content"],
                    "new_hash": node["content_hash"],
                    "changed_by": submitted_by,
                    "diff_content": diff,
                    "status": "pending",
                }).execute()
                summary["changed_nodes"].append({
                    "workflow": node["workflow_name"],
                    "node": node["node_name"],
                    "type": node["node_type"],
                })

    summary["totals"] = {
        "files": len(summary["scanned_files"]),
        "new": len(summary["new_nodes"]),
        "changed": len(summary["changed_nodes"]),
        "already_pending": len(summary["already_pending"]),
        "unchanged": len(summary["unchanged_nodes"]),
        "errors": len(summary["errors"]),
    }

    return summary