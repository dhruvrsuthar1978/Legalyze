# app/services/suggestion_service.py

from typing import List, Dict, Optional
from app.ai.transformer_model import generate_text
from app.ai.prompt_templates import (
    build_suggestion_prompt,
    build_regeneration_prompt
)
import logging

logger = logging.getLogger("legalyze.suggestion")


# ══════════════════════════════════════════════════════════════════
# FAIR ALTERNATIVE TEMPLATES (fallback if LLM unavailable)
# Keyed by: (clause_type, risk_category)
# ══════════════════════════════════════════════════════════════════

FALLBACK_TEMPLATES: Dict[str, str] = {
    "rights_waiver": (
        "Both parties shall retain all rights granted under applicable law. "
        "Any waiver of rights must be made explicitly in writing and agreed "
        "upon by both parties."
    ),
    "one_sided_control": (
        "Decisions affecting both parties shall be made by mutual written consent. "
        "Neither party may unilaterally modify, terminate, or override the terms "
        "of this agreement."
    ),
    "financial_risk": (
        "Refund eligibility and payment terms shall be fair and clearly defined. "
        "Any penalty or charge must be proportionate and agreed upon by both parties "
        "prior to execution."
    ),
    "irrevocable_terms": (
        "Either party may review and renegotiate the terms of this clause "
        "with 30 days written notice. No term shall be irrevocable without "
        "explicit consent from both parties."
    ),
    "non_negotiable": (
        "Both parties agree that all terms in this agreement are subject to good "
        "faith negotiation. Either party may propose amendments with reasonable notice."
    ),
    "due_process": (
        "Either party may terminate this agreement with a minimum of 30 days "
        "written notice. Immediate termination is only permissible in cases of "
        "material breach that remains uncured for 15 days after written notice."
    ),
    "ip_risk": (
        "Intellectual property created by each party independently shall remain "
        "the property of that party. Jointly developed works shall be co-owned "
        "with equal rights to use, subject to mutual written agreement."
    ),
    "non_compete": (
        "Any non-compete restriction shall be limited to a specific geographic area, "
        "a defined industry sector, and a reasonable time period not exceeding "
        "12 months from the termination of this agreement."
    ),
    "vague_obligation": (
        "The obligations of each party shall be clearly defined with measurable "
        "deliverables, timelines, and acceptance criteria agreed upon in writing."
    ),
    "data_risk": (
        "Personal data shall be processed only for the purposes described in this "
        "agreement, in compliance with applicable data protection laws (GDPR/CCPA). "
        "Data shall not be shared with third parties without explicit written consent."
    ),
    "liability": (
        "Each party's total liability shall be limited to the total fees paid or "
        "payable under this agreement in the 12-month period prior to the event "
        "giving rise to the claim."
    ),
}


# ══════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def generate_suggestions(clauses: List[dict]) -> List[dict]:
    """
    Generates AI-based fair clause alternatives for all Medium/High
    risk clauses. Low risk clauses receive a generic affirmation.

    Strategy:
        1. Skip Low risk clauses (no suggestion needed)
        2. Try AI-based suggestion via transformer model
        3. Fall back to template-based suggestion if AI fails
        4. Attach suggestion to clause dict

    Returns:
        Updated clause list with 'suggestion' field populated
    """
    medium_high = [
        c for c in clauses
        if c.get("risk_level") in ["Medium", "High"]
    ]
    logger.info(
        f"Generating suggestions for "
        f"{len(medium_high)}/{len(clauses)} clauses"
    )

    for clause in clauses:
        risk_level = clause.get("risk_level", "Low")

        if risk_level == "Low":
            clause["suggestion"] = (
                "This clause appears balanced. No changes are recommended. "
                "However, ensure the terms align with your specific legal context."
            )
            clause["suggestion_status"] = "pending"
            continue

        try:
            suggestion = _generate_ai_suggestion(clause)
            clause["suggestion"] = suggestion
            logger.debug(
                f"AI suggestion generated for clause "
                f"{clause.get('clause_id', 'unknown')}"
            )

        except Exception as e:
            logger.warning(
                f"AI suggestion failed for clause "
                f"{clause.get('clause_id', 'unknown')}: {e}. "
                f"Using fallback template."
            )
            clause["suggestion"] = _get_fallback_suggestion(clause)

        clause["suggestion_status"] = "pending"

    return clauses


def regenerate_suggestion_for_clause(clause: dict) -> str:
    """
    Generates a fresh AI suggestion for a single clause.
    Uses a regeneration-specific prompt for diversity.

    Returns:
        New suggestion text string
    """
    logger.info(
        f"Regenerating suggestion for clause "
        f"{clause.get('clause_id', 'unknown')}"
    )

    try:
        prompt = build_regeneration_prompt(
            original_text=clause["original_text"],
            clause_type=clause.get("clause_type", "General"),
            risk_reason=clause.get("risk_reason", ""),
            rag_context=clause.get("rag_context", {}).get("context_summary", "")
            if clause.get("rag_context") else "",
            previous_suggestion=clause.get("suggestion", "")
        )
        return generate_text(prompt, max_tokens=300)

    except Exception as e:
        logger.error(f"Regeneration failed: {e}")
        return _get_fallback_suggestion(clause)


# ══════════════════════════════════════════════════════════════════
# AI SUGGESTION GENERATOR
# ══════════════════════════════════════════════════════════════════

def _generate_ai_suggestion(clause: dict) -> str:
    """
    Builds a structured prompt and calls the LLM transformer
    to generate a fair, balanced alternative clause.
    """
    rag_ctx = ""
    if clause.get("rag_context") and clause["rag_context"].get("context_summary"):
        rag_ctx = clause["rag_context"]["context_summary"]

    top_indicators = sorted(
        clause.get("risk_indicators", []),
        key=lambda x: x.get("severity_score", 0),
        reverse=True
    )[:2]

    risk_categories = [i.get("risk_category", "") for i in top_indicators]

    prompt = build_suggestion_prompt(
        original_text=clause["original_text"],
        clause_type=clause.get("clause_type", "General"),
        risk_level=clause.get("risk_level", "Medium"),
        risk_reason=clause.get("risk_reason", ""),
        risk_categories=risk_categories,
        rag_context=rag_ctx
    )

    return generate_text(prompt, max_tokens=300)


# ══════════════════════════════════════════════════════════════════
# FALLBACK TEMPLATE SELECTOR
# ══════════════════════════════════════════════════════════════════

def _get_fallback_suggestion(clause: dict) -> str:
    """
    Returns the most relevant fallback template based on
    the clause's top risk category.
    """
    indicators = clause.get("risk_indicators", [])

    if indicators:
        top_category = sorted(
            indicators,
            key=lambda x: x.get("severity_score", 0),
            reverse=True
        )[0].get("risk_category", "")

        if top_category in FALLBACK_TEMPLATES:
            return (
                f"[Suggested Alternative — {clause.get('clause_type', 'Clause')}] "
                f"{FALLBACK_TEMPLATES[top_category]}"
            )

    # Generic fallback
    return (
        f"[Suggested Alternative] "
        f"This clause should be reviewed by a qualified legal professional. "
        f"Consider negotiating more balanced terms that protect the rights "
        f"and obligations of both parties equally."
    )


# ══════════════════════════════════════════════════════════════════
# SUGGESTION STATISTICS
# ══════════════════════════════════════════════════════════════════

def compute_suggestion_stats(clauses: List[dict]) -> dict:
    """
    Returns a statistics summary of suggestion status across all clauses.
    """
    total = len(clauses)
    by_status: Dict[str, int] = {
        "pending": 0, "accepted": 0, "rejected": 0, "edited": 0
    }
    by_clause_type: Dict[str, int] = {}
    by_risk_level: Dict[str, int] = {"High": 0, "Medium": 0, "Low": 0}

    for clause in clauses:
        status     = clause.get("suggestion_status", "pending")
        clause_type = clause.get("clause_type", "Other")
        risk_level  = clause.get("risk_level", "Low")

        by_status[status] = by_status.get(status, 0) + 1
        by_clause_type[clause_type] = by_clause_type.get(clause_type, 0) + 1
        by_risk_level[risk_level]   = by_risk_level.get(risk_level, 0) + 1

    decided = by_status["accepted"] + by_status["rejected"] + by_status["edited"]
    acceptance_rate = (
        round((by_status["accepted"] / decided) * 100, 2)
        if decided > 0 else 0.0
    )

    return {
        "total_suggestions": total,
        "by_status":         by_status,
        "by_clause_type":    by_clause_type,
        "by_risk_level":     by_risk_level,
        "acceptance_rate":   acceptance_rate
    }