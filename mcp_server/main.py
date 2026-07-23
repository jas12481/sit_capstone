from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form, BackgroundTasks
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path
import concurrent.futures
import json
import os
import requests
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
    # The judge's qualitative reasoning per score — previously computed by llm_judge on
    # every assessment but never sent past Dify at all (write_assessment_log's body never
    # referenced it), so there was no way to see WHY a hallucination-risk/consistency score
    # landed where it did without re-running the assessment live. Not a new assessment_logs
    # column — logged as an MLflow artifact instead (see _log_assessment_to_mlflow_and_persist),
    # popped out of `data` before the Supabase insert since that table has no matching column.
    judge_comments: Optional[str] = None


CLAIM_STATUS_FROM_RECOMMENDATION = {
    "APPROVE": "approved",
    "REJECT": "rejected",
    "REFER_FOR_FURTHER_REVIEW": "under_review",
}

# prompt_version is a static default baked into each *_Assess_Claim workflow's
# prepare_assessment_log_payload code node (e.g. prompt_version="life_assess_claim_v1.0")
# — it's never bumped by Dify itself when the underlying prompt actually changes, so two
# assessments a week apart under genuinely different prompts still report the same label.
# Rather than editing the Dify workflows to fix this (deliberately avoided per the same
# design-boundary reasoning as skip_status_update — see PROJECT_CONTEXT.md §9), this
# overrides the known-stale default server-side, effective from whenever an entry is added
# here forward. Add a new entry (old_value -> new_value) here as part of any future session
# that ships a real prompt/logic change to one of these workflows — this is the ongoing
# process replacing an automatic version bump. Historical rows before an entry existed keep
# their original (possibly stale) label; not retroactively rewritten, since reconstructing
# exact historical change boundaries from timestamps alone would be guesswork.
PROMPT_VERSION_BUMPS = {
    # Dify always sends the hardcoded "_v1.0" default (never edited — see the design-boundary
    # note above) — the key is always "_v1.0" regardless of how many real changes have
    # actually shipped since; only the target value moves forward each time.
    #
    # v1.1 (2026-07-16): LLM-as-judge grounding redesign (claim/policy-grounded scoring,
    # rubric anchors, deterministic judge_overall_score) — see PROJECT_CONTEXT.md §13.
    #
    # v1.2 (2026-07-16/17): judge_comments persistence; target-leakage fix (claim_record_json
    # no longer includes status/rejection_reason); judge now also grounded in
    # claim_documents, not just claim/policy records (was systematically flagging correctly-
    # cited document evidence as unsupported); new status-cross-check override
    # (check_status_consistency node forcing REFER_FOR_FURTHER_REVIEW when the rule-based
    # outcome disagrees with the claim's recorded status); fixed a leak where the override's
    # internal field name/value ("status_override", "MISMATCH") was appearing verbatim in
    # the final report's narrative text instead of plain language.
    "life_assess_claim_v1.0": "life_assess_claim_v1.2",
    "health_assess_claim_v1.0": "health_assess_claim_v1.2",
    "ci_assess_claim_v1.0": "ci_assess_claim_v1.2",
    "disability_assess_claim_v1.0": "disability_assess_claim_v1.2",
}

# model_version has the exact same staleness problem as prompt_version above — a static
# default hardcoded into each *_Assess_Claim workflow's prepare_assessment_log_payload
# code node (model_version="gpt-5.2"), never updated by Dify when an individual node's
# model actually changes. Unlike prompt_version, the raw value Dify sends doesn't encode
# which workflow it came from, so this is keyed on (workflow_type, raw_value) rather than
# the raw value alone — otherwise a domain that's had its models swapped and one that
# hasn't would collide on the same "gpt-5.2" key. Add an entry here whenever a
# *_Assess_Claim workflow's real per-node model mix changes.
#
# ci_assess_claim (2026-07-23): extract_response_focus_assess, format_final_report, and
# build_assessment_suggestion_context switched to gpt-5.4-mini to cut total pipeline
# latency (the orchestrator's workflow-as-tool call to this sub-workflow was timing out
# against its own ~60-70s full runtime).
#
# ci_assess_claim (2026-07-23, follow-up): policy_document_analysis also switched to
# gpt-5.4-mini after rule_by_rule_eligibility_check + policy_document_analysis were
# parallelized wasn't enough alone — this node was consistently the single largest
# contributor (~17-27s). Verified against 4 real runs on the same claim (2 before, 2
# after): judge scores stayed flat (overall 3.62-4.0 across all 4, no downward trend;
# hallucination-risk if anything ticked up slightly) while elapsed time dropped from
# ~65-67s to ~47-52s. rule_by_rule_eligibility_check, synthesize_final_verdict, and
# llm_judge remain on gpt-5.2 — the steps where a weaker model still carries real
# decision/quality risk.
MODEL_VERSION_OVERRIDES = {
    ("ci_assess_claim", "gpt-5.2"): "gpt-5.2 (+ gpt-5.4-mini: policy_document_analysis + formatting/support nodes)",
}

_mlflow_tracker = None


def _get_mlflow_tracker():
    """Lazily-initialized, process-wide singleton — MLflowTracker.initialize() makes a
    Databricks API call to resolve the experiment path, so this must happen once per
    process, not once per assessment-log write."""
    global _mlflow_tracker
    if _mlflow_tracker is None:
        from mlflow_tracker import MLflowTracker
        tracker = MLflowTracker()
        try:
            tracker.initialize()
        except Exception as exc:  # noqa: BLE001
            print(f"MLflowTracker initialize failed: {exc}")
        _mlflow_tracker = tracker
    return _mlflow_tracker


def _log_assessment_to_mlflow_and_persist(data: dict, log_id: str) -> None:
    """
    Creates a real MLflow run for a production assessment and stashes its run_id back onto
    the assessment_logs row. This is what assessment_logs.mlflow_run_id is supposed to point
    at (PROJECT_CONTEXT.md §12); previously nothing in the live Dify pipeline ever created
    this run at all, so the column was always empty for real assessments (only the separate
    evaluation harness created its own, disconnected MLflow runs).

    Runs as a FastAPI BackgroundTask, after the response is already sent — a real Databricks
    round-trip (start_run + several log_param/log_metric calls) measured at 13+ seconds even
    with a warm tracker, which must never block the actual governance record write or a
    claims officer waiting on a chat response. Same reasoning as the write-back/cross-check
    being isolated from the core insert, just async instead of synchronous since this one is
    slow rather than merely non-essential.
    """
    try:
        from mlflow_tracker import AssessmentRunPayload
        tracker = _get_mlflow_tracker()
        if not tracker.is_ready():
            return
        payload = AssessmentRunPayload(
            run_name=f"{data.get('workflow_type', 'assessment')}_{data.get('claim_id', 'unknown')}",
            workflow_type=data.get("workflow_type", "unknown"),
            model_name=data.get("model_version", "gpt-5.2"),
            prompt_version=data.get("prompt_version"),
            claim_id=data.get("claim_id"),
            recommendation=data.get("recommendation"),
            confidence_level=data.get("confidence_level"),
            coverage_conclusion=data.get("coverage_conclusion"),
            mandatory_rules_failed=data.get("mandatory_rules_failed"),
            total_rules_passed=data.get("total_rules_passed"),
            judge_completeness_score=data.get("judge_completeness_score"),
            judge_consistency_score=data.get("judge_consistency_score"),
            judge_hallucination_risk_score=data.get("judge_hallucination_risk_score"),
            judge_clarity_score=data.get("judge_clarity_score"),
            judge_overall_score=data.get("judge_overall_score"),
            tags={"run_type": "production_assessment"},
            artifacts={
                **({"rule_checks": data["rule_checks"]} if data.get("rule_checks") else {}),
                **({"judge_comments": data["judge_comments"]} if data.get("judge_comments") else {}),
            },
        )
        mlflow_run_id = tracker.log_assessment_run(payload)
        if mlflow_run_id:
            supabase.table("assessment_logs").update({"mlflow_run_id": mlflow_run_id}).eq("log_id", log_id).execute()
    except Exception as exc:  # noqa: BLE001
        print(f"MLflow logging failed for log {log_id} ({data.get('claim_id')}): {exc}")


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


def _is_missing_docs_relevant(recommendation: Optional[str], rule_checks: Optional[list]) -> bool:
    """
    Same gating rule as the Audit Log's manual "Check missing documentation" button
    (frontend/app/audit/page.tsx: isMissingDocsRelevant) — kept in sync deliberately,
    since that's the only other place deciding whether the Advisor is worth calling
    for a given claim. REFER always qualifies (assessment couldn't complete); REJECT
    qualifies only when the failing mandatory rule's evidence pointed at
    claim_documents, i.e. the rejection actually turned on documentation.
    """
    if recommendation == "REFER_FOR_FURTHER_REVIEW":
        return True
    if recommendation != "REJECT" or not rule_checks:
        return False
    return any(
        rc.get("result") == "FAIL"
        and str(rc.get("is_mandatory")).lower() == "true"
        and any(str(f).startswith("claim_documents") for f in (rc.get("evidence_fields") or []))
        for rc in rule_checks
    )


def _run_missing_docs_advisor(claim_id: str) -> Optional[dict]:
    """
    Calls the Missing_Documentation_Advisor Dify workflow app directly — same
    contract as frontend/app/api/dify/missing-docs/route.ts, ported here so the
    assessment pipeline can trigger it server-side without a round trip through
    the frontend. Returns None (not an exception) if the app isn't configured on
    this deployment, matching MLflowTracker's non-strict pattern elsewhere in
    this file.
    """
    dify_url = os.getenv("DIFY_URL")
    dify_key = os.getenv("DIFY_MISSING_DOCS_KEY")
    if not dify_url or not dify_key:
        print("Missing_Documentation_Advisor not configured (DIFY_URL / DIFY_MISSING_DOCS_KEY) — skipping auto-check")
        return None

    resp = requests.post(
        f"{dify_url}/v1/workflows/run",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {dify_key}"},
        json={
            "inputs": {"claim_id": claim_id, "query": f"What documentation is missing for claim {claim_id}?"},
            "response_mode": "blocking",
            "user": "assessment-pipeline",
        },
        timeout=120,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("data", {}).get("status") != "succeeded":
        raise RuntimeError(f"Advisor workflow did not succeed: {body.get('data', {}).get('error')}")
    parsed = json.loads(body.get("data", {}).get("outputs", {}).get("answer"))
    # Same coercion as lib/mcp.ts's runMissingDocumentationCheck — Dify's structured
    # output occasionally returns this as the string "false" rather than a real JSON
    # boolean, which is truthy in Python/JS alike and would silently corrupt every
    # downstream "is this claim complete" check if left uncoerced.
    parsed["all_requirements_met"] = str(parsed.get("all_requirements_met")).strip().lower() == "true"
    return parsed


def _check_missing_docs_and_persist(claim_id: str) -> None:
    """
    Runs as a FastAPI BackgroundTask after an assessment log write, for claims that
    qualify per _is_missing_docs_relevant — the automatic counterpart to a human
    clicking "Check missing documentation" in the Audit Log. Non-strict: any
    failure here must never affect the assessment log write it's attached to,
    which has already succeeded and returned to the caller by the time this runs.
    """
    try:
        result = _run_missing_docs_advisor(claim_id)
        if result is None:
            return
        payload = {
            "claim_id": claim_id,
            "all_requirements_met": result.get("all_requirements_met", False),
            "missing_documents": result.get("missing_documents") or [],
            "submitted_documents_summary": result.get("submitted_documents_summary") or "",
            "checked_by": "auto_pipeline",
        }
        supabase.table("missing_documentation_checks").insert(payload).execute()
    except Exception as exc:  # noqa: BLE001
        print(f"Auto missing-documentation check failed for {claim_id}: {exc}")


def _write_back_status_and_cross_check(
    claim_id: str,
    recommendation: str,
    rule_checks: Optional[list],
    log_id: Optional[str],
    skip_status_update: bool,
) -> None:
    """
    Write-back (pending claims) / status cross-check (already-decided claims) — mutually
    exclusive by construction, matching "claim intake" vs. "audit re-check" semantics. A
    freshly-submitted ("pending") claim gets its status finalized by the outcome of its
    first real assessment. A claim that already has a decided status is left untouched
    (re-assessing one of those must never silently overwrite the existing historical
    record) — instead, this records whether the fresh, independent assessment agrees with
    what's already on record, purely observational, with zero influence on the verdict
    itself (computed entirely after the fact, from data already sent to this endpoint).

    Runs as a FastAPI BackgroundTask — this is 2-3 sequential Supabase round trips (a
    status lookup, then either a claims update or an assessment_logs update) that used to
    sit in the synchronous response path for a purely observational side effect, adding
    real latency (measured contributing to write_assessment_log's ~3.3s node time in a
    live Dify trace) to every single assessment write. Moved off the response path the
    same way MLflow logging already was — see _log_assessment_to_mlflow_and_persist.
    """
    try:
        claim_resp = supabase.table("claims").select("status,rejection_reason").eq("claim_id", claim_id).execute()
        current_status = claim_resp.data[0]["status"] if claim_resp.data else None
        current_rejection_reason = claim_resp.data[0].get("rejection_reason") if claim_resp.data else None
    except Exception as exc:  # noqa: BLE001
        print(f"could not read claims.status for {claim_id}: {exc}")
        return

    if not skip_status_update and current_status == "pending":
        try:
            update = {"status": CLAIM_STATUS_FROM_RECOMMENDATION[recommendation]}
            if recommendation == "REJECT":
                reason = _derive_rejection_reason(rule_checks)
                if reason:
                    update["rejection_reason"] = reason
            supabase.table("claims").update(update).eq("claim_id", claim_id).execute()
        except Exception as exc:  # noqa: BLE001
            # Never let the write-back block the assessment log write — that's the
            # core governance record and must succeed regardless of this side effect.
            print(f"claims.status write-back failed for {claim_id}: {exc}")
    elif current_status and current_status != "pending" and log_id:
        expected_status = CLAIM_STATUS_FROM_RECOMMENDATION[recommendation]
        cross_check_update = {"status_cross_check": "CONSISTENT" if expected_status == current_status else "MISMATCH"}
        if cross_check_update["status_cross_check"] == "MISMATCH":
            note = f"recorded status is '{current_status}'"
            if current_rejection_reason:
                note += f" (reason: {current_rejection_reason})"
            note += f", but AI recommendation is '{recommendation}'"
            cross_check_update["status_cross_check_note"] = note
        try:
            # Separate update, not part of the main insert — status_cross_check is a
            # column that may not exist yet on a given deployment (see PROJECT_CONTEXT.md's
            # ALTER TABLE note); isolating it here means a missing column only drops this
            # observational field, never the assessment log itself.
            supabase.table("assessment_logs").update(cross_check_update).eq("log_id", log_id).execute()
        except Exception as exc:  # noqa: BLE001
            print(f"status_cross_check update failed for log {log_id}: {exc}")


@app.post("/assessment-logs")
def create_assessment_log(
    log: AssessmentLogCreate,
    background_tasks: BackgroundTasks,
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

    if data.get("prompt_version") in PROMPT_VERSION_BUMPS:
        data["prompt_version"] = PROMPT_VERSION_BUMPS[data["prompt_version"]]

    model_override_key = (data.get("workflow_type"), data.get("model_version"))
    if model_override_key in MODEL_VERSION_OVERRIDES:
        data["model_version"] = MODEL_VERSION_OVERRIDES[model_override_key]

    # judge_comments has no assessment_logs column (logged to MLflow as an artifact
    # instead) — pop it out before the insert, but keep it in mlflow_data for the
    # background task below, which needs the full picture.
    mlflow_data = dict(data)
    data.pop("judge_comments", None)

    # Idempotency: write_assessment_log (all 4 *_Assess_Claim workflows) has
    # retry_enabled=true with no idempotency key — if this endpoint's response is slow or
    # dropped, Dify silently resends the exact same completed request, creating a second
    # governance record for the same real assessment with a different log_id. Found live
    # (2026-07-16/17): a stray duplicate survived several rounds of manual cleanup because
    # each cleanup only ever deleted the specific log_id captured from that call's own
    # response, never a full sweep. A genuine second assessment of the same claim — even
    # seconds apart — will not have identical judge scores (the judge call isn't
    # deterministic, confirmed repeatedly this session), so an exact match on claim_id +
    # all 4 judge sub-scores within a short window reliably signals a retry, not a new run.
    claim_id_for_dedup = data.get("claim_id")
    judge_score_keys = ("judge_completeness_score", "judge_consistency_score", "judge_hallucination_risk_score", "judge_clarity_score")
    if claim_id_for_dedup and all(k in data for k in judge_score_keys):
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
            dup_query = supabase.table("assessment_logs").select("*").eq("claim_id", claim_id_for_dedup)
            for k in judge_score_keys:
                dup_query = dup_query.eq(k, data[k])
            dup_check = dup_query.gte("assessed_at", cutoff).order("assessed_at", desc=True).limit(1).execute()
            if dup_check.data:
                print(f"Duplicate assessment detected for {claim_id_for_dedup} "
                      f"(matches log_id {dup_check.data[0]['log_id']} within 120s) — "
                      f"skipping insert, likely a Dify retry")
                return dup_check.data[0]
        except Exception as exc:  # noqa: BLE001
            # Never let the idempotency check itself block a genuine write.
            print(f"Idempotency check failed for {claim_id_for_dedup}: {exc}")

    response = supabase.table("assessment_logs").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to write assessment log")
    result = response.data[0]

    # MLflow logging is real Databricks network I/O (13+ seconds even warm) — scheduled to
    # run after this response is returned, never blocking the core write. mlflow_run_id
    # will not be present on the immediate response; a subsequent GET on this log_id will
    # have it once the background task completes, same as status_cross_check below.
    if result.get("log_id"):
        background_tasks.add_task(_log_assessment_to_mlflow_and_persist, mlflow_data, result["log_id"])

    # Auto-trigger the Missing_Documentation_Advisor for claims where this assessment
    # itself signals a documentation problem (REFER, or REJECT on doc-related mandatory
    # evidence) — same gating a human uses manually from the Audit Log, just automatic
    # and non-blocking (background task, mirroring the MLflow write above) so every
    # future qualifying claim gets flagged right away instead of waiting on someone to
    # click the button.
    if data.get("claim_id") and _is_missing_docs_relevant(data.get("recommendation"), data.get("rule_checks")):
        background_tasks.add_task(_check_missing_docs_and_persist, data["claim_id"])

    # Write-back / cross-check is a purely observational side effect (see
    # _write_back_status_and_cross_check's docstring) — scheduled as a background task,
    # like the MLflow write above, instead of 2-3 synchronous Supabase round trips on
    # every single assessment.
    claim_id = data.get("claim_id")
    recommendation = data.get("recommendation")
    log_id = result.get("log_id")
    if claim_id and recommendation in CLAIM_STATUS_FROM_RECOMMENDATION:
        background_tasks.add_task(
            _write_back_status_and_cross_check,
            claim_id, recommendation, data.get("rule_checks"), log_id, skip_status_update,
        )

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


def _parse_upload_or_400(content: bytes, filename: str) -> list:
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    try:
        return parse_workflow_content(
            content.decode("utf-8"), workflow_name_fallback=Path(filename).stem
        )
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Not valid Dify DSL YAML: {exc}")


def _node_fingerprint(node_list: list) -> frozenset:
    return frozenset((n["node_type"], n["node_name"], n["content_hash"]) for n in node_list)


def _find_duplicate_upload(nodes: list, filename: str) -> Optional[str]:
    """
    Fingerprint this upload's trackable nodes (type, name, content_hash) and
    compare against every other file already in the bucket, using the same
    parse_workflow_content extraction the rest of DSL Change Management
    relies on. An exact match under a *different* filename means this upload
    adds nothing new/changed to what's already tracked — most likely a
    re-download saved under an auto-suffixed name (e.g. "Foo-3.yml") rather
    than a genuine new file.

    Can false-positive for a file that differs only outside tracked node
    types (layout, untracked nodes, workflow-level settings) — rare, and
    deliberately treated as a warning rather than a block for that reason.
    """
    new_fingerprint = _node_fingerprint(nodes)
    if not new_fingerprint:
        return None
    for existing_name in _list_workflow_storage_files():
        if existing_name == filename:
            continue
        _, existing_nodes, error = _download_and_parse_workflow(existing_name)
        if error or not existing_nodes:
            continue
        if _node_fingerprint(existing_nodes) == new_fingerprint:
            return existing_name
    return None


@app.post("/dsl/upload/check-duplicate")
async def dsl_upload_check_duplicate(file: UploadFile = File(...)):
    """
    Read-only pre-check for the Upload Workflow UI: parses the selected file
    and reports whether its tracked node content already matches another file
    in Storage, *without* writing anything. Lets the frontend warn the user
    before they click Upload, the same way the existing-filename overwrite
    warning already does.
    """
    if not (file.filename.endswith(".yml") or file.filename.endswith(".yaml")):
        raise HTTPException(status_code=400, detail="Only .yml/.yaml files are accepted")

    content = await file.read()
    nodes = _parse_upload_or_400(content, file.filename)
    duplicate_of = _find_duplicate_upload(nodes, file.filename)

    return {
        "filename": file.filename,
        "node_count": len(nodes),
        "workflow_name": nodes[0]["workflow_name"] if nodes else Path(file.filename).stem,
        "duplicate_of": duplicate_of,
    }


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
    nodes = _parse_upload_or_400(content, file.filename)
    duplicate_of = _find_duplicate_upload(nodes, file.filename)

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
        "duplicate_of": duplicate_of,
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