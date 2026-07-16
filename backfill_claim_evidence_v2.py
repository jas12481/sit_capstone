"""
backfill_claim_evidence_v2.py

Second-pass backfill, same conventions as backfill_claim_evidence.py (Faker +
random.seed(42), one-time, idempotent — skips claims that already have the target data).
Closes the gaps found while cross-referencing the 8 synthetic rejection_reason categories
against what eligibility_rules could actually verify (see PROJECT_CONTEXT.md / session
history for the full review):

- life/critical_illness/disability: claims.diagnosis / claims.condition_is_pre_existing
  were populated for health only — RULE-LI-006/RULE-CI-007/RULE-DI-008 (new "Pre-existing
  Condition Exclusion" rules) would otherwise always return UNKNOWN.
- health: zero claim_documents existed at all — RULE-HE-007 (new "Medical Documentation
  Required") would otherwise always FAIL.
- life death/total_permanent_disability categories: zero claim_documents existed (only
  accidental_death had police/coroner reports) — RULE-LI-007/RULE-LI-008 (new) would
  otherwise always FAIL.

Consistency-aware, not just presence-filling: a claim already carrying
rejection_reason="Condition is a pre-existing illness not declared at underwriting" gets
condition_is_pre_existing forced True (not just weighted-random) so that specific claim's
story is actually coherent. Same logic withholds the new document backfill from any claim
already carrying rejection_reason="Insufficient supporting documents provided" — so that
reason becomes genuinely true for those claims instead of being contradicted by a document
this same script would otherwise add. (Note: this consistency check is NOT retroactively
applied to critical_illness/disability's original backfill in backfill_claim_evidence.py —
those claims may still have this same latent inconsistency; out of scope for this pass.)

Usage:
    python backfill_claim_evidence_v2.py --dry-run
    python backfill_claim_evidence_v2.py
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / "mcp_server" / ".env")

import os  # noqa: E402
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

BATCH_SIZE = 100
INSUFFICIENT_DOCS_REASON = "Insufficient supporting documents provided"
PRE_EXISTING_REASON = "Condition is a pre-existing illness not declared at underwriting"

LIFE_DIAGNOSES = {
    "death": [
        "Sudden cardiac arrest",
        "Metastatic cancer",
        "Acute respiratory failure",
        "Multi-organ failure following prolonged illness",
        "Fatal cerebrovascular accident (stroke)",
    ],
    "total_permanent_disability": [
        "Traumatic spinal cord injury resulting in permanent paraplegia",
        "Severe traumatic brain injury resulting in permanent incapacity",
        "Bilateral limb amputation following traumatic injury",
        "Total and irreversible loss of vision in both eyes",
    ],
    "accidental_death": [
        "Fatal injuries sustained in a road traffic accident",
        "Fatal injuries sustained in a workplace accident",
        "Fatal drowning incident",
    ],
}

CI_DIAGNOSES = {
    "cancer": ["Malignant tumour requiring oncological treatment", "Stage III adenocarcinoma"],
    "heart_attack": ["Acute myocardial infarction", "ST-elevation myocardial infarction (STEMI)"],
    "stroke": ["Acute ischaemic stroke", "Haemorrhagic stroke"],
    "kidney_failure": ["End-stage renal failure requiring dialysis", "Chronic kidney disease stage 5"],
    "major_organ_transplant": ["Liver transplant procedure", "Kidney transplant procedure", "Heart transplant procedure"],
}

DISABILITY_DIAGNOSES = {
    "total_temporary_disability": [
        "Lumbar disc herniation causing temporary incapacity",
        "Fractured femur requiring extended recovery",
        "Severe concussion with temporary cognitive impairment",
    ],
    "total_permanent_disability": [
        "Traumatic spinal cord injury resulting in permanent paralysis",
        "Severe traumatic brain injury resulting in permanent incapacity",
        "Bilateral limb amputation",
    ],
    "partial_permanent_disability": [
        "Partial loss of function in dominant hand following traumatic injury",
        "Partial hearing loss following occupational injury",
        "Partial vision loss in one eye",
    ],
    "occupational_disability": [
        "Repetitive strain injury preventing performance of occupational duties",
        "Chronic lower back injury preventing manual labour",
        "Occupational hearing loss",
    ],
}

HEALTH_MEDICAL_REPORT_TEXT = (
    "Medical report and itemised invoice from the treating facility confirm {diagnosis}, "
    "consistent with the claim's {category} category."
)
LIFE_DEATH_DOC_TEXT = (
    "Death certificate issued by the Registry of Births and Deaths confirms date and cause "
    "of death as {diagnosis}. Attending physician's report corroborates the cause of death."
)
LIFE_TPD_DOC_TEXT = (
    "Medical report from a registered medical practitioner confirms {diagnosis}, meeting the "
    "policy's total permanent disability definition (permanent and total incapacity)."
)


def _paginate(table: str, select: str, filters: dict | None = None) -> list[dict]:
    rows: list[dict] = []
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


def _existing_doc_claim_ids(document_type: str) -> set[str]:
    resp = supabase.table("claim_documents").select("claim_id").eq("document_type", document_type).execute()
    return {r["claim_id"] for r in (resp.data or [])}


def _pre_existing_value(rejection_reason: str | None, weight: float = 0.15) -> bool:
    if rejection_reason == PRE_EXISTING_REASON:
        return True
    return random.random() < weight


def backfill_conditions(policy_type: str, diagnosis_pool: dict, dry_run: bool) -> int:
    claims = _paginate(
        "claims", "claim_id,claim_category,diagnosis,rejection_reason",
        {"claim_type": policy_type},
    )
    todo = [c for c in claims if c.get("diagnosis") is None]
    print(f"[{policy_type}] {len(todo)} of {len(claims)} claims need diagnosis/condition_is_pre_existing")

    if dry_run:
        for c in todo[:3]:
            cat = c["claim_category"]
            diag = random.choice(diagnosis_pool.get(cat, ["Condition confirmed by medical assessment"]))
            pre_existing = _pre_existing_value(c.get("rejection_reason"))
            print(f"  [DRY RUN] {c['claim_id']} ({cat}) -> diagnosis='{diag}', condition_is_pre_existing={pre_existing}")
        return len(todo)

    for i, c in enumerate(todo, 1):
        cat = c["claim_category"]
        diag = random.choice(diagnosis_pool.get(cat, ["Condition confirmed by medical assessment"]))
        pre_existing = _pre_existing_value(c.get("rejection_reason"))
        supabase.table("claims").update({
            "diagnosis": diag,
            "condition_is_pre_existing": pre_existing,
        }).eq("claim_id", c["claim_id"]).execute()
        if i % 100 == 0:
            print(f"  ...{i}/{len(todo)} {policy_type} claims updated")
    print(f"  Done — {len(todo)} {policy_type} claims updated")
    return len(todo)


def backfill_health_documents(dry_run: bool) -> int:
    claims = _paginate(
        "claims", "claim_id,claim_category,diagnosis,rejection_reason",
        {"claim_type": "health"},
    )
    already = _existing_doc_claim_ids("medical_report")
    withheld = [c for c in claims if c.get("rejection_reason") == INSUFFICIENT_DOCS_REASON]
    withheld_ids = {c["claim_id"] for c in withheld}
    todo = [c for c in claims if c["claim_id"] not in already and c["claim_id"] not in withheld_ids]
    print(f"[health documents] {len(todo)} of {len(claims)} claims get a medical_report "
          f"({len(withheld)} withheld — already labeled '{INSUFFICIENT_DOCS_REASON}')")

    rows = []
    for c in todo:
        diag = c.get("diagnosis") or "the diagnosed condition"
        summary = HEALTH_MEDICAL_REPORT_TEXT.format(diagnosis=diag, category=c["claim_category"])
        rows.append({
            "claim_id": c["claim_id"],
            "document_type": "medical_report",
            "document_name": f"Medical Report - {c['claim_id']}.pdf",
            "pdf_url": f"https://example-synthetic-docs.local/{c['claim_id']}/medical_report.pdf",
            "content_summary": summary,
        })

    if dry_run:
        for r in rows[:3]:
            print(f"  [DRY RUN] {r['claim_id']} -> {r['content_summary']}")
        return len(rows)

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        supabase.table("claim_documents").insert(batch).execute()
        print(f"  ...batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
    print(f"  Done — {len(rows)} health medical reports inserted")
    return len(rows)


def backfill_life_death_tpd_documents(dry_run: bool) -> int:
    claims = _paginate(
        "claims", "claim_id,claim_category,diagnosis,rejection_reason",
        {"claim_type": "life"},
    )
    death_claims = [c for c in claims if c["claim_category"] == "death"]
    tpd_claims = [c for c in claims if c["claim_category"] == "total_permanent_disability"]

    already_death = _existing_doc_claim_ids("death_certificate")
    already_tpd = _existing_doc_claim_ids("tpd_medical_certification")

    withheld_death = {c["claim_id"] for c in death_claims if c.get("rejection_reason") == INSUFFICIENT_DOCS_REASON}
    withheld_tpd = {c["claim_id"] for c in tpd_claims if c.get("rejection_reason") == INSUFFICIENT_DOCS_REASON}

    death_todo = [c for c in death_claims if c["claim_id"] not in already_death and c["claim_id"] not in withheld_death]
    tpd_todo = [c for c in tpd_claims if c["claim_id"] not in already_tpd and c["claim_id"] not in withheld_tpd]

    print(f"[life death] {len(death_todo)} of {len(death_claims)} claims get a death_certificate "
          f"({len(withheld_death)} withheld)")
    print(f"[life tpd] {len(tpd_todo)} of {len(tpd_claims)} claims get a tpd_medical_certification "
          f"({len(withheld_tpd)} withheld)")

    death_rows = []
    for c in death_todo:
        diag = c.get("diagnosis") or "the recorded cause of death"
        death_rows.append({
            "claim_id": c["claim_id"],
            "document_type": "death_certificate",
            "document_name": f"Death Certificate - {c['claim_id']}.pdf",
            "pdf_url": f"https://example-synthetic-docs.local/{c['claim_id']}/death_certificate.pdf",
            "content_summary": LIFE_DEATH_DOC_TEXT.format(diagnosis=diag),
        })

    tpd_rows = []
    for c in tpd_todo:
        diag = c.get("diagnosis") or "the diagnosed condition"
        tpd_rows.append({
            "claim_id": c["claim_id"],
            "document_type": "tpd_medical_certification",
            "document_name": f"TPD Medical Certification - {c['claim_id']}.pdf",
            "pdf_url": f"https://example-synthetic-docs.local/{c['claim_id']}/tpd_medical_certification.pdf",
            "content_summary": LIFE_TPD_DOC_TEXT.format(diagnosis=diag),
        })

    if dry_run:
        for r in death_rows[:3]:
            print(f"  [DRY RUN death] {r['claim_id']} -> {r['content_summary']}")
        for r in tpd_rows[:3]:
            print(f"  [DRY RUN tpd] {r['claim_id']} -> {r['content_summary']}")
        return len(death_rows) + len(tpd_rows)

    for i in range(0, len(death_rows), BATCH_SIZE):
        batch = death_rows[i:i + BATCH_SIZE]
        supabase.table("claim_documents").insert(batch).execute()
        print(f"  ...death_certificate batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
    for i in range(0, len(tpd_rows), BATCH_SIZE):
        batch = tpd_rows[i:i + BATCH_SIZE]
        supabase.table("claim_documents").insert(batch).execute()
        print(f"  ...tpd_medical_certification batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
    print(f"  Done — {len(death_rows)} death certificates, {len(tpd_rows)} TPD certifications inserted")
    return len(death_rows) + len(tpd_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill v2 — pre-existing condition + document gaps")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    random.seed(42)

    print(f"{'='*60}\n  {'DRY RUN — ' if args.dry_run else ''}Claim evidence backfill v2\n{'='*60}\n")
    n_life = backfill_conditions("life", LIFE_DIAGNOSES, args.dry_run)
    print()
    n_ci = backfill_conditions("critical_illness", CI_DIAGNOSES, args.dry_run)
    print()
    n_disability = backfill_conditions("disability", DISABILITY_DIAGNOSES, args.dry_run)
    print()
    n_health_docs = backfill_health_documents(args.dry_run)
    print()
    n_life_docs = backfill_life_death_tpd_documents(args.dry_run)

    print(f"\n{'='*60}")
    print(f"  Life diagnosis/pre-existing rows       : {n_life}")
    print(f"  CI diagnosis/pre-existing rows         : {n_ci}")
    print(f"  Disability diagnosis/pre-existing rows : {n_disability}")
    print(f"  Health documents inserted              : {n_health_docs}")
    print(f"  Life death/TPD documents inserted      : {n_life_docs}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
