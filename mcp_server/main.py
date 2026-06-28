from fastapi import FastAPI, Query, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os

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
    changed_by: str
    diff_content: str


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
        raise HTTPException(status_code=404, detail="Approval not found")
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