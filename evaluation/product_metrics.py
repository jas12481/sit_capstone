"""
Pure scoring functions for the 3 product-capability apps (Missing_Documentation_Advisor,
Fraud_Anomaly_Risk_Signals, Explain_Assessment_Reasoning). No I/O here — run_product_evaluation.py
fetches data and calls these. None of these apps produce an APPROVE/REJECT/REFER recommendation,
so none of evaluation/metrics.py's functions apply — these are separate, capability-specific metrics.
"""

from __future__ import annotations

import re

VALID_RECOMMENDATIONS = {"APPROVE", "REJECT", "REFER_FOR_FURTHER_REVIEW"}


def _coerce_bool(v) -> bool | None:
    """Structured-output booleans have come back as literal strings ("yes"/"no"/"true"/"false")
    in real testing this session (Missing_Documentation_Advisor), not just real bools — this
    normalizes both forms rather than assuming a clean Python bool."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        low = v.strip().lower()
        if low in ("true", "yes"):
            return True
        if low in ("false", "no"):
            return False
    return None


# ── Missing Documentation Advisor ────────────────────────────────────────────────

def missing_docs_precision_recall(predicted_missing_types: list[str], expected_missing_types: list[str]) -> dict:
    """
    Precision/recall on document_type strings the app flagged as missing vs. the real expected
    gap. Both empty (nothing missing, correctly) scores 1.0/1.0 — that's a genuine correct
    outcome, not an undefined one.
    """
    predicted = set(predicted_missing_types or [])
    expected = set(expected_missing_types or [])

    if not predicted and not expected:
        return {"precision": 1.0, "recall": 1.0, "true_positives": 0, "false_positives": 0, "false_negatives": 0}

    true_positives = len(predicted & expected)
    false_positives = len(predicted - expected)
    false_negatives = len(expected - predicted)

    precision = true_positives / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = true_positives / len(expected) if expected else (1.0 if not predicted else 0.0)

    return {
        "precision": precision,
        "recall": recall,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def all_requirements_met_correct(predicted, expected: bool) -> bool | None:
    """Compares all_requirements_met, coercing string forms ("yes"/"no") seen in real testing.
    Returns None (not scoreable) if predicted couldn't be parsed as a boolean at all."""
    predicted_bool = _coerce_bool(predicted)
    if predicted_bool is None:
        return None
    return predicted_bool == expected


# ── Fraud/Anomaly Risk Signals ───────────────────────────────────────────────────

def fraud_risk_level_correct(predicted: str | None, expected: str) -> bool:
    """Exact match on risk_level (LOW/MEDIUM/HIGH)."""
    if predicted is None:
        return False
    return predicted.strip().upper() == expected.strip().upper()


def fraud_flag_precision_recall(predicted_flags: list[dict], expected_signal_keywords: list[str]) -> dict:
    """
    Flags are free text (signal + explanation), not an enum, so this is a keyword/substring
    match rather than exact comparison. recall = fraction of expected keywords actually
    mentioned somewhere in the predicted flags; precision = fraction of predicted flags that
    match at least one expected keyword (a flag mentioning none of the expected keywords is
    still potentially a valid, just untested, finding — this is a looser precision notion than
    a strict enum match would give, by necessity of free text).
    """
    if not expected_signal_keywords:
        return {"precision": None, "recall": None, "matched_keywords": [], "unmatched_keywords": []}

    flag_text = " ".join(
        f"{f.get('signal', '')} {f.get('explanation', '')}" for f in (predicted_flags or [])
    ).lower()

    matched = [kw for kw in expected_signal_keywords if kw.lower() in flag_text]
    unmatched = [kw for kw in expected_signal_keywords if kw.lower() not in flag_text]
    recall = len(matched) / len(expected_signal_keywords)

    if not predicted_flags:
        precision = 0.0 if expected_signal_keywords else None
    else:
        matching_flags = sum(
            1 for f in predicted_flags
            if any(kw.lower() in f"{f.get('signal', '')} {f.get('explanation', '')}".lower() for kw in expected_signal_keywords)
        )
        precision = matching_flags / len(predicted_flags)

    return {"precision": precision, "recall": recall, "matched_keywords": matched, "unmatched_keywords": unmatched}


# ── Explain Assessment Reasoning (Mode A) ────────────────────────────────────────

def explanation_faithfulness(explanation_text: str, actual_recommendation: str, actual_mandatory_rules_failed: int) -> dict:
    """
    Checks whether a Mode A explanation (of an *existing* logged assessment) faithfully
    represents that logged outcome, rather than contradicting or re-deriving a different one.
    Free-text faithfulness is inherently fuzzy — this is a keyword/substring heuristic, not a
    semantic check, matching the same lossiness accepted for Direct/CoT extraction in metrics.py.
    """
    text = explanation_text or ""

    recommendation_mentioned = actual_recommendation.upper() in text.upper()

    # Word-boundary regex, not substring — a naive "APPROVE" in text.upper() also matches
    # "APPROVED"/"APPROVAL" (common English words, not the enum token), which produced false
    # contradictions on real explanations that legitimately say e.g. "cannot be approved"
    # while explaining a REJECT. \b correctly excludes those inflected forms.
    other_recommendations_mentioned = [
        rec for rec in VALID_RECOMMENDATIONS
        if rec != actual_recommendation.upper() and re.search(rf"\b{re.escape(rec)}\b", text, re.IGNORECASE)
    ]
    no_contradicting_recommendation = len(other_recommendations_mentioned) == 0

    # Negation-aware pattern matching, not exact-count extraction. Real explanations phrase
    # "0 mandatory rules failed" in unpredictable word orders ("mandatory rules failed: 0",
    # "0 mandatory rules failed", "no mandatory rules were breached", "no critical rule
    # breaches" with no number at all) — trying to regex out one canonical numeric position
    # broke on every phrasing variant except the one it was written against. Checking for
    # explicit negation/affirmation framing near "mandatory" + "fail/breach" generalizes much
    # better across the phrasings actually observed in testing.
    negation_zero_patterns = [
        r"\bno\s+mandatory\b.{0,40}?\b(fail|breach)",
        r"\b(0|zero)\s+mandatory\b.{0,40}?\b(fail|breach)",
        r"\bmandatory\b.{0,40}?\b(fail\w*|breach\w*)\b.{0,15}?\b(0|zero|none)\b",
        r"\ball\s+mandatory\b.{0,40}?\b(met|satisfied|passed)",
    ]
    positive_fail_patterns = [
        r"\bmandatory\b.{0,40}?\bfail",
        r"\bfail\w*\b.{0,40}?\bmandatory\b",
        r"\bmandatory\b.{0,40}?\bnot\s+met\b",
        r"\bmandatory\b.{0,40}?\bbreach",
    ]
    if actual_mandatory_rules_failed == 0:
        failure_consistent = any(re.search(p, text, re.IGNORECASE) for p in negation_zero_patterns)
    else:
        failure_consistent = any(re.search(p, text, re.IGNORECASE) for p in positive_fail_patterns)

    return {
        "recommendation_mentioned": recommendation_mentioned,
        "no_contradicting_recommendation": no_contradicting_recommendation,
        "other_recommendations_mentioned": other_recommendations_mentioned,
        "failure_consistent": failure_consistent,
        "is_faithful": recommendation_mentioned and no_contradicting_recommendation and failure_consistent,
    }
