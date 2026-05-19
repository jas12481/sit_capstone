from fastapi import FastAPI, Query, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
import os

load_dotenv()

app = FastAPI(title="AIA Capstone MCP Server", version="1.0.0")

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "AIA MCP Server"}

# ── CLAIMS ───────────────────────────────────────────────────────────────────

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

# ── ASSESSMENT (combined claim + policy + rules in one call) ──────────────────

@app.get("/assessment")
def get_assessment_data(claim_id: str = Query(...)):
    # Fetch claim
    claim_response = supabase.table("claims").select("*").eq("claim_id", claim_id).execute()
    if not claim_response.data:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    claim = claim_response.data[0]

    # Fetch linked policy
    policy_response = supabase.table("policies").select("*").eq("policy_id", claim["policy_id"]).execute()
    if not policy_response.data:
        raise HTTPException(status_code=404, detail=f"Policy {claim['policy_id']} not found")
    policy = policy_response.data[0]

    # Fetch eligibility rules for this policy type
    rules_response = supabase.table("eligibility_rules").select("*").eq("policy_type", claim["claim_type"]).execute()

    return {
        "claim": claim,
        "policy": policy,
        "eligibility_rules": rules_response.data
    }