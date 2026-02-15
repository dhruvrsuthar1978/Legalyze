# app/routes/analysis_routes.py

from fastapi import (
    APIRouter, HTTPException,
    Depends, status, Query,
    BackgroundTasks
)
from typing import Optional
from app.controllers.analysis_controller import (
    run_full_analysis,
    get_analysis_result,
    get_clauses_by_risk,
    get_simplified_clauses,
    get_analysis_summary,
    get_clause_by_id,
    reanalyze_contract,
    export_analysis_report
)
from app.models.clause_model import (
    AnalysisResponse,
    ClauseListResponse,
    SimplifiedClauseResponse,
    AnalysisSummaryResponse,
    SingleClauseResponse,
    ExportReportResponse
)
from app.middleware.auth_middleware import verify_token

router = APIRouter(
    prefix="/analysis",
    tags=["🔍 Contract Analysis"]
)


# ══════════════════════════════════════════════════════
# @route    POST /api/analysis/{contract_id}/run
# @desc     Trigger full AI analysis pipeline on a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/{contract_id}/run",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run complete AI analysis on a contract",
    description="""
    Triggers the full Legalyze AI analysis pipeline on the specified contract.
    
    **Analysis Pipeline Steps:**
    
    1. **Clause Extraction** — spaCy NLP identifies and segments clauses
       (Confidentiality, Payment, Termination, Liability, IP, etc.)
    
    2. **Risk Classification** — Each clause is assigned:
       - `Low` — Standard, balanced language
       - `Medium` — Potentially unfavorable terms
       - `High` — Dangerous, one-sided, or rights-waiving language
    
    3. **Plain-English Simplification** — BART Transformer converts
       complex legal sentences into simple, readable explanations
    
    4. **RAG Enrichment** — Retrieval-Augmented Generation pulls
       relevant context from the legal knowledge vector store
    
    5. **AI Suggestions** — Fair alternative clauses are generated
       for all Medium/High risk clauses
    
    **Run Mode:**
    - `sync` — Wait for results (suitable for small contracts)
    - `async` — Run in background, poll `/api/analysis/{id}` for status
    """
)
async def analyze_contract(
    contract_id: str,
    background_tasks: BackgroundTasks,
    mode: str = Query(
        "sync",
        description="Execution mode: sync (wait) | async (background)"
    ),
    current_user: dict = Depends(verify_token)
):
    if mode not in ["sync", "async"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode must be 'sync' or 'async'."
        )
    return await run_full_analysis(
        contract_id=contract_id,
        current_user=current_user,
        background_tasks=background_tasks,
        mode=mode
    )


# ══════════════════════════════════════════════════════
# @route    POST /api/analysis/{contract_id}/reanalyze
# @desc     Re-run analysis (overwrites previous results)
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/{contract_id}/reanalyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-run AI analysis on a previously analyzed contract",
    description="""
    Clears the existing analysis results and runs a fresh analysis.
    
    Use this when:
    - The AI models have been updated
    - The user wants a fresh perspective
    - Previous analysis failed or was incomplete
    
    ⚠️ **All previous clause results, risk labels, and suggestions
    will be permanently overwritten.**
    """
)
async def reanalyze(
    contract_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token)
):
    return await reanalyze_contract(contract_id, current_user, background_tasks)


# ══════════════════════════════════════════════════════
# @route    GET /api/analysis/{contract_id}
# @desc     Get full analysis result of a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full analysis result of a contract",
    description="""
    Retrieves the complete stored analysis result for a contract.
    
    **Returns:**
    - All extracted clauses with type, original text, simplified text
    - Risk level and risk reasoning for each clause
    - RAG-enriched legal context
    - AI-generated suggestions
    - Clause counts by risk level
    - Analysis timestamp
    
    Returns `404` if analysis has not been run yet.
    Use `POST /run` to trigger analysis first.
    """
)
async def get_analysis(
    contract_id: str,
    current_user: dict = Depends(verify_token)
):
    return await get_analysis_result(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/analysis/{contract_id}/summary
# @desc     Get a quick high-level summary of analysis
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/summary",
    response_model=AnalysisSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get high-level analysis summary",
    description="""
    Returns a quick executive-level summary of the contract analysis.
    
    **Includes:**
    - Total clause count + breakdown by risk level
    - Most risky clause type
    - Overall contract risk score (0–100)
    - Top 3 recommendations
    - Analysis completion timestamp
    
    Faster than fetching the full analysis. Ideal for dashboard cards.
    """
)
async def get_summary(
    contract_id: str,
    current_user: dict = Depends(verify_token)
):
    return await get_analysis_summary(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/analysis/{contract_id}/risk
# @desc     Get clauses filtered by risk level
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/risk",
    response_model=ClauseListResponse,
    status_code=status.HTTP_200_OK,
    summary="Filter contract clauses by risk level",
    description="""
    Returns only the clauses matching the specified **risk level**.
    
    **Risk Levels:**
    - `High` — Dangerous or one-sided terms (e.g., waives all rights)
    - `Medium` — Potentially unfavorable (e.g., vague obligations)
    - `Low` — Balanced and standard language
    
    **Query Params:**
    - `level` — Required: `Low`, `Medium`, or `High`
    - `clause_type` — Optional: filter by type (e.g., `Confidentiality`)
    
    Useful for prioritizing legal review efforts.
    """
)
async def get_risky_clauses(
    contract_id: str,
    level: str = Query(
        ...,
        description="Risk level to filter: Low | Medium | High"
    ),
    clause_type: Optional[str] = Query(
        None,
        description="Optional: filter by clause type e.g. Confidentiality, Payment"
    ),
    current_user: dict = Depends(verify_token)
):
    if level not in ["Low", "Medium", "High"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid risk level.",
                "allowed": ["Low", "Medium", "High"],
                "received": level
            }
        )
    return await get_clauses_by_risk(
        contract_id=contract_id,
        level=level,
        clause_type=clause_type,
        current_user=current_user
    )


# ══════════════════════════════════════════════════════
# @route    GET /api/analysis/{contract_id}/simplified
# @desc     Get plain-English version of all clauses
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/simplified",
    response_model=SimplifiedClauseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all clauses in plain English",
    description="""
    Returns all contract clauses converted to **simple, readable English**
    using Facebook's BART Transformer model.
    
    **Ideal for:**
    - Non-lawyers trying to understand contract terms
    - Quick comprehension of complex clauses
    - Side-by-side comparison (original vs simplified)
    
    **Query Params:**
    - `risk_only` — If `true`, returns only simplified High/Medium risk clauses
    """
)
async def simplified_clauses(
    contract_id: str,
    risk_only: bool = Query(
        False,
        description="If true, return only High and Medium risk clauses"
    ),
    current_user: dict = Depends(verify_token)
):
    return await get_simplified_clauses(
        contract_id=contract_id,
        risk_only=risk_only,
        current_user=current_user
    )


# ══════════════════════════════════════════════════════
# @route    GET /api/analysis/{contract_id}/clauses/{clause_id}
# @desc     Get a specific clause by its ID
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/clauses/{clause_id}",
    response_model=SingleClauseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single specific clause by ID",
    description="""
    Retrieves the full details of a single clause by its **clause_id**
    within a contract's analysis result.
    
    **Returns:**
    - Clause type and original text
    - Risk level and reason
    - Simplified explanation
    - RAG legal context
    - AI suggestion and its current status
    """
)
async def get_clause(
    contract_id: str,
    clause_id: str,
    current_user: dict = Depends(verify_token)
):
    return await get_clause_by_id(contract_id, clause_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/analysis/{contract_id}/export
# @desc     Export full analysis as PDF or JSON report
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/export",
    response_model=ExportReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export full analysis report as PDF or JSON",
    description="""
    Generates and exports the complete analysis report in the requested format.
    
    **Supported Formats:**
    - `pdf` — Professionally formatted PDF report with risk heatmap
    - `json` — Raw structured data for programmatic use
    
    **Report Contents:**
    - Contract overview and metadata
    - All extracted clauses with risk levels
    - Plain-English summaries
    - AI suggestions and recommendations
    - Digital signature status (if signed)
    
    Returns a **temporary download URL** (expires in 30 minutes).
    """
)
async def export_report(
    contract_id: str,
    format: str = Query(
        "pdf",
        description="Export format: pdf | json"
    ),
    current_user: dict = Depends(verify_token)
):
    if format not in ["pdf", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Export format must be 'pdf' or 'json'."
        )
    return await export_analysis_report(contract_id, format, current_user)