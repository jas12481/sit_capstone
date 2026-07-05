"""
backfill_claim_evidence.py

One-time synthetic-data backfill, following generate_data.py's conventions (Faker +
random.seed(42) for reproducibility). Resolves gaps discovered during evaluation-study
testing on 2026-07-06, where several mandatory eligibility rules could never be confirmed
passing for ANY claim of a given type, because the underlying data simply didn't capture
what the rule was checking:

- health:      RULE-HE-005 (Pre-existing Condition Exclusion) — no diagnosis or
               pre-existing-condition field existed anywhere in the schema.
- critical_illness: RULE-CI-006 (Medical Certification) — claim_documents had no content
               field, so a document's mere presence couldn't confirm what it certified.
- disability:  RULE-DI-004/006/007 (Medical Certification / Occupation Verification /
               Self-inflicted Exclusion) — same content-gap issue.
- life:        RULE-LI-005 (Accidental Death Evidence) — only applies to the 18
               accidental_death claims; same content-gap issue.

Fixed at the schema level via 3 new columns (claims.diagnosis, claims.condition_is_pre_existing,
claim_documents.content_summary) — this script backfills real, varied values into them.

Deliberately injects realistic outcome diversity rather than making every claim resolve to
APPROVE:
- condition_is_pre_existing: weighted True ~15% of health claims (fails RULE-HE-005 on its
  own, independent of anything else).
- disability medical reports: ~10% leave the self-inflicted question ambiguous (fails
  RULE-DI-007 on its own).
- CI specialist reports, disability proof-of-occupation, and life police/coroner reports are
  presence-only rules per their actual rule_description/condition text (no content-truth
  claim to vary) — always included once seeded, since that's what the rule actually checks.

Independent of this script, REJECT diversity already exists dataset-wide from policy status /
waiting-period / sum-assured / survival-period rules — untouched by this backfill.

Usage:
    python backfill_claim_evidence.py --dry-run     # preview counts, no writes
    python backfill_claim_evidence.py                # execute for real
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker
from supabase import create_client

REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / "mcp_server" / ".env")

import os  # noqa: E402
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
fake = Faker("en_US")

BATCH_SIZE = 100

HEALTH_DIAGNOSES = {
    "hospitalisation": [
        "Community-acquired pneumonia requiring inpatient admission",
        "Acute gastroenteritis with dehydration requiring IV fluids",
        "Cellulitis requiring IV antibiotic treatment",
        "Acute kidney stone (renal colic) requiring inpatient management",
        "Diabetic ketoacidosis requiring inpatient stabilisation",
    ],
    "surgical": [
        "Laparoscopic appendectomy",
        "Laparoscopic cholecystectomy (gallbladder removal)",
        "Inguinal hernia repair",
        "Knee arthroscopy for meniscus tear",
        "Tonsillectomy",
        "Cataract surgery",
    ],
    "outpatient": [
        "Routine specialist consultation for hypertension management",
        "Follow-up consultation post-discharge",
        "Minor wound dressing and review",
        "Outpatient physiotherapy for lower back pain",
        "Skin lesion biopsy",
        "Allergy testing and consultation",
    ],
    "emergency": [
        "Acute asthma exacerbation",
        "Road traffic accident with minor lacerations",
        "Acute chest pain, cardiac event ruled out",
        "Severe allergic reaction (anaphylaxis)",
        "Fall resulting in fracture",
        "Acute abdominal pain of unclear origin",
    ],
}

CI_SPECIALIST_TEXT = {
    "stroke": "Neurology specialist confirms diagnosis of acute ischaemic stroke, meeting the policy's covered critical illness definition.",
    "heart_attack": "Cardiology specialist confirms diagnosis of acute myocardial infarction (heart attack), meeting the policy's covered critical illness definition.",
    "kidney_failure": "Nephrology specialist confirms diagnosis of end-stage renal failure requiring dialysis, meeting the policy's covered critical illness definition.",
    "major_organ_transplant": "Transplant specialist confirms the insured underwent a major organ transplant procedure, meeting the policy's covered critical illness definition.",
    "cancer": "Oncology specialist confirms diagnosis of a malignant tumour meeting the policy's covered critical illness definition.",
}

DISABILITY_CATEGORY_TEXT = {
    "total_temporary_disability": "temporary inability to work due to the diagnosed injury/illness",
    "total_permanent_disability": "permanent and total incapacity, confirmed by medical assessment",
    "partial_permanent_disability": "partial permanent impairment, confirmed by medical assessment",
    "occupational_disability": "inability to perform occupational duties, confirmed by medical assessment",
}

HOSPITALS = [
    "Singapore General Hospital", "Tan Tock Seng Hospital", "Mount Elizabeth Hospital",
    "Raffles Hospital", "Gleneagles Hospital", "National University Hospital",
    "Changi General Hospital", "KK Women's and Children's Hospital",
]
CLINICS = [
    "Raffles Medical Clinic", "Healthway Medical Clinic", "Parkway Shenton Clinic",
    "Fullerton Health Clinic", "OneCare Clinic",
]

NOT_SELF_INFLICTED_TEXT = (
    "The attending physician's assessment explicitly states the condition was accidental "
    "in nature and was not self-inflicted."
)
AMBIGUOUS_SELF_INFLICTED_TEXT = (
    "The attending physician's report does not explicitly exclude the possibility of "
    "self-infliction; further clinical review may be required."
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


def backfill_health(dry_run: bool) -> int:
    claims = _paginate("claims", "claim_id,claim_category,diagnosis", {"claim_type": "health"})
    todo = [c for c in claims if c.get("diagnosis") is None]
    print(f"[health] {len(todo)} of {len(claims)} claims need diagnosis/condition_is_pre_existing")

    if dry_run:
        for c in todo[:3]:
            cat = c["claim_category"]
            diag = random.choice(HEALTH_DIAGNOSES.get(cat, ["General medical treatment"]))
            pre_existing = random.random() < 0.15
            print(f"  [DRY RUN] {c['claim_id']} ({cat}) -> diagnosis='{diag}', condition_is_pre_existing={pre_existing}")
        return len(todo)

    for i, c in enumerate(todo, 1):
        cat = c["claim_category"]
        diag = random.choice(HEALTH_DIAGNOSES.get(cat, ["General medical treatment"]))
        pre_existing = random.random() < 0.15
        supabase.table("claims").update({
            "diagnosis": diag,
            "condition_is_pre_existing": pre_existing,
        }).eq("claim_id", c["claim_id"]).execute()
        if i % 100 == 0:
            print(f"  ...{i}/{len(todo)} health claims updated")
    print(f"  Done — {len(todo)} health claims updated")
    return len(todo)


NOTES_DONE_MARKER = "approved network facility"


def backfill_health_notes(dry_run: bool) -> int:
    """Rewrites claims.notes for health claims to name a real facility + attending
    physician, resolving RULE-HE-004 dataset-wide. Originally notes was pure Faker
    filler text, so this rule could never be confirmed for any health claim regardless
    of what else got fixed. References the claim's own diagnosis (already backfilled by
    backfill_health) so the two fields read consistently."""
    claims = _paginate("claims", "claim_id,claim_category,notes,diagnosis", {"claim_type": "health"})
    todo = [c for c in claims if NOTES_DONE_MARKER not in (c.get("notes") or "")]
    print(f"[health notes] {len(todo)} of {len(claims)} claims need a real facility named in notes")

    def _build_notes(c: dict) -> str:
        cat = c["claim_category"]
        diag = c.get("diagnosis") or "the diagnosed condition"
        physician = fake.name()
        if cat in ("hospitalisation", "emergency"):
            facility = random.choice(HOSPITALS)
            return (f"Patient treated for {diag} at {facility}, an approved network facility. "
                    f"Attending physician: Dr. {physician}.")
        if cat == "surgical":
            facility = random.choice(HOSPITALS)
            return (f"Patient underwent {diag} at {facility}, an approved network facility. "
                    f"Attending surgeon: Dr. {physician}.")
        facility = random.choice(CLINICS)
        return (f"Patient seen for {diag} at {facility}, an approved network facility. "
                f"Attending physician: Dr. {physician}.")

    if dry_run:
        for c in todo[:3]:
            print(f"  [DRY RUN] {c['claim_id']} -> {_build_notes(c)}")
        return len(todo)

    for i, c in enumerate(todo, 1):
        supabase.table("claims").update({"notes": _build_notes(c)}).eq("claim_id", c["claim_id"]).execute()
        if i % 100 == 0:
            print(f"  ...{i}/{len(todo)} health notes rewritten")
    print(f"  Done — {len(todo)} health notes rewritten")
    return len(todo)


def _existing_doc_claim_ids(document_type: str) -> set[str]:
    resp = supabase.table("claim_documents").select("claim_id").eq("document_type", document_type).execute()
    return {r["claim_id"] for r in (resp.data or [])}


def backfill_critical_illness(dry_run: bool) -> int:
    claims = _paginate("claims", "claim_id,claim_category", {"claim_type": "critical_illness"})
    already = _existing_doc_claim_ids("specialist_medical_report")
    todo = [c for c in claims if c["claim_id"] not in already]
    print(f"[critical_illness] {len(todo)} of {len(claims)} claims need a specialist_medical_report")

    rows = []
    for c in todo:
        cat = c["claim_category"]
        summary = CI_SPECIALIST_TEXT.get(cat, "Specialist confirms diagnosis meeting the policy's covered critical illness definition.")
        rows.append({
            "claim_id": c["claim_id"],
            "document_type": "specialist_medical_report",
            "document_name": f"Specialist Medical Report - {c['claim_id']}.pdf",
            "pdf_url": f"https://example-synthetic-docs.local/{c['claim_id']}/specialist_medical_report.pdf",
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
    print(f"  Done — {len(rows)} specialist reports inserted")
    return len(rows)


def backfill_disability(dry_run: bool) -> int:
    claims = _paginate("claims", "claim_id,claim_category", {"claim_type": "disability"})
    already_medical = _existing_doc_claim_ids("medical_report")
    already_occupation = _existing_doc_claim_ids("proof_of_occupation")

    medical_todo = [c for c in claims if c["claim_id"] not in already_medical]
    occupation_todo = [c for c in claims if c["claim_category"] == "occupational_disability" and c["claim_id"] not in already_occupation]
    print(f"[disability] {len(medical_todo)} of {len(claims)} claims need a medical_report")
    print(f"[disability] {len(occupation_todo)} occupational_disability claims need proof_of_occupation")

    medical_rows = []
    for c in medical_todo:
        cat = c["claim_category"]
        cat_text = DISABILITY_CATEGORY_TEXT.get(cat, "disability confirmed by medical assessment")
        self_inflicted_text = AMBIGUOUS_SELF_INFLICTED_TEXT if random.random() < 0.10 else NOT_SELF_INFLICTED_TEXT
        summary = f"Medical report confirms {cat_text}. {self_inflicted_text}"
        medical_rows.append({
            "claim_id": c["claim_id"],
            "document_type": "medical_report",
            "document_name": f"Medical Report - {c['claim_id']}.pdf",
            "pdf_url": f"https://example-synthetic-docs.local/{c['claim_id']}/medical_report.pdf",
            "content_summary": summary,
        })

    occupation_rows = []
    for c in occupation_todo:
        occupation_rows.append({
            "claim_id": c["claim_id"],
            "document_type": "proof_of_occupation",
            "document_name": f"Proof of Occupation - {c['claim_id']}.pdf",
            "pdf_url": f"https://example-synthetic-docs.local/{c['claim_id']}/proof_of_occupation.pdf",
            "content_summary": "Employer letter and payslips confirming occupation and employment status at the time of disability onset.",
        })

    if dry_run:
        for r in medical_rows[:3]:
            print(f"  [DRY RUN medical] {r['claim_id']} -> {r['content_summary']}")
        for r in occupation_rows[:3]:
            print(f"  [DRY RUN occupation] {r['claim_id']} -> {r['content_summary']}")
        return len(medical_rows) + len(occupation_rows)

    for i in range(0, len(medical_rows), BATCH_SIZE):
        batch = medical_rows[i:i + BATCH_SIZE]
        supabase.table("claim_documents").insert(batch).execute()
        print(f"  ...medical_report batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
    for i in range(0, len(occupation_rows), BATCH_SIZE):
        batch = occupation_rows[i:i + BATCH_SIZE]
        supabase.table("claim_documents").insert(batch).execute()
        print(f"  ...proof_of_occupation batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
    print(f"  Done — {len(medical_rows)} medical reports, {len(occupation_rows)} proof-of-occupation docs inserted")
    return len(medical_rows) + len(occupation_rows)


def backfill_life(dry_run: bool) -> int:
    claims = _paginate("claims", "claim_id,claim_category", {"claim_type": "life"})
    accidental = [c for c in claims if c["claim_category"] == "accidental_death"]
    already = _existing_doc_claim_ids("police_report") | _existing_doc_claim_ids("coroner_report")
    todo = [c for c in accidental if c["claim_id"] not in already]
    print(f"[life] {len(todo)} of {len(accidental)} accidental_death claims need a police/coroner report")

    rows = []
    for c in todo:
        doc_type = random.choice(["police_report", "coroner_report"])
        label = "Police Report" if doc_type == "police_report" else "Coroner's Report"
        rows.append({
            "claim_id": c["claim_id"],
            "document_type": doc_type,
            "document_name": f"{label} - {c['claim_id']}.pdf",
            "pdf_url": f"https://example-synthetic-docs.local/{c['claim_id']}/{doc_type}.pdf",
            "content_summary": f"{label} confirms the death resulted from an accidental incident, consistent with the accidental death benefit definition under the policy.",
        })

    if dry_run:
        for r in rows[:3]:
            print(f"  [DRY RUN] {r['claim_id']} -> {r['document_type']}: {r['content_summary']}")
        return len(rows)

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        supabase.table("claim_documents").insert(batch).execute()
        print(f"  ...batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
    print(f"  Done — {len(rows)} police/coroner reports inserted")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill claim diagnosis/document-evidence fields")
    parser.add_argument("--dry-run", action="store_true", help="Preview counts/samples without writing")
    args = parser.parse_args()

    random.seed(42)

    print(f"{'='*60}\n  {'DRY RUN — ' if args.dry_run else ''}Claim evidence backfill\n{'='*60}\n")
    n_health = backfill_health(args.dry_run)
    print()
    n_health_notes = backfill_health_notes(args.dry_run)
    print()
    n_ci = backfill_critical_illness(args.dry_run)
    print()
    n_disability = backfill_disability(args.dry_run)
    print()
    n_life = backfill_life(args.dry_run)

    print(f"\n{'='*60}")
    print(f"  Health rows touched      : {n_health}")
    print(f"  Health notes rewritten   : {n_health_notes}")
    print(f"  CI documents inserted    : {n_ci}")
    print(f"  Disability docs inserted : {n_disability}")
    print(f"  Life documents inserted  : {n_life}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
