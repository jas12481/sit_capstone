from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime, timezone
from pathlib import Path
import concurrent.futures
import json
import os
import sys

# dsl_manager lives at the repo root, one level up from this file. Add it to
# sys.path so parsing/hashing/diffing logic has a single implementation
# shared by this server-side scan and the `dsl_manager` CLI — do not
# reimplement node extraction here.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dsl_manager.parser import parse_workflow, parse_workflow_content, hash_content  # noqa: E402
from dsl_manager.diff import compute_diff  # noqa: E402
from dsl_manager import git_commit  # noqa: E402

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
        if claim_id:
            raise HTTPException(status_code=404, detail="No claims found")
        return []
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
        if policy_id:
            raise HTTPException(status_code=404, detail="No policies found")
        return []
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

    # Included so any consumer of this endpoint can check document-dependent mandatory
    # rules (e.g. "medical report must be included in claim documents") — without this,
    # such rules can never be confirmed as satisfied, since claim_documents was otherwise
    # only reachable via the separate /claim-documents endpoint.
    documents_response = supabase.table("claim_documents").select("*").eq("claim_id", claim_id).execute()

    return {
        "claim": claim,
        "policy": policy,
        "eligibility_rules": rules_response.data,
        "claim_documents": documents_response.data or []
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

# ── FRAUD RISK CHECKS ─────────────────────────────────────────────────────────
# Persists results from the Fraud/Anomaly Risk Signals Dify app so the Audit
# Log can show a badge without re-running the check, and the Dashboard can
# aggregate risk levels/flag signals across every claim checked so far.

class FraudRiskCheckCreate(BaseModel):
    claim_id: str
    risk_level: str
    flags: Optional[List[dict]] = None
    recommended_action: Optional[str] = None
    checked_by: Optional[str] = None


@app.post("/fraud-risk-checks")
def create_fraud_risk_check(check: FraudRiskCheckCreate):
    data = {k: v for k, v in check.dict().items() if v is not None}
    response = supabase.table("fraud_risk_checks").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to store fraud risk check")
    return response.data[0]


@app.get("/fraud-risk-checks")
def get_fraud_risk_checks(
    claim_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(500)
):
    query = supabase.table("fraud_risk_checks").select("*")
    if claim_id:
        query = query.eq("claim_id", claim_id)
    if risk_level:
        query = query.eq("risk_level", risk_level)
    query = query.order("checked_at", desc=True).limit(limit)
    response = query.execute()
    # An empty result is a legitimate state (no claims checked yet) — same
    # convention as /claim-documents, not a 404.
    return response.data or []


# ── ASSESSMENT EXPLANATIONS ──────────────────────────────────────────────────
# Deliberately keyed by log_id, not claim_id (unlike fraud_risk_checks) — a
# claim can have many assessment_logs rows (repeat assessments), and an
# explanation is tied to one specific verdict, not "whatever's currently
# newest" for that claim. See Explain_Assessment_Reasoning.yml, which now
# also takes log_id as an input for the same reason.

class AssessmentExplanationCreate(BaseModel):
    log_id: str
    claim_id: str
    explanation_text: str
    generated_by: Optional[str] = None


@app.post("/explanations")
def create_assessment_explanation(explanation: AssessmentExplanationCreate):
    data = {k: v for k, v in explanation.dict().items() if v is not None}
    response = supabase.table("assessment_explanations").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to store assessment explanation")
    return response.data[0]


@app.get("/explanations")
def get_assessment_explanations(
    log_id: Optional[str] = Query(None),
    claim_id: Optional[str] = Query(None),
    limit: int = Query(500)
):
    query = supabase.table("assessment_explanations").select("*")
    if log_id:
        query = query.eq("log_id", log_id)
    if claim_id:
        query = query.eq("claim_id", claim_id)
    query = query.order("generated_at", desc=True).limit(limit)
    response = query.execute()
    return response.data or []


# ── MISSING DOCUMENTATION CHECKS ────────────────────────────────────────────
# Keyed by claim_id, like fraud_risk_checks — /assessment and /claim-documents
# both reflect the claim's CURRENT state, not a specific historical
# assessment_logs row, so unlike explanations this isn't tied to one verdict.
# Frontend scopes this action to REFER_FOR_FURTHER_REVIEW rows only (see
# Missing_Documentation_Advisor.yml's own prompt: it determines what's "still
# required to complete assessment" — only meaningful when assessment
# couldn't be completed, not for a completed REJECT/APPROVE).

class MissingDocumentationCheckCreate(BaseModel):
    claim_id: str
    all_requirements_met: bool
    missing_documents: Optional[List[dict]] = None
    submitted_documents_summary: Optional[str] = None
    checked_by: Optional[str] = None


@app.post("/missing-documentation-checks")
def create_missing_documentation_check(check: MissingDocumentationCheckCreate):
    data = {k: v for k, v in check.dict().items() if v is not None}
    response = supabase.table("missing_documentation_checks").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to store missing documentation check")
    return response.data[0]


@app.get("/missing-documentation-checks")
def get_missing_documentation_checks(
    claim_id: Optional[str] = Query(None),
    limit: int = Query(500)
):
    query = supabase.table("missing_documentation_checks").select("*")
    if claim_id:
        query = query.eq("claim_id", claim_id)
    query = query.order("checked_at", desc=True).limit(limit)
    response = query.execute()
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
    # Per-rule breakdown (rule_id, result PASS/FAIL/UNKNOWN/NOT_APPLICABLE, reason,
    # evidence_fields) from rule_by_rule_eligibility_check — previously computed on
    # every assessment but discarded after the workflow run, so there was no way to
    # see WHY a specific claim was referred/rejected beyond aggregate counts.
    # Accepts either a JSON-encoded string or a native array — Dify's HTTP node
    # sent this as a raw array in practice (confirmed via a live 422 against this
    # endpoint), not the JSON string its code node's declared output type implied,
    # so the backend has to tolerate both rather than assume one shape.
    rule_checks: Optional[Union[str, List[dict]]] = None


CLAIM_STATUS_FROM_RECOMMENDATION = {
    "APPROVE": "approved",
    "REJECT": "rejected",
    "REFER_FOR_FURTHER_REVIEW": "under_review",
}


def _derive_rejection_reason(rule_checks: Optional[list]) -> Optional[str]:
    """First mandatory-failed rule, formatted as '{rule_name}: {reason}' — the same
    signal a human would look at first to understand why a claim was rejected."""
    if not rule_checks:
        return None
    for rc in rule_checks:
        if rc.get("result") == "FAIL" and str(rc.get("is_mandatory")).lower() == "true":
            name = rc.get("rule_name") or rc.get("rule_id") or "eligibility rule"
            reason = rc.get("reason") or ""
            return f"{name}: {reason}" if reason else name
    return None


@app.post("/assessment-logs")
def create_assessment_log(
    log: AssessmentLogCreate,
    skip_status_update: bool = Query(
        False,
        description="Skip writing the outcome back to claims.status — used by evaluation/backfill "
                    "scripts so repeated test runs don't mutate the source dataset.",
    ),
):
    data = {k: v for k, v in log.dict().items() if v is not None}
    if isinstance(data.get("rule_checks"), str):
        try:
            data["rule_checks"] = json.loads(data["rule_checks"])
        except json.JSONDecodeError:
            # Don't let a malformed rule_checks payload block the actual
            # assessment log write — that's the core governance record.
            del data["rule_checks"]
    response = supabase.table("assessment_logs").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to write assessment log")
    result = response.data[0]

    # Write-back: a freshly-submitted ("pending") claim gets its status finalized by the
    # outcome of its first real assessment. Claims that already have a decided status
    # (approved/rejected/under_review) are left untouched — re-assessing one of those is
    # an audit re-check, not claim intake, and must never silently overwrite the existing
    # historical record. This also makes the write-back self-limiting: once a pending
    # claim flips to a decided status, later re-assessments of the same claim (e.g.
    # repeated manual testing) no longer qualify and can't overwrite it again.
    claim_id = data.get("claim_id")
    recommendation = data.get("recommendation")
    if not skip_status_update and claim_id and recommendation in CLAIM_STATUS_FROM_RECOMMENDATION:
        try:
            claim_resp = supabase.table("claims").select("status").eq("claim_id", claim_id).execute()
            current_status = claim_resp.data[0]["status"] if claim_resp.data else None
            if current_status == "pending":
                update = {"status": CLAIM_STATUS_FROM_RECOMMENDATION[recommendation]}
                if recommendation == "REJECT":
                    reason = _derive_rejection_reason(data.get("rule_checks"))
                    if reason:
                        update["rejection_reason"] = reason
                supabase.table("claims").update(update).eq("claim_id", claim_id).execute()
        except Exception as exc:  # noqa: BLE001
            # Never let the write-back block the assessment log write — that's the core
            # governance record and must succeed regardless of this side effect.
            print(f"claims.status write-back failed for {claim_id}: {exc}")

    return result


@app.get("/assessment-logs")
def get_assessment_logs(
    workflow_type: Optional[str] = Query(None),
    recommendation: Optional[str] = Query(None),
    confidence_level: Optional[str] = Query(None),
    claim_id: Optional[str] = Query(None),
    log_id: Optional[str] = Query(None),
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
    if log_id:
        query = query.eq("log_id", log_id)
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

class SnapshotRequest(BaseModel):
    # None/empty → snapshot every dify-data/*.yml file
    files: Optional[List[str]] = None
    by: str
    reason: str


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
# Reads every .yml from the "dify-workflows" Supabase Storage bucket (the
# sole source of truth for "current" workflow state — dify-data/ on disk is
# kept only as a frozen historical artifact and is never read by any of the
# endpoints below), parses LLM/code/agent nodes, compares SHA256 hashes
# against workflow_nodes table, and:
#   - First-seen nodes  → stored directly as baseline (no approval needed)
#   - Changed nodes     → pending change_approval created (unless one already pending)
# ─────────────────────────────────────────────────────────────────────────────

WORKFLOW_BUCKET = "dify-workflows"


def _list_workflow_storage_files() -> list[str]:
    """Bare filenames (e.g. "Life_Assess_Claim.yml") currently in the bucket."""
    items = supabase.storage.from_(WORKFLOW_BUCKET).list()
    return sorted(item["name"] for item in (items or []) if item["name"].endswith(".yml"))


def _download_workflow_file(name: str) -> bytes:
    return supabase.storage.from_(WORKFLOW_BUCKET).download(name)


def _download_and_parse_workflow(name: str) -> tuple[str, Optional[list], Optional[str]]:
    """Download + parse a single workflow file. Returns (name, nodes, error)."""
    try:
        raw_bytes = _download_workflow_file(name)
        nodes = parse_workflow_content(
            raw_bytes.decode("utf-8"), workflow_name_fallback=Path(name).stem
        )
        return name, nodes, None
    except Exception as exc:  # noqa: BLE001
        return name, None, str(exc)


@app.post("/dsl/upload")
async def dsl_upload_workflow(
    file: UploadFile = File(...),
    uploaded_by: str = Form(...),
):
    """
    Upload an exported Dify DSL YAML directly into the dify-workflows Storage
    bucket — becomes "current" immediately for /dsl/scan, snapshot-taking,
    and node-diff comparison, no local file placement or backend access
    needed. Overwrites any existing file with the same name (upsert).
    """
    if not (file.filename.endswith(".yml") or file.filename.endswith(".yaml")):
        raise HTTPException(status_code=400, detail="Only .yml/.yaml files are accepted")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        nodes = parse_workflow_content(
            content.decode("utf-8"), workflow_name_fallback=Path(file.filename).stem
        )
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Not valid Dify DSL YAML: {exc}")

    try:
        supabase.storage.from_(WORKFLOW_BUCKET).upload(
            path=file.filename,
            file=content,
            file_options={"content-type": "application/x-yaml", "upsert": "true"},
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Upload to Storage failed: {exc}")

    return {
        "filename": file.filename,
        "size": len(content),
        "node_count": len(nodes),
        "workflow_name": nodes[0]["workflow_name"] if nodes else Path(file.filename).stem,
        "uploaded_by": uploaded_by,
    }


@app.get("/dsl/status")
def dsl_status():
    """
    Return summary of what .yml files are in the dify-workflows Storage
    bucket and how many nodes are stored per workflow in workflow_nodes.
    """
    files = _list_workflow_storage_files()

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
        "storage_bucket": WORKFLOW_BUCKET,
        "files_in_folder": files,
        "stored_workflows": {wf: len(nodes) for wf, nodes in stored_by_workflow.items()},
        "pending_approvals": len(pending_set),
    }


@app.post("/dsl/scan")
def dsl_scan(submitted_by: str = Query(..., description="Name of the person triggering the scan")):
    """
    Scan all .yml files in the dify-workflows Storage bucket.
    - First-seen nodes  → stored as baseline in workflow_nodes (no approval)
    - Changed nodes     → pending change_approval created (skipped if one already pending)
    - Unchanged nodes   → skipped
    Returns a full summary of the scan.
    """
    yaml_files = _list_workflow_storage_files()
    if not yaml_files:
        raise HTTPException(status_code=404, detail=f"No YAML files found in the '{WORKFLOW_BUCKET}' bucket")

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

    # Download + parse all files concurrently — this loop is network-bound
    # (one Storage API round-trip per file), not memory-bound, so a bounded
    # worker pool cuts total scan time from ~N sequential round-trips down to
    # ~N/10 batches without risking rate limits or connection exhaustion as
    # the workflow count grows. executor.map preserves input order, so
    # scanned_files stays in the same order as before.
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        parse_results = list(executor.map(_download_and_parse_workflow, yaml_files))

    for yaml_name, nodes, error in parse_results:
        summary["scanned_files"].append(yaml_name)
        if error is not None:
            summary["errors"].append({"file": yaml_name, "error": error})
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


# ── DSL WORKFLOW SNAPSHOTS ──────────────────────────────────────────────────────
# Whole-file version history of dify-data/*.yml, committed to a dedicated
# dsl-governance-history branch (never main) — independent of the node-level
# approval flow above. Exists so the actual YAML files (not just individually
# extracted node text) have a full, diffable audit trail visible in the
# frontend, not just via the dsl_manager CLI.
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/dsl/snapshot-files")
def dsl_snapshot_files():
    """
    List every workflow YAML in the dify-workflows Storage bucket, eligible
    for a whole-file snapshot. Returned as "dify-data/{name}" strings (the
    same shape as before the Storage migration) purely so the snapshot's
    commit path on the governance branch stays consistent with history
    already there — the actual source of content is Storage, not disk.
    """
    files = [f"dify-data/{name}" for name in _list_workflow_storage_files()]
    return {"files": files}


@app.get("/dsl/snapshots")
def dsl_snapshots(
    file: str = Query(..., description="Path to a dify-data/*.yml file, e.g. dify-data/Life_Assess_Claim.yml"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Return the whole-file snapshot commit history for one workflow YAML,
    read live from the dsl-governance-history branch on GitHub.
    """
    try:
        commits = git_commit.list_workflow_snapshots(file, limit=limit)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    compare_url = None
    if len(commits) >= 2:
        compare_url = git_commit.get_compare_url(commits[1]["sha"], commits[0]["sha"])

    return {
        "file": file,
        "branch": git_commit._governance_branch(),
        "commits": commits,
        "compare_url": compare_url,
    }


@app.post("/dsl/snapshots")
def dsl_take_snapshot(body: SnapshotRequest):
    """
    Commit the current Storage-bucket content of one or all workflow YAMLs to
    the dsl-governance-history branch. Creates the branch first if needed.
    """
    targets = body.files or [f"dify-data/{name}" for name in _list_workflow_storage_files()]
    if not targets:
        raise HTTPException(status_code=404, detail=f"No YAML files found in the '{WORKFLOW_BUCKET}' bucket")

    results = []
    for path in targets:
        # Accept both "dify-data/Name.yml" (what /dsl/snapshot-files returns)
        # and a bare "Name.yml" — either way, resolve to the bare Storage
        # object name for the download, and keep the "dify-data/" form as
        # the commit's repo path for continuity with existing history.
        name = path.split("/")[-1]
        repo_path = path if path.startswith("dify-data/") else f"dify-data/{name}"
        try:
            content = _download_workflow_file(name)
        except Exception as exc:  # noqa: BLE001
            results.append({"file": path, "status": "error", "detail": f"Not found in bucket: {exc}"})
            continue
        try:
            sha = git_commit.commit_workflow_snapshot(
                repo_path=repo_path, content=content, committed_by=body.by, reason=body.reason
            )
            results.append({
                "file": path,
                "status": "ok",
                "commit_sha": sha,
                "commit_url": git_commit.get_commit_url(sha),
            })
        except EnvironmentError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception as exc:  # noqa: BLE001
            results.append({"file": path, "status": "error", "detail": str(exc)})

    return {"branch": git_commit._governance_branch(), "results": results}


@app.get("/dsl/snapshots/node-diff")
def dsl_snapshot_node_diff(
    file: str = Query(..., description="e.g. dify-data/Life_Assess_Claim.yml"),
):
    """
    Compare the latest GitHub snapshot of a workflow against its current
    Storage-bucket content at the NODE level — only nodes whose content
    hash actually differs are returned (added/removed/changed), using the
    same parse_workflow_content()/compute_diff() machinery the approval
    flow already uses, instead of a raw whole-file text diff.
    """
    try:
        commits = git_commit.list_workflow_snapshots(file, limit=1)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if not commits:
        raise HTTPException(status_code=404, detail="No snapshot exists yet for this file.")

    latest = commits[0]
    repo_path = file if file.startswith("dify-data/") else f"dify-data/{file}"
    name = file.split("/")[-1]

    try:
        snapshot_bytes = git_commit.get_file_content_at_ref(repo_path, latest["sha"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not fetch snapshot content: {exc}")

    try:
        current_bytes = _download_workflow_file(name)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Not found in bucket: {exc}")

    fallback = Path(name).stem
    snapshot_nodes = {
        n["node_name"]: n
        for n in parse_workflow_content(snapshot_bytes.decode("utf-8"), workflow_name_fallback=fallback)
    }
    current_nodes = {
        n["node_name"]: n
        for n in parse_workflow_content(current_bytes.decode("utf-8"), workflow_name_fallback=fallback)
    }

    changed: list[dict] = []
    unchanged_count = 0

    for node_name in sorted(set(snapshot_nodes) | set(current_nodes)):
        snap = snapshot_nodes.get(node_name)
        curr = current_nodes.get(node_name)

        if snap and curr:
            if snap["content_hash"] == curr["content_hash"]:
                unchanged_count += 1
                continue
            status, node_type = "changed", curr["node_type"]
            diff = compute_diff(snap["content"], curr["content"], node_name, node_type)
        elif curr and not snap:
            status, node_type = "added", curr["node_type"]
            diff = compute_diff("", curr["content"], node_name, node_type)
        else:
            status, node_type = "removed", snap["node_type"]
            diff = compute_diff(snap["content"], "", node_name, node_type)

        changed.append({
            "node_name": node_name,
            "node_type": node_type,
            "status": status,
            "diff_content": diff,
        })

    return {
        "file": file,
        "snapshot_sha": latest["sha"],
        "snapshot_short_sha": latest["short_sha"],
        "snapshot_date": latest["date"],
        "snapshot_message": latest["message"],
        "changed_nodes": changed,
        "unchanged_count": unchanged_count,
    }