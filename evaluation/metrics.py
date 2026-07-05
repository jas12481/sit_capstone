"""
Pure scoring functions for the 4-strategy (Direct/CoT/Structured/Combined) recommendation-
accuracy research study. No I/O here — run_evaluation.py fetches data and calls these.

Direct/CoT are unstructured text by design (that's the point of the ablation — no schema
enforcement), so extraction from their raw output is lossier than reading Structured/Combined's
JSON directly. That lossiness is itself part of what the study measures, not a bug to hide.
"""

from __future__ import annotations

import re

VALID_RECOMMENDATIONS = {"APPROVE", "REJECT", "REFER_FOR_FURTHER_REVIEW"}
CONFIDENCE_SCALE = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.0}
RULE_ID_PATTERN = re.compile(r"\bRULE-[A-Z]{2,4}-\d{2,4}\b")


def extract_recommendation_from_text(text: str) -> str | None:
    """
    Extracts APPROVE/REJECT/REFER_FOR_FURTHER_REVIEW from unstructured Direct/CoT output.
    Prefers CoT's fixed-format 'Final Recommendation: X' line if present; falls back to a
    bare search for whichever valid token appears (last occurrence wins, since a reasoning
    trace may mention a rejected/approved *rule* before stating its actual conclusion).
    """
    if not text:
        return None

    m = re.search(r"Final Recommendation:\s*([A-Z_]+)", text, re.IGNORECASE)
    if m:
        token = m.group(1).upper()
        if token in VALID_RECOMMENDATIONS:
            return token

    found = [tok for tok in VALID_RECOMMENDATIONS if tok in text.upper()]
    if not found:
        return None
    # last valid token by position in text — favors a trailing conclusion over an
    # earlier mention (e.g. "this is not a REJECT case... APPROVE")
    positions = [(text.upper().rfind(tok), tok) for tok in found]
    return max(positions)[1]


def extract_cited_rule_ids_from_text(text: str) -> list[str]:
    """Regex-extracts rule-ID-shaped substrings (e.g. RULE-HE-004) from unstructured text."""
    if not text:
        return []
    return sorted(set(RULE_ID_PATTERN.findall(text)))


def check_recommendation_correct(actual: str | None, expected: str) -> bool:
    """
    Exact match, with one special case: expected == "ERROR_OR_GRACEFUL_REJECT" (the
    domain-mismatch test cases in test_claims.json) is satisfied by either a REJECT
    recommendation or an errored call (actual == "ERROR", set by run_evaluation.py's
    try/except wrapper when the Dify call itself fails).
    """
    if expected == "ERROR_OR_GRACEFUL_REJECT":
        return actual in ("REJECT", "ERROR")
    return actual == expected


def count_hallucinated_rules(cited_rule_ids: list[str], real_rule_ids: list[str]) -> int:
    """Count of cited rule IDs that don't exist in the real eligibility_rules set for this policy_type."""
    real = set(real_rule_ids)
    return sum(1 for rid in cited_rule_ids if rid not in real)


def count_valid_clause_references(cited_clauses: list[str], policy_text: str) -> int:
    """Count of cited clause/section references that are actually findable in the real policy_text."""
    if not policy_text:
        return 0
    return sum(1 for clause in cited_clauses if clause and clause in policy_text)


def count_hallucinated_clauses(cited_clauses: list[str], policy_text: str) -> int:
    """Inverse of count_valid_clause_references — cited clauses not findable in policy_text."""
    return len(cited_clauses) - count_valid_clause_references(cited_clauses, policy_text)


def confidence_to_numeric(level: str | None) -> float | None:
    """HIGH=1.0, MEDIUM=0.5, LOW=0.0, per the documented scale. None for anything unrecognized."""
    if level is None:
        return None
    return CONFIDENCE_SCALE.get(level.upper())
