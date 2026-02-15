# app/controllers/suggestion_controller.py

from fastapi import HTTPException, status
from app.config.database import get_database
from app.services.suggestion_service import regenerate_suggestion_for_clause
from app.models.clause_model import CustomEditRequest
from datetime import datetime
from bson import ObjectId
from typing import Optional
import logging

logger = logging.getLogger("legalyze.suggestion")


# ══════════════════════════════════════════════════════════════════
# GET ALL SUGGESTIONS
# ══════════════════════════════════════════════════════════════════

async def get_all_suggestions(
    contract_id: str,
    status_filter: Optional[str],
    risk_level: Optional[str],
    clause_type: Optional[str],
    current_user: dict
) -> dict:
    """
    Returns all AI suggestions for a contract with optional filters.
    
    Filters:
    - status: pending | accepted | rejected | edited
    - risk_level: High | Medium | Low
    - clause_type: Confidentiality, Payment, etc.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Verify ownership
    contract = await db["contracts"].find_one({
        "_id": ObjectId(contract_id),
        "user_id": user_id
    })
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    
    # Get analysis
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run analysis first."
        )
    
    clauses = analysis["clauses"]
    
    # Filter by status
    if status_filter:
        clauses = [
            c for c in clauses
            if c.get("suggestion_status") == status_filter
        ]
    
    # Filter by risk level
    if risk_level:
        clauses = [
            c for c in clauses
            if c.get("risk_level") == risk_level
        ]
    
    # Filter by clause type
    if clause_type:
        clauses = [
            c for c in clauses
            if c.get("clause_type") == clause_type
        ]
    
    # Build suggestion responses
    suggestions = []
    for clause in clauses:
        if clause.get("suggestion"):  # Only include clauses with suggestions
            suggestions.append({
                "clause_id": clause["clause_id"],
                "contract_id": contract_id,
                "clause_type": clause["clause_type"],
                "original_text": clause["original_text"],
                "risk_level": clause["risk_level"],
                "risk_reason": clause.get("risk_reason", ""),
                "risk_score": clause.get("risk_score"),
                "suggested_alternative": clause["suggestion"],
                "edited_alternative": clause.get("edited_suggestion"),
                "effective_suggestion": (
                    clause.get("edited_suggestion") or clause["suggestion"]
                ),
                "status": clause["suggestion_status"],
                "rag_context_summary": (
                    clause.get("rag_context", {}).get("context_summary")
                    if clause.get("rag_context") else None
                ),
                "updated_at": clause.get("updated_at")
            })
    
    # Count by status
    by_status = {
        "pending": sum(1 for s in suggestions if s["status"] == "pending"),
        "accepted": sum(1 for s in suggestions if s["status"] == "accepted"),
        "rejected": sum(1 for s in suggestions if s["status"] == "rejected"),
        "edited": sum(1 for s in suggestions if s["status"] == "edited")
    }
    
    return {
        "contract_id": contract_id,
        "total": len(suggestions),
        "pending_count": by_status["pending"],
        "accepted_count": by_status["accepted"],
        "rejected_count": by_status["rejected"],
        "edited_count": by_status["edited"],
        "filters_applied": {
            "status": status_filter,
            "risk_level": risk_level,
            "clause_type": clause_type
        },
        "suggestions": suggestions
    }


# ══════════════════════════════════════════════════════════════════
# GET SUGGESTION FOR SPECIFIC CLAUSE
# ══════════════════════════════════════════════════════════════════

async def get_suggestion_for_clause(
    contract_id: str,
    clause_id: str,
    current_user: dict
) -> dict:
    """
    Returns the AI suggestion for a single clause.
    """
    
    db = get_database()
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    # Find clause
    clause = next(
        (c for c in analysis["clauses"] if c["clause_id"] == clause_id),
        None
    )
    
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found.")
    
    if not clause.get("suggestion"):
        raise HTTPException(
            status_code=404,
            detail="No suggestion available for this clause (likely Low risk)."
        )
    
    return {
        "clause_id": clause["clause_id"],
        "contract_id": contract_id,
        "clause_type": clause["clause_type"],
        "original_text": clause["original_text"],
        "risk_level": clause["risk_level"],
        "risk_reason": clause.get("risk_reason", ""),
        "risk_score": clause.get("risk_score"),
        "suggested_alternative": clause["suggestion"],
        "edited_alternative": clause.get("edited_suggestion"),
        "effective_suggestion": (
            clause.get("edited_suggestion") or clause["suggestion"]
        ),
        "status": clause["suggestion_status"],
        "rag_context_summary": (
            clause.get("rag_context", {}).get("context_summary")
            if clause.get("rag_context") else None
        ),
        "updated_at": clause.get("updated_at")
    }


# ══════════════════════════════════════════════════════════════════
# ACCEPT SUGGESTION
# ══════════════════════════════════════════════════════════════════

async def accept_suggestion(
    contract_id: str,
    clause_id: str,
    current_user: dict
) -> dict:
    """
    Marks a suggestion as accepted.
    The accepted suggestion will be used in contract generation.
    """
    
    db = get_database()
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    # Find and update clause
    clause_found = False
    previous_status = None
    
    for clause in analysis["clauses"]:
        if clause["clause_id"] == clause_id:
            previous_status = clause["suggestion_status"]
            clause["suggestion_status"] = "accepted"
            clause["updated_at"] = datetime.utcnow()
            clause_found = True
            break
    
    if not clause_found:
        raise HTTPException(status_code=404, detail="Clause not found.")
    
    # Save updated analysis
    await db["analyses"].update_one(
        {"_id": analysis["_id"]},
        {"$set": {"clauses": analysis["clauses"]}}
    )
    
    logger.info(
        f"Suggestion accepted | "
        f"contract={contract_id}, clause={clause_id}"
    )
    
    # Get effective suggestion text
    clause = next(c for c in analysis["clauses"] if c["clause_id"] == clause_id)
    effective_text = clause.get("edited_suggestion") or clause.get("suggestion")
    
    return {
        "clause_id": clause_id,
        "contract_id": contract_id,
        "previous_status": previous_status,
        "new_status": "accepted",
        "effective_text": effective_text,
        "message": "Suggestion accepted. It will be used in the generated contract.",
        "updated_at": datetime.utcnow()
    }


# ══════════════════════════════════════════════════════════════════
# REJECT SUGGESTION
# ══════════════════════════════════════════════════════════════════

async def reject_suggestion(
    contract_id: str,
    clause_id: str,
    current_user: dict
) -> dict:
    """
    Marks a suggestion as rejected.
    The original clause will be retained in the generated contract.
    """
    
    db = get_database()
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    clause_found = False
    previous_status = None
    
    for clause in analysis["clauses"]:
        if clause["clause_id"] == clause_id:
            previous_status = clause["suggestion_status"]
            clause["suggestion_status"] = "rejected"
            clause["updated_at"] = datetime.utcnow()
            clause_found = True
            break
    
    if not clause_found:
        raise HTTPException(status_code=404, detail="Clause not found.")
    
    await db["analyses"].update_one(
        {"_id": analysis["_id"]},
        {"$set": {"clauses": analysis["clauses"]}}
    )
    
    logger.info(
        f"Suggestion rejected | "
        f"contract={contract_id}, clause={clause_id}"
    )
    
    return {
        "clause_id": clause_id,
        "contract_id": contract_id,
        "previous_status": previous_status,
        "new_status": "rejected",
        "message": "Suggestion rejected. Original clause will be retained.",
        "updated_at": datetime.utcnow()
    }


# ══════════════════════════════════════════════════════════════════
# MANUALLY EDIT SUGGESTION
# ══════════════════════════════════════════════════════════════════

async def custom_edit_suggestion(
    contract_id: str,
    clause_id: str,
    payload: CustomEditRequest,
    current_user: dict
) -> dict:
    """
    Allows the user to manually edit the AI suggestion.
    The edited version takes precedence when generating contracts.
    """
    
    db = get_database()
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    clause_found = False
    
    for clause in analysis["clauses"]:
        if clause["clause_id"] == clause_id:
            # Store original suggestion if first edit
            if not clause.get("edited_suggestion"):
                original = clause.get("suggestion", "")
            else:
                original = clause["edited_suggestion"]
            
            # Apply edit
            clause["edited_suggestion"] = payload.edited_text
            clause["suggestion_status"] = "edited"
            clause["updated_at"] = datetime.utcnow()
            
            # Log edit
            if "edit_log" not in clause:
                clause["edit_log"] = []
            
            clause["edit_log"].append({
                "original_suggestion": original,
                "edited_text": payload.edited_text,
                "edited_at": datetime.utcnow(),
                "edit_reason": payload.edit_reason
            })
            
            clause_found = True
            break
    
    if not clause_found:
        raise HTTPException(status_code=404, detail="Clause not found.")
    
    await db["analyses"].update_one(
        {"_id": analysis["_id"]},
        {"$set": {"clauses": analysis["clauses"]}}
    )
    
    logger.info(
        f"Suggestion manually edited | "
        f"contract={contract_id}, clause={clause_id}"
    )
    
    return {
        "clause_id": clause_id,
        "contract_id": contract_id,
        "previous_status": "pending",
        "new_status": "edited",
        "effective_text": payload.edited_text,
        "message": "Suggestion edited successfully. Your custom version will be used in generation.",
        "updated_at": datetime.utcnow()
    }


# ══════════════════════════════════════════════════════════════════
# REGENERATE SUGGESTION
# ══════════════════════════════════════════════════════════════════

async def regenerate_suggestion(
    contract_id: str,
    clause_id: str,
    current_user: dict
) -> dict:
    """
    Generates a fresh AI suggestion for a clause.
    Replaces the previous suggestion permanently.
    """
    
    db = get_database()
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    # Find clause
    clause = next(
        (c for c in analysis["clauses"] if c["clause_id"] == clause_id),
        None
    )
    
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found.")
    
    # Regenerate suggestion
    try:
        new_suggestion = regenerate_suggestion_for_clause(clause)
        
        # Update clause
        for c in analysis["clauses"]:
            if c["clause_id"] == clause_id:
                c["suggestion"] = new_suggestion
                c["edited_suggestion"] = None  # Clear manual edit
                c["suggestion_status"] = "pending"
                c["updated_at"] = datetime.utcnow()
                break
        
        # Save
        await db["analyses"].update_one(
            {"_id": analysis["_id"]},
            {"$set": {"clauses": analysis["clauses"]}}
        )
        
        logger.info(
            f"Suggestion regenerated | "
            f"contract={contract_id}, clause={clause_id}"
        )
        
        return {
            "clause_id": clause_id,
            "contract_id": contract_id,
            "clause_type": clause["clause_type"],
            "original_text": clause["original_text"],
            "risk_level": clause["risk_level"],
            "risk_reason": clause.get("risk_reason", ""),
            "suggested_alternative": new_suggestion,
            "status": "pending",
            "message": "New suggestion generated successfully."
        }
    
    except Exception as e:
        logger.error(f"Suggestion regeneration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate suggestion: {str(e)}"
        )


# ══════════════════════════════════════════════════════════════════
# ACCEPT ALL SUGGESTIONS
# ══════════════════════════════════════════════════════════════════

async def accept_all_suggestions(
    contract_id: str,
    risk_level: Optional[str],
    current_user: dict
) -> dict:
    """
    Bulk accepts all pending suggestions.
    If risk_level specified, only accepts that risk level.
    """
    
    db = get_database()
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    accepted_count = 0
    
    for clause in analysis["clauses"]:
        if clause.get("suggestion_status") != "pending":
            continue
        
        if risk_level and clause.get("risk_level") != risk_level:
            continue
        
        clause["suggestion_status"] = "accepted"
        clause["updated_at"] = datetime.utcnow()
        accepted_count += 1
    
    await db["analyses"].update_one(
        {"_id": analysis["_id"]},
        {"$set": {"clauses": analysis["clauses"]}}
    )
    
    logger.info(
        f"Bulk accept | "
        f"contract={contract_id}, accepted={accepted_count}, "
        f"risk_filter={risk_level}"
    )
    
    return {
        "success": True,
        "contract_id": contract_id,
        "accepted_count": accepted_count,
        "risk_level_filter": risk_level,
        "message": f"Accepted {accepted_count} pending suggestions."
    }


# ══════════════════════════════════════════════════════════════════
# REJECT ALL SUGGESTIONS
# ══════════════════════════════════════════════════════════════════

async def reject_all_suggestions(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Bulk rejects all pending suggestions.
    """
    
    db = get_database()
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    rejected_count = 0
    
    for clause in analysis["clauses"]:
        if clause.get("suggestion_status") == "pending":
            clause["suggestion_status"] = "rejected"
            clause["updated_at"] = datetime.utcnow()
            rejected_count += 1
    
    await db["analyses"].update_one(
        {"_id": analysis["_id"]},
        {"$set": {"clauses": analysis["clauses"]}}
    )
    
    logger.info(
        f"Bulk reject | contract={contract_id}, rejected={rejected_count}"
    )
    
    return {
        "success": True,
        "contract_id": contract_id,
        "rejected_count": rejected_count,
        "message": f"Rejected {rejected_count} pending suggestions."
    }


# ══════════════════════════════════════════════════════════════════
# GET SUGGESTION STATS
# ══════════════════════════════════════════════════════════════════

async def get_suggestion_stats(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Returns statistics about suggestions for a contract.
    """
    
    db = get_database()
    from app.services.suggestion_service import compute_suggestion_stats
    
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    stats = compute_suggestion_stats(analysis["clauses"])
    stats["contract_id"] = contract_id
    stats["computed_at"] = datetime.utcnow()
    
    return stats