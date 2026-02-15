# app/services/rag_service.py

from typing import List, Optional
from datetime import datetime
from app.ai.rag_pipeline import retrieve_context, is_vector_store_ready
import logging
import asyncio

logger = logging.getLogger("legalyze.rag")

# Only enrich Medium/High risk clauses (Low don't need RAG context)
ENRICH_RISK_LEVELS = {"Medium", "High"}

# Number of similar documents to retrieve per clause
TOP_K = 3


# ══════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════

async def enrich_with_rag(clauses: List[dict]) -> List[dict]:
    """
    Enriches Medium/High risk clauses with relevant context
    retrieved from the legal knowledge vector store (FAISS).

    Process per clause:
        1. Encode clause text to vector embedding
        2. Query FAISS for top-K similar legal document chunks
        3. Build RAGContext object with docs, scores, and summary
        4. Attach to clause dict

    Returns:
        Updated clause list with 'rag_context' populated
    """
    if not is_vector_store_ready():
        logger.warning(
            "Vector store not loaded — skipping RAG enrichment. "
            "Run build_vector_store() to initialize."
        )
        return clauses

    eligible = [
        c for c in clauses
        if c.get("risk_level") in ENRICH_RISK_LEVELS
    ]
    logger.info(
        f"RAG enrichment starting | "
        f"eligible={len(eligible)}/{len(clauses)} clauses"
    )

    # Run enrichment concurrently for performance
    tasks = [_enrich_single_clause(clause) for clause in clauses]
    enriched = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(enriched):
        if isinstance(result, Exception):
            logger.error(f"RAG enrichment error on clause {i}: {result}")
        else:
            clauses[i] = result

    logger.info("RAG enrichment complete")
    return clauses


# ══════════════════════════════════════════════════════════════════
# SINGLE CLAUSE ENRICHMENT
# ══════════════════════════════════════════════════════════════════

async def _enrich_single_clause(clause: dict) -> dict:
    """
    Asynchronously enriches a single clause with RAG context.
    Non-eligible clauses are returned unchanged.
    """
    risk_level = clause.get("risk_level", "Low")

    if risk_level not in ENRICH_RISK_LEVELS:
        clause["rag_context"] = None
        return clause

    clause_id   = clause.get("clause_id", "unknown")
    clause_type = clause.get("clause_type", "General")
    query_text  = _build_rag_query(clause)

    try:
        # Retrieve context from vector store
        results = retrieve_context(query_text, top_k=TOP_K)

        if not results["docs"]:
            logger.debug(f"No RAG context found for clause {clause_id}")
            clause["rag_context"] = None
            return clause

        # Build context summary
        context_summary = _build_context_summary(
            clause_type=clause_type,
            docs=results["docs"],
            scores=results["scores"]
        )

        clause["rag_context"] = {
            "retrieved_docs":      results["docs"],
            "similarity_scores":   results["scores"],
            "context_summary":     context_summary,
            "retrieval_timestamp": datetime.utcnow().isoformat()
        }

        logger.debug(
            f"RAG enriched clause {clause_id} | "
            f"docs={len(results['docs'])}, "
            f"top_score={results['scores'][0]:.3f}"
            if results["scores"] else ""
        )

    except Exception as e:
        logger.error(f"RAG enrichment failed for clause {clause_id}: {e}")
        clause["rag_context"] = None

    return clause


# ══════════════════════════════════════════════════════════════════
# RAG QUERY BUILDER
# ══════════════════════════════════════════════════════════════════

def _build_rag_query(clause: dict) -> str:
    """
    Constructs a focused retrieval query combining:
    - Clause type (e.g., 'Confidentiality')
    - Risk reason (what's wrong)
    - First 200 chars of original text

    This gives the retriever better context than raw clause text alone.
    """
    parts = []

    clause_type = clause.get("clause_type", "")
    if clause_type:
        parts.append(f"Legal clause type: {clause_type}")

    risk_reason = clause.get("risk_reason", "")
    if risk_reason:
        # Use first sentence of risk reason
        first_sentence = risk_reason.split(".")[0]
        parts.append(f"Risk concern: {first_sentence}")

    original = clause.get("original_text", "")
    if original:
        parts.append(f"Clause text: {original[:200]}")

    return " | ".join(parts)


# ══════════════════════════════════════════════════════════════════
# CONTEXT SUMMARY BUILDER
# ══════════════════════════════════════════════════════════════════

def _build_context_summary(
    clause_type: str,
    docs: List[str],
    scores: List[float]
) -> str:
    """
    Builds a human-readable summary from retrieved RAG documents.
    Used to provide context to the suggestion generator.
    """
    if not docs:
        return ""

    # Filter only high-confidence retrievals (similarity > 0.5)
    relevant = [
        doc for doc, score in zip(docs, scores)
        if score > 0.5
    ]

    if not relevant:
        relevant = docs[:1]   # Use at least the best match

    # Truncate each doc to 200 chars
    doc_summaries = [doc[:200].strip() for doc in relevant]
    combined      = " | ".join(doc_summaries)

    summary = (
        f"Based on similar {clause_type} clauses in legal documents: "
        f"{combined}"
    )

    return summary[:800]   # Cap summary length


# ══════════════════════════════════════════════════════════════════
# SINGLE QUERY (for API use)
# ══════════════════════════════════════════════════════════════════

def query_rag(query: str, top_k: int = 5) -> dict:
    """
    Performs a direct RAG query.
    Used by external callers e.g. regeneration endpoint.

    Returns:
        { docs: List[str], scores: List[float] }
    """
    if not is_vector_store_ready():
        return {"docs": [], "scores": []}

    return retrieve_context(query, top_k=top_k)