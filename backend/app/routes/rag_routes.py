from datetime import UTC, datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.rag_pipeline import (
    is_vector_store_ready,
    load_vector_store,
    retrieve_context,
)
from app.config.database import get_database
from app.middleware.auth_middleware import require_legal_user
from app.services.rag_service import query_rag


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


def _simple_answer(query: str, docs: list[str]) -> str:
    if not docs:
        return "No relevant legal context was found for this question."
    top = docs[:2]
    joined = " ".join(top)
    return f"Query: {query}\n\nRelevant legal context:\n{joined[:700]}"


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    summary="Run a general RAG query",
)
async def rag_query(
    payload: dict,
    current_user: dict = Depends(require_legal_user),
):
    query = (payload or {}).get("query")
    contract_id = (payload or {}).get("contract_id")
    if not query:
        raise HTTPException(status_code=400, detail="Field 'query' is required.")

    results = query_rag(query, top_k=5)
    response = {
        "query": query,
        "contract_id": contract_id,
        "answer": _simple_answer(query, results.get("docs", [])),
        "contexts": results.get("docs", []),
        "scores": results.get("scores", []),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return response


@router.get(
    "/contract/{contract_id}/insights",
    status_code=status.HTTP_200_OK,
    summary="Get RAG insights for a contract",
)
async def contract_insights(
    contract_id: str,
    current_user: dict = Depends(require_legal_user),
):
    db = get_database()
    user_id = current_user["sub"]

    try:
        oid = ObjectId(contract_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid contract ID format.")

    contract = await db["contracts"].find_one({"_id": oid, "user_id": user_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")

    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found. Run analysis first.")

    insights = []
    for clause in (analysis.get("clauses") or []):
        rag_context = clause.get("rag_context") or {}
        if rag_context.get("context_summary"):
            insights.append({
                "clause_id": clause.get("clause_id"),
                "clause_type": clause.get("clause_type"),
                "risk_level": clause.get("risk_level"),
                "insight": rag_context.get("context_summary"),
            })

    return {
        "contract_id": contract_id,
        "total_insights": len(insights),
        "insights": insights,
    }


@router.post(
    "/contract/{contract_id}/ask",
    status_code=status.HTTP_200_OK,
    summary="Ask a contract-specific question using RAG",
)
async def ask_contract(
    contract_id: str,
    question: str = Query(..., min_length=3),
    current_user: dict = Depends(require_legal_user),
):
    db = get_database()
    user_id = current_user["sub"]

    try:
        oid = ObjectId(contract_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid contract ID format.")

    contract = await db["contracts"].find_one({"_id": oid, "user_id": user_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")

    base_query = f"{question} | Contract title: {contract.get('title') or contract.get('filename')}"
    results = retrieve_context(base_query, top_k=5, min_similarity=0.2)
    return {
        "contract_id": contract_id,
        "question": question,
        "answer": _simple_answer(question, results.get("docs", [])),
        "contexts": results.get("docs", []),
        "scores": results.get("scores", []),
    }


@router.get(
    "/similar-clauses",
    status_code=status.HTTP_200_OK,
    summary="Find similar legal clauses from knowledge base",
)
async def similar_clauses(
    clause_text: str = Query(..., min_length=10),
    clause_type: Optional[str] = Query(None),
    limit: int = Query(3, ge=1, le=10),
    current_user: dict = Depends(require_legal_user),
):
    query = f"{clause_type or 'General'} clause | {clause_text}"
    results = retrieve_context(query, top_k=limit, min_similarity=0.2)
    return {
        "query": query,
        "similar_clauses": results.get("docs", []),
        "scores": results.get("scores", []),
    }


@router.post(
    "/explain",
    status_code=status.HTTP_200_OK,
    summary="Explain a legal concept using RAG context",
)
async def explain_concept(
    concept: str = Query(..., min_length=2),
    context: Optional[str] = Query(None),
    current_user: dict = Depends(require_legal_user),
):
    query = f"Explain legal concept: {concept}. Context: {context or 'general contract law'}"
    results = retrieve_context(query, top_k=4, min_similarity=0.2)
    return {
        "concept": concept,
        "explanation": _simple_answer(concept, results.get("docs", [])),
        "contexts": results.get("docs", []),
        "scores": results.get("scores", []),
    }


@router.get(
    "/knowledge-base/stats",
    status_code=status.HTTP_200_OK,
    summary="Get RAG knowledge base stats",
)
async def knowledge_base_stats(
    current_user: dict = Depends(require_legal_user),
):
    if not is_vector_store_ready():
        return {
            "ready": False,
            "documents": 0,
            "vectors": 0,
        }

    try:
        index, docs = load_vector_store()
        return {
            "ready": True,
            "documents": len(docs),
            "vectors": int(index.ntotal),
        }
    except Exception:
        return {
            "ready": False,
            "documents": 0,
            "vectors": 0,
        }
