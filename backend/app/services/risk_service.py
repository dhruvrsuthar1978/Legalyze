# app/services/risk_service.py

import re
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger("legalyze.risk")


# ══════════════════════════════════════════════════════════════════
# RISK PATTERN REGISTRY
# Each entry: (pattern, risk_category, severity_score 1-10)
# ══════════════════════════════════════════════════════════════════

HIGH_RISK_PATTERNS: List[Tuple[str, str, int]] = [
    # Rights Waivers
    ("waive all rights",         "rights_waiver",      10),
    ("irrevocably waive",        "rights_waiver",      10),
    ("no right to",              "rights_waiver",       9),
    ("forfeit all",              "rights_waiver",       9),
    ("relinquish",               "rights_waiver",       8),

    # One-sided Control
    ("sole discretion",          "one_sided_control",   9),
    ("absolute discretion",      "one_sided_control",   9),
    ("at our discretion",        "one_sided_control",   8),
    ("without your consent",     "one_sided_control",   9),
    ("unilaterally",             "one_sided_control",   8),

    # Financial Risk
    ("no refund",                "financial_risk",      9),
    ("non-refundable",           "financial_risk",      8),
    ("unlimited liability",      "financial_risk",     10),
    ("personal liability",       "financial_risk",      8),
    ("joint and several",        "financial_risk",      7),

    # Irrevocable / Perpetual
    ("irrevocable",              "irrevocable_terms",   9),
    ("perpetual license",        "irrevocable_terms",   8),
    ("in perpetuity",            "irrevocable_terms",   8),
    ("forever",                  "irrevocable_terms",   7),

    # Non-negotiable
    ("non-negotiable",           "non_negotiable",      9),
    ("take it or leave",         "non_negotiable",      9),
    ("absolute obligation",      "non_negotiable",      8),

    # Notice & Process
    ("without notice",           "due_process",         9),
    ("without prior notice",     "due_process",         9),
    ("immediate termination",    "due_process",         8),
    ("terminate immediately",    "due_process",         8),

    # Broad IP Assignment
    ("assign all rights",        "ip_risk",             9),
    ("all inventions",           "ip_risk",             8),
    ("worldwide exclusive",      "ip_risk",             8),
    ("all intellectual property","ip_risk",             8),

    # Broad Non-Compete
    ("any and all competition",  "non_compete",         9),
    ("any competing activity",   "non_compete",         8),
    ("worldwide non-compete",    "non_compete",         9),
    ("indefinite non-compete",   "non_compete",         9),
]

MEDIUM_RISK_PATTERNS: List[Tuple[str, str, int]] = [
    # Vague Obligations
    ("reasonable efforts",       "vague_obligation",    6),
    ("commercially reasonable",  "vague_obligation",    5),
    ("best efforts",             "vague_obligation",    5),
    ("as determined by",         "vague_obligation",    6),
    ("at the company's option",  "vague_obligation",    6),

    # Partial Rights
    ("limited license",          "limited_rights",      5),
    ("may terminate",            "conditional_risk",    5),
    ("subject to change",        "conditional_risk",    6),
    ("reserves the right",       "conditional_risk",    6),
    ("at our discretion",        "conditional_risk",    6),

    # Financial Medium
    ("partial refund",           "financial_risk",      5),
    ("pro-rata",                 "financial_risk",      4),
    ("variable fee",             "financial_risk",      5),
    ("additional charges",       "financial_risk",      6),
    ("late payment penalty",     "financial_risk",      6),

    # Data
    ("share your data",          "data_risk",           6),
    ("third party access",       "data_risk",           6),
    ("data retention",           "data_risk",           5),

    # Liability (medium)
    ("limited liability",        "liability",           5),
    ("cap on liability",         "liability",           5),
    ("exclusion of damages",     "liability",           6),
]

LOW_RISK_PATTERNS: List[Tuple[str, str, int]] = [
    ("mutual agreement",         "balanced_terms",      2),
    ("both parties",             "balanced_terms",      1),
    ("30 days notice",           "fair_process",        2),
    ("written notice",           "fair_process",        2),
    ("reasonable notice",        "fair_process",        2),
    ("either party",             "balanced_terms",      1),
    ("mutual consent",           "balanced_terms",      1),
]

# Weight per risk category for composite score
RISK_WEIGHT: Dict[str, float] = {
    "rights_waiver":    1.5,
    "one_sided_control": 1.4,
    "financial_risk":   1.3,
    "irrevocable_terms": 1.3,
    "non_negotiable":   1.2,
    "due_process":      1.2,
    "ip_risk":          1.3,
    "non_compete":      1.4,
    "vague_obligation": 0.9,
    "limited_rights":   0.8,
    "conditional_risk": 0.9,
    "data_risk":        1.0,
    "liability":        1.0,
    "balanced_terms":   0.5,
    "fair_process":     0.5,
}


# ══════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def assign_risk_levels(clauses: List[dict]) -> List[dict]:
    """
    Assigns risk level, risk reason, risk indicators,
    and numeric risk score to each clause.

    Also computes an overall contract risk score and
    attaches it to the clause list as a whole.

    Returns:
        Updated clause list with risk metadata
    """
    logger.info(f"Starting risk analysis on {len(clauses)} clauses")

    for clause in clauses:
        try:
            risk_level, risk_reason, indicators, score = _evaluate_clause_risk(
                clause["original_text"]
            )
            clause["risk_level"]      = risk_level
            clause["risk_reason"]     = risk_reason
            clause["risk_indicators"] = indicators
            clause["risk_score"]      = score

        except Exception as e:
            logger.error(
                f"Risk evaluation failed for clause "
                f"{clause.get('clause_id', 'unknown')}: {e}"
            )
            clause["risk_level"]      = "Low"
            clause["risk_reason"]     = "Risk evaluation error — defaulted to Low"
            clause["risk_indicators"] = []
            clause["risk_score"]      = 0

    # Log distribution
    dist = _get_risk_distribution(clauses)
    logger.info(
        f"Risk analysis complete | "
        f"High={dist['High']}, Medium={dist['Medium']}, Low={dist['Low']}"
    )

    return clauses


# ══════════════════════════════════════════════════════════════════
# CORE RISK EVALUATOR
# ══════════════════════════════════════════════════════════════════

def _evaluate_clause_risk(
    text: str
) -> Tuple[str, str, List[dict], int]:
    """
    Evaluates a single clause for risk.

    Algorithm:
        1. Match against HIGH_RISK_PATTERNS
        2. Match against MEDIUM_RISK_PATTERNS
        3. Check for LOW_RISK_PATTERNS (reduces raw score)
        4. Compute weighted raw score
        5. Convert to risk level + normalized 0-100 score

    Returns:
        (risk_level, risk_reason, risk_indicators, risk_score)
    """
    text_lower = text.lower()
    indicators: List[dict] = []
    raw_score: float = 0.0

    # ── Check HIGH risk patterns ──────────────────────────────
    for pattern, category, severity in HIGH_RISK_PATTERNS:
        if pattern in text_lower:
            weight = RISK_WEIGHT.get(category, 1.0)
            raw_score += severity * weight
            indicators.append({
                "pattern_matched": pattern,
                "risk_category":   category,
                "severity_score":  severity
            })

    # ── Check MEDIUM risk patterns ────────────────────────────
    for pattern, category, severity in MEDIUM_RISK_PATTERNS:
        if pattern in text_lower:
            weight = RISK_WEIGHT.get(category, 1.0)
            raw_score += severity * weight * 0.5   # Medium half weight
            indicators.append({
                "pattern_matched": pattern,
                "risk_category":   category,
                "severity_score":  severity
            })

    # ── Check LOW / balancing patterns ───────────────────────
    for pattern, category, severity in LOW_RISK_PATTERNS:
        if pattern in text_lower:
            weight = RISK_WEIGHT.get(category, 0.5)
            raw_score -= severity * weight           # Reduce score

    raw_score = max(0.0, raw_score)

    # ── Classify risk level ───────────────────────────────────
    # High: raw_score >= 12, or any single severity 9-10 indicator
    # Medium: raw_score >= 5
    # Low: else

    has_critical = any(ind["severity_score"] >= 9 for ind in indicators)

    if raw_score >= 12 or has_critical:
        risk_level = "High"
    elif raw_score >= 5:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # ── Generate normalized 0-100 score ──────────────────────
    # Cap: 30.0 raw_score maps to 100
    normalized_score = min(100, int((raw_score / 30.0) * 100))

    # ── Generate human-readable reason ───────────────────────
    risk_reason = _generate_risk_reason(risk_level, indicators, raw_score)

    return risk_level, risk_reason, indicators, normalized_score


# ══════════════════════════════════════════════════════════════════
# RISK REASON GENERATOR
# ══════════════════════════════════════════════════════════════════

def _generate_risk_reason(
    risk_level: str,
    indicators: List[dict],
    raw_score: float
) -> str:
    """
    Generates a human-readable explanation for the assigned risk level.
    """
    if not indicators:
        return (
            "No significant risk patterns detected. "
            "The language appears balanced and standard."
        )

    # Get top 3 most severe indicators
    top = sorted(indicators, key=lambda x: x["severity_score"], reverse=True)[:3]
    pattern_list = ", ".join([f"'{i['pattern_matched']}'" for i in top])

    category_set = list({i["risk_category"] for i in top})
    category_str = ", ".join(
        c.replace("_", " ").title() for c in category_set
    )

    reasons = {
        "High": (
            f"This clause contains highly concerning language: {pattern_list}. "
            f"Risk categories identified: {category_str}. "
            f"These terms significantly favor one party and may expose you to "
            f"legal or financial harm. Strongly recommend reviewing with a lawyer."
        ),
        "Medium": (
            f"This clause contains moderately risky language: {pattern_list}. "
            f"Risk categories: {category_str}. "
            f"The terms may be vague or conditionally unfavorable. "
            f"Consider requesting clearer, more balanced language."
        ),
        "Low": (
            f"Minor concerns detected: {pattern_list}. "
            f"Overall language appears reasonable. "
            f"Review in context to ensure terms align with your expectations."
        )
    }

    return reasons.get(risk_level, "Risk assessment not available.")


# ══════════════════════════════════════════════════════════════════
# OVERALL CONTRACT RISK SCORE
# ══════════════════════════════════════════════════════════════════

def compute_contract_risk_score(clauses: List[dict]) -> int:
    """
    Computes a single composite risk score for the entire contract (0-100).

    Formula:
        - High risk clauses contribute 3× their score
        - Medium risk clauses contribute 1.5× their score
        - Low risk clauses contribute 0.3× their score
        - Final score normalized by total clause count
    """
    if not clauses:
        return 0

    weighted_total = 0.0

    for clause in clauses:
        score = clause.get("risk_score", 0) or 0
        level = clause.get("risk_level", "Low")

        if level == "High":
            weighted_total += score * 3.0
        elif level == "Medium":
            weighted_total += score * 1.5
        else:
            weighted_total += score * 0.3

    # Normalize: assume max possible score is 300 per clause
    max_possible  = len(clauses) * 300.0
    contract_score = min(100, int((weighted_total / max_possible) * 100))

    logger.info(f"Contract risk score computed: {contract_score}/100")

    return contract_score


def _get_risk_distribution(clauses: List[dict]) -> Dict[str, int]:
    dist = {"High": 0, "Medium": 0, "Low": 0}
    for clause in clauses:
        level = clause.get("risk_level", "Low")
        dist[level] = dist.get(level, 0) + 1
    return dist


def get_top_risky_clause_type(clauses: List[dict]) -> Optional[str]:
    """Returns the clause type with the highest concentration of High risk clauses."""
    type_risk: Dict[str, int] = {}
    for clause in clauses:
        if clause.get("risk_level") == "High":
            ct = clause.get("clause_type", "Other")
            type_risk[ct] = type_risk.get(ct, 0) + 1

    return max(type_risk, key=type_risk.get) if type_risk else None