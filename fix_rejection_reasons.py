"""
fix_rejection_reasons.py

One-time targeted correction, run 2026-07-16 — does NOT regenerate the dataset. Resolves
gaps found while reviewing all 24 eligibility_rules against the 8 synthetic rejection_reason
categories: the original pool in generate_data.py was shared across all domains, so a claim
could be randomly assigned a reason no rule for its claim_type/claim_category could ever
verify (e.g. a health claim rejected for "Diagnosis does not meet the clinical criteria
defined in the policy" when no health rule checks diagnosis criteria at all).

Phase A: reassigns rejection_reason for claims whose currently-assigned reason has no
matching rule for their claim_type/claim_category (61 claims at time of run: 3 life, 39
health, 19 disability — critical_illness had none, since all 8 reasons are valid there
after the 2026-07-16 rule-coverage additions), using the same valid_reasons_for() logic
added to generate_data.py's valid_rejection_reasons().

Phase B: runs AFTER phase A commits (re-fetches fresh data) — for every claim across ALL
domains whose CURRENT rejection_reason is "Insufficient supporting documents provided",
checks whether the domain-appropriate document actually exists and removes it if so. This
covers both a pre-existing contradiction (critical_illness/disability claims that got a
document from the original backfill_claim_evidence.py run, which didn't check for this) and
any NEW contradiction phase A's reassignment could create (a claim reassigned to this reason
that already has a document from backfill_claim_evidence_v2.py, since it had a different
reason at the time that backfill ran). At time of run: 17 documents removed total.

Usage:
    python fix_rejection_reasons.py --dry-run [a|b]   # preview, no writes
    python fix_rejection_reasons.py [a|b]              # execute for real
    (phase defaults to "all" — run a first, let it commit, then run b separately, since b
    depends on a's writes already being live)
"""
import sys, os, random
sys.path.insert(0, os.getcwd())
os.chdir("mcp_server")
from dotenv import load_dotenv
load_dotenv(".env")
from supabase import create_client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
os.chdir("..")

UNIVERSAL = [
    "Claim submitted within waiting period",
    "Policy was lapsed at time of incident",
    "Claim amount exceeds sum assured",
    "Incident does not fall within policy coverage period",
]
PRE_EXISTING = "Condition is a pre-existing illness not declared at underwriting"
INSUFFICIENT_DOCS = "Insufficient supporting documents provided"
CLINICAL_CRITERIA = "Diagnosis does not meet the clinical criteria defined in the policy"
SURVIVAL_PERIOD = "Survival period of 30 days not satisfied"

# domain/category -> document_type(s) that would satisfy the documentation rule for that
# claim, and therefore must NOT be present if rejection_reason says documents are missing
DOC_TYPES_THAT_SATISFY = {
    ("health", None): ["medical_report"],
    ("critical_illness", None): ["specialist_medical_report"],
    ("disability", None): ["medical_report"],
    ("life", "accidental_death"): ["police_report", "coroner_report"],
    ("life", "death"): ["death_certificate"],
    ("life", "total_permanent_disability"): ["tpd_medical_certification"],
}


def valid_reasons_for(claim_type, claim_category):
    reasons = list(UNIVERSAL)
    if claim_type == "critical_illness":
        reasons += [PRE_EXISTING, INSUFFICIENT_DOCS, CLINICAL_CRITERIA, SURVIVAL_PERIOD]
    elif claim_type == "health":
        reasons += [PRE_EXISTING, INSUFFICIENT_DOCS]
    elif claim_type == "disability":
        reasons += [PRE_EXISTING, INSUFFICIENT_DOCS]
    elif claim_type == "life":
        if claim_category == "accidental_death":
            reasons += [INSUFFICIENT_DOCS]
        elif claim_category == "death":
            reasons += [PRE_EXISTING, INSUFFICIENT_DOCS]
        elif claim_category == "total_permanent_disability":
            reasons += [PRE_EXISTING, INSUFFICIENT_DOCS, CLINICAL_CRITERIA]
    return reasons


def _doc_types_for(domain, category):
    return DOC_TYPES_THAT_SATISFY.get((domain, category)) or DOC_TYPES_THAT_SATISFY.get((domain, None)) or []


def _paginate(table, select, filters=None):
    rows = []
    start = 0
    page = 1000
    while True:
        q = supabase.table(table).select(select)
        for k, v in (filters or {}).items():
            q = q.eq(k, v)
        resp = q.range(start, start + page - 1).execute()
        if not resp.data:
            break
        rows.extend(resp.data)
        if len(resp.data) < page:
            break
        start += page
    return rows


def fix_mismatched_reasons(dry_run):
    random.seed(42)
    fixed = 0
    for domain in ["life", "health", "critical_illness", "disability"]:
        claims = _paginate("claims", "claim_id,claim_category,rejection_reason", {"claim_type": domain, "status": "rejected"})
        for c in claims:
            valid = valid_reasons_for(domain, c["claim_category"])
            if c.get("rejection_reason") not in valid:
                new_reason = random.choice(valid)
                if dry_run:
                    print(f"  [DRY RUN] {c['claim_id']} ({domain}/{c['claim_category']}): "
                          f"'{c['rejection_reason']}' -> '{new_reason}'")
                else:
                    supabase.table("claims").update({"rejection_reason": new_reason}).eq("claim_id", c["claim_id"]).execute()
                fixed += 1
    print(f"{'Would fix' if dry_run else 'Fixed'}: {fixed} claims")
    return fixed


def fix_contradicting_documents(dry_run):
    """Runs against CURRENT data — call after phase A has committed for real."""
    removed = 0
    for domain in ["life", "health", "critical_illness", "disability"]:
        claims = _paginate(
            "claims", "claim_id,claim_category",
            {"claim_type": domain, "status": "rejected", "rejection_reason": INSUFFICIENT_DOCS},
        )
        for c in claims:
            doc_types = _doc_types_for(domain, c["claim_category"])
            if not doc_types:
                continue
            docs = supabase.table("claim_documents").select("document_id,document_type").eq("claim_id", c["claim_id"]).execute()
            for d in (docs.data or []):
                if d["document_type"] in doc_types:
                    if dry_run:
                        print(f"  [DRY RUN] would remove {d['document_type']} from {c['claim_id']} ({domain}/{c['claim_category']})")
                    else:
                        supabase.table("claim_documents").delete().eq("document_id", d["document_id"]).execute()
                    removed += 1
    print(f"{'Would remove' if dry_run else 'Removed'}: {removed} contradicting documents")
    return removed


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    phase = next((a for a in sys.argv[1:] if a in ("a", "b")), "all")
    print(f"{'='*60}\n  {'DRY RUN — ' if dry_run else ''}Rejection reason correction ({phase})\n{'='*60}\n")
    if phase in ("all", "a"):
        fix_mismatched_reasons(dry_run)
        print()
    if phase in ("all", "b"):
        fix_contradicting_documents(dry_run)
