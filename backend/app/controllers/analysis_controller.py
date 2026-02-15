# app/controllers/analysis_controller.py

from fastapi import HTTPException, status, BackgroundTasks
from app.config.database import get_database
from app.services.clause_service import (
    extract_and_classify_clauses,
    get_clause_type_distribution
)
from app.services.risk_service import (
    assign_risk_levels,
    compute_contract_risk_score,
    get_top_risky_clause_type
)
from app.services.simplifier_service import simplify_clauses
from app.services.rag_service import enrich_with_rag
from app.services.suggestion_service import generate_suggestions
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional
import logging
import asyncio

logger = logging.getLogger("legalyze.analysis")


# ══════════════════════════════════════════════════════════════════
# RUN FULL ANALYSIS
# ══════════════════════════════════════════════════════════════════

async def run_full_analysis(
    contract_id: str,
    current_user: dict,
    background_tasks: BackgroundTasks,
    mode: str = "sync"
) -> dict:
    """
    Executes the complete AI analysis pipeline on a contract.
    
    Pipeline:
    1. Extract & classify clauses (spaCy NLP)
    2. Assign risk levels (pattern matching)
    3. Simplify to plain English (BART)
    4. Enrich with RAG context (FAISS vector search)
    5. Generate AI suggestions (Transformer LLM)
    6. Compute overall contract risk score
    7. Store analysis in MongoDB
    
    Modes:
    - sync: Wait for completion, return results
    - async: Run in background, return immediately
    
    Returns:
        Full analysis response with all clauses
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Verify contract exists and belongs to user
    contract = await db["contracts"].find_one({
        "_id": ObjectId(contract_id),
        "user_id": user_id
    })
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or you don't have access to it."
        )
    
    # Check if already analyzed
    existing = await db["analyses"].find_one({"contract_id": contract_id})
    if existing:
        logger.warning(
            f"Analysis already exists for contract {contract_id}. "
            f"Use /reanalyze to run again."
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contract has already been analyzed. Use the reanalyze endpoint to run again."
        )
    
    if mode == "async":
        # Run in background
        background_tasks.add_task(
            _execute_analysis_pipeline,
            contract_id=contract_id,
            user_id=user_id,
            extracted_text=contract["extracted_text"]
        )
        
        # Update status immediately
        await db["contracts"].update_one(
            {"_id": ObjectId(contract_id)},
            {"$set": {"analysis_status": "processing"}}
        )
        
        return {
            "contract_id": contract_id,
            "status": "processing",
            "message": "Analysis started in background. Check status with GET /analysis/{contract_id}"
        }
    
    else:  # sync mode
        return await _execute_analysis_pipeline(
            contract_id=contract_id,
            user_id=user_id,
            extracted_text=contract["extracted_text"]
        )


async def _execute_analysis_pipeline(
    contract_id: str,
    user_id: str,
    extracted_text: str
) -> dict:
    """
    Internal function: Executes the full analysis pipeline.
    Can be called sync or async.
    """
    
    db = get_database()
    logger.info(f"Analysis pipeline started | contract_id={contract_id}")
    
    # Update status to processing
    await db["contracts"].update_one(
        {"_id": ObjectId(contract_id)},
        {"$set": {"analysis_status": "processing"}}
    )
    
    try:
        # ── Step 1: Extract & Classify Clauses ───────────────────
        logger.info(f"Step 1/6: Extracting clauses | {contract_id}")
        clauses = extract_and_classify_clauses(extracted_text)
        
        if not clauses:
            raise ValueError("No clauses could be extracted from the contract.")
        
        logger.info(f"Extracted {len(clauses)} clauses")
        
        # ── Step 2: Assign Risk Levels ───────────────────────────
        logger.info(f"Step 2/6: Assigning risk levels | {contract_id}")
        clauses = assign_risk_levels(clauses)
        
        # ── Step 3: Simplify to Plain English ────────────────────
        logger.info(f"Step 3/6: Simplifying clauses | {contract_id}")
        clauses = simplify_clauses(clauses)
        
        # ── Step 4: RAG Enrichment ───────────────────────────────
        logger.info(f"Step 4/6: RAG enrichment | {contract_id}")
        clauses = await enrich_with_rag(clauses)
        
        # ── Step 5: Generate AI Suggestions ──────────────────────
        logger.info(f"Step 5/6: Generating suggestions | {contract_id}")
        clauses = generate_suggestions(clauses)
        
        # ── Step 6: Compute Overall Risk Score ───────────────────
        logger.info(f"Step 6/6: Computing contract risk score | {contract_id}")
        overall_risk_score = compute_contract_risk_score(clauses)
        top_risky_type = get_top_risky_clause_type(clauses)
        
        # ── Build Analysis Document ──────────────────────────────
        analysis = {
            "contract_id": contract_id,
            "user_id": user_id,
            "clauses": clauses,
            "total_clauses": len(clauses),
            "high_risk_count": sum(1 for c in clauses if c.get("risk_level") == "High"),
            "medium_risk_count": sum(1 for c in clauses if c.get("risk_level") == "Medium"),
            "low_risk_count": sum(1 for c in clauses if c.get("risk_level") == "Low"),
            "overall_risk_score": overall_risk_score,
            "top_risky_clause_type": top_risky_type,
            "clauses_by_type": get_clause_type_distribution(clauses),
            "analysis_version": "1.0",
            "analyzed_at": datetime.utcnow()
        }
        
        # ── Store Analysis ───────────────────────────────────────
        await db["analyses"].insert_one(analysis)
        
        # ── Update Contract Summary ──────────────────────────────
        await db["contracts"].update_one(
            {"_id": ObjectId(contract_id)},
            {
                "$set": {
                    "analysis_status": "completed",
                    "analysis_summary": {
                        "total_clauses": analysis["total_clauses"],
                        "high_risk_count": analysis["high_risk_count"],
                        "medium_risk_count": analysis["medium_risk_count"],
                        "low_risk_count": analysis["low_risk_count"],
                        "overall_risk_score": overall_risk_score,
                        "analyzed_at": analysis["analyzed_at"]
                    }
                }
            }
        )
        
        logger.info(
            f"Analysis complete | "
            f"contract_id={contract_id}, "
            f"clauses={len(clauses)}, "
            f"risk_score={overall_risk_score}"
        )
        
        # Remove _id for response
        analysis["id"] = str(analysis.pop("_id"))
        
        return analysis
    
    except Exception as e:
        logger.error(f"Analysis pipeline failed | contract_id={contract_id}: {e}")
        
        # Update status to failed
        await db["contracts"].update_one(
            {"_id": ObjectId(contract_id)},
            {
                "$set": {
                    "analysis_status": "failed",
                    "analysis_error": str(e)
                }
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


# ══════════════════════════════════════════════════════════════════
# REANALYZE CONTRACT
# ══════════════════════════════════════════════════════════════════

async def reanalyze_contract(
    contract_id: str,
    current_user: dict,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Clears existing analysis and runs a fresh analysis.
    Useful when AI models are updated or user wants a second opinion.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    contract = await db["contracts"].find_one({
        "_id": ObjectId(contract_id),
        "user_id": user_id
    })
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    
    # Delete existing analysis
    await db["analyses"].delete_many({"contract_id": contract_id})
    
    logger.info(f"Reanalyzing contract | contract_id={contract_id}")
    
    # Run fresh analysis
    return await _execute_analysis_pipeline(
        contract_id=contract_id,
        user_id=user_id,
        extracted_text=contract["extracted_text"]
    )


# ══════════════════════════════════════════════════════════════════
# GET ANALYSIS RESULT
# ══════════════════════════════════════════════════════════════════

async def get_analysis_result(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Retrieves stored analysis result for a contract.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Verify contract ownership
    contract = await db["contracts"].find_one({
        "_id": ObjectId(contract_id),
        "user_id": user_id
    })
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    
    # Fetch analysis
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found. Please run analysis first using POST /analysis/{contract_id}/run"
        )
    
    analysis["id"] = str(analysis.pop("_id"))
    return analysis


# ══════════════════════════════════════════════════════════════════
# GET ANALYSIS SUMMARY
# ══════════════════════════════════════════════════════════════════

async def get_analysis_summary(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Returns a high-level executive summary of the analysis.
    Lighter than full analysis response.
    """
    
    db = get_database()
    analysis = await get_analysis_result(contract_id, current_user)
    
    # Build top recommendations
    high_risk = [
        c for c in analysis["clauses"]
        if c.get("risk_level") == "High"
    ]
    
    recommendations = []
    for clause in high_risk[:5]:  # Top 5 high risk
        recommendations.append(
            f"Review {clause['clause_type']} clause: {clause['risk_reason'][:100]}..."
        )
    
    return {
        "contract_id": contract_id,
        "total_clauses": analysis["total_clauses"],
        "high_risk_count": analysis["high_risk_count"],
        "medium_risk_count": analysis["medium_risk_count"],
        "low_risk_count": analysis["low_risk_count"],
        "overall_risk_score": analysis["overall_risk_score"],
        "top_risky_clause_type": analysis.get("top_risky_clause_type"),
        "top_recommendations": recommendations,
        "clauses_by_type": analysis.get("clauses_by_type", {}),
        "analyzed_at": analysis["analyzed_at"]
    }


# ══════════════════════════════════════════════════════════════════
# GET CLAUSES BY RISK LEVEL
# ══════════════════════════════════════════════════════════════════

async def get_clauses_by_risk(
    contract_id: str,
    level: str,
    clause_type: Optional[str],
    current_user: dict
) -> dict:
    """
    Filters clauses by risk level and optionally by clause type.
    """
    
    db = get_database()
    analysis = await get_analysis_result(contract_id, current_user)
    
    # Filter by risk level
    filtered = [
        c for c in analysis["clauses"]
        if c.get("risk_level") == level
    ]
    
    # Further filter by clause type if specified
    if clause_type:
        filtered = [
            c for c in filtered
            if c.get("clause_type") == clause_type
        ]
    
    return {
        "contract_id": contract_id,
        "risk_level": level,
        "clause_type_filter": clause_type,
        "count": len(filtered),
        "clauses": filtered
    }


# ══════════════════════════════════════════════════════════════════
# GET SIMPLIFIED CLAUSES
# ══════════════════════════════════════════════════════════════════

async def get_simplified_clauses(
    contract_id: str,
    risk_only: bool,
    current_user: dict
) -> dict:
    """
    Returns plain-English versions of all clauses.
    If risk_only=True, returns only High/Medium risk clauses.
    """
    
    db = get_database()
    analysis = await get_analysis_result(contract_id, current_user)
    
    clauses = analysis["clauses"]
    
    if risk_only:
        clauses = [
            c for c in clauses
            if c.get("risk_level") in ["High", "Medium"]
        ]
    
    simplified_list = []
    for clause in clauses:
        simplified_list.append({
            "clause_id": clause["clause_id"],
            "clause_type": clause["clause_type"],
            "risk_level": clause.get("risk_level"),
            "original": clause["original_text"],
            "simplified": clause.get("simplified_text", clause["original_text"])
        })
    
    return {
        "contract_id": contract_id,
        "total": len(simplified_list),
        "risk_only": risk_only,
        "simplified_clauses": simplified_list
    }


# ══════════════════════════════════════════════════════════════════
# GET SINGLE CLAUSE BY ID
# ══════════════════════════════════════════════════════════════════

async def get_clause_by_id(
    contract_id: str,
    clause_id: str,
    current_user: dict
) -> dict:
    """
    Fetches a single clause by its clause_id.
    """
    
    db = get_database()
    analysis = await get_analysis_result(contract_id, current_user)
    
    # Find clause
    clause = next(
        (c for c in analysis["clauses"] if c["clause_id"] == clause_id),
        None
    )
    
    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause with ID '{clause_id}' not found in this contract's analysis."
        )
    
    return {
        "contract_id": contract_id,
        "clause": clause
    }


# ══════════════════════════════════════════════════════════════════
# EXPORT ANALYSIS REPORT
# ══════════════════════════════════════════════════════════════════

async def export_analysis_report(
    contract_id: str,
    format: str,
    current_user: dict
) -> dict:
    """
    Generates a downloadable analysis report in PDF or JSON format.
    
    PDF: Professional formatted report with risk heatmap
    JSON: Raw structured data for programmatic use
    """
    
    db = get_database()
    from app.services.generation_service import generate_contract_document
    from app.services.storage_service import upload_to_cloud, get_download_url
    import json
    
    user_id = current_user["sub"]
    analysis = await get_analysis_result(contract_id, current_user)
    
    if format == "json":
        # Return JSON directly
        json_bytes = json.dumps(analysis, indent=2, default=str).encode("utf-8")
        filename = f"analysis_{contract_id}.json"
        
    else:  # pdf
        # Generate PDF report using generation service
        contract = await db["contracts"].find_one({"_id": ObjectId(contract_id)})
        
        pdf_bytes, filename, _ = generate_contract_document(
            original_contract=contract,
            clauses=analysis["clauses"],
            accepted_clauses=[],  # No replacements, just show analysis
            format="pdf",
            include_summary=True,
            version=1
        )
        json_bytes = pdf_bytes
    
    # Upload to S3
    cloud_url = await upload_to_cloud(
        contents=json_bytes,
        filename=filename,
        user_id=user_id,
        subfolder="reports"
    )
    
    # Generate download URL
    download_url = await get_download_url(cloud_url, expiry_minutes=30)
    
    logger.info(
        f"Analysis report exported | "
        f"contract_id={contract_id}, format={format}"
    )
    
    return {
        "contract_id": contract_id,
        "format": format,
        "download_url": download_url,
        "url_expires_at": datetime.utcnow() + timedelta(minutes=30),
        "generated_at": datetime.utcnow()
    }