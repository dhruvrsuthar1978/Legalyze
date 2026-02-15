# app/ai/prompt_templates.py

from typing import List, Optional


# ══════════════════════════════════════════════════════════════════
# SUGGESTION GENERATION PROMPT
# ══════════════════════════════════════════════════════════════════

def build_suggestion_prompt(
    original_text: str,
    clause_type: str,
    risk_level: str,
    risk_reason: str,
    risk_categories: List[str],
    rag_context: Optional[str] = None
) -> str:
    """
    Builds a prompt for generating fair clause alternatives.
    
    Returns:
        Formatted prompt string
    """
    context_section = ""
    if rag_context:
        context_section = f"""
LEGAL CONTEXT:
{rag_context}
"""
    
    categories_str = ", ".join(risk_categories) if risk_categories else "general unfairness"
    
    prompt = f"""You are an expert legal contract advisor. Your task is to rewrite an unfair contract clause into a balanced, fair alternative that protects both parties equally.

CLAUSE TYPE: {clause_type}
RISK LEVEL: {risk_level}
RISK CATEGORIES: {categories_str}
{context_section}
PROBLEMATIC CLAUSE:
"{original_text}"

REASON FOR CONCERN:
{risk_reason}

INSTRUCTIONS:
1. Rewrite this clause to be fair and balanced for both parties
2. Remove one-sided language and unreasonable restrictions
3. Add mutual obligations where appropriate
4. Ensure clarity and specificity
5. Maintain the core purpose while protecting both parties' rights
6. Keep the rewrite concise (similar length to original)

BALANCED ALTERNATIVE CLAUSE:"""
    
    return prompt


# ══════════════════════════════════════════════════════════════════
# REGENERATION PROMPT (with variation)
# ══════════════════════════════════════════════════════════════════

def build_regeneration_prompt(
    original_text: str,
    clause_type: str,
    risk_reason: str,
    rag_context: Optional[str] = None,
    previous_suggestion: Optional[str] = None
) -> str:
    """
    Builds a prompt for regenerating a different suggestion.
    """
    previous_section = ""
    if previous_suggestion:
        previous_section = f"""
PREVIOUS SUGGESTION (generate a DIFFERENT alternative):
"{previous_suggestion}"
"""
    
    context_section = ""
    if rag_context:
        context_section = f"""
LEGAL CONTEXT:
{rag_context}
"""
    
    prompt = f"""You are an expert legal contract advisor. Generate a DIFFERENT fair alternative to this problematic clause.

CLAUSE TYPE: {clause_type}
{context_section}
ORIGINAL CLAUSE:
"{original_text}"

ISSUE:
{risk_reason}
{previous_section}
INSTRUCTIONS:
1. Create a NEW, DIFFERENT balanced alternative (not similar to previous)
2. Explore a different approach or angle
3. Ensure fairness to both parties
4. Be specific and actionable
5. Maintain professional legal language

NEW BALANCED ALTERNATIVE:"""
    
    return prompt


# ══════════════════════════════════════════════════════════════════
# SIMPLIFICATION PROMPT (for complex clauses)
# ══════════════════════════════════════════════════════════════════

def build_simplification_prompt(text: str) -> str:
    """
    Builds a prompt for simplifying legal text to plain English.
    """
    prompt = f"""Convert the following legal text into simple, plain English that anyone can understand. Preserve the meaning but use everyday language.

LEGAL TEXT:
"{text}"

PLAIN ENGLISH VERSION:"""
    
    return prompt


# ══════════════════════════════════════════════════════════════════
# CONTRACT SUMMARY PROMPT
# ══════════════════════════════════════════════════════════════════

def build_summary_prompt(
    contract_text: str,
    max_length: int = 300
) -> str:
    """
    Builds a prompt for generating an executive summary of a contract.
    """
    prompt = f"""Summarize the following legal contract in plain English. Focus on the key points, parties involved, main obligations, and critical terms. Keep it under {max_length} words.

CONTRACT:
{contract_text[:5000]}  # First 5000 chars

EXECUTIVE SUMMARY:"""
    
    return prompt


# ══════════════════════════════════════════════════════════════════
# RISK EXPLANATION PROMPT
# ══════════════════════════════════════════════════════════════════

def build_risk_explanation_prompt(
    clause_text: str,
    risk_level: str,
    risk_patterns: List[str]
) -> str:
    """
    Builds a prompt for explaining why a clause is risky.
    """
    patterns_str = ", ".join([f"'{p}'" for p in risk_patterns])
    
    prompt = f"""Explain to a non-lawyer why this contract clause is problematic and what risks it poses.

CLAUSE:
"{clause_text}"

RISK LEVEL: {risk_level}
DETECTED PATTERNS: {patterns_str}

Provide a clear, simple explanation of:
1. What makes this clause unfair
2. What could go wrong
3. Why this matters

EXPLANATION:"""
    
    return prompt