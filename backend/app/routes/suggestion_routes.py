# app/routes/suggestion_routes.py

from fastapi import (
    APIRouter, HTTPException,
    Depends, status, Query
)
from typing import Optional
from app.controllers.suggestion_controller import (
    get_all_suggestions,
    get_suggestion_for_clause,
    accept_suggestion,
    reject_suggestion,
    regenerate_suggestion,
    accept_all_suggestions,
    reject_all_suggestions,
    get_suggestion_stats,
    custom_edit_suggestion
)
from app.models.clause_model import (
    SuggestionListResponse,
    SuggestionResponse,
    SuggestionActionResponse,
    SuggestionStatsResponse,
    CustomEditRequest
)
from app.middleware.auth_middleware import require_legal_user

router = APIRouter(
    prefix="/suggestions",
    tags=["💡 AI Suggestions"]
)


# ══════════════════════════════════════════════════════
# @route    GET /api/suggestions/{contract_id}
# @desc     Get all AI suggestions for a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}",
    response_model=SuggestionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all AI-generated suggestions for a contract",
    description="""
    Returns all AI-generated fair clause alternatives for risky or
    biased clauses identified in the given contract.
    
    **Each suggestion includes:**
    - Original clause text
    - Risk level and reason for flagging
    - AI-recommended fair alternative
    - Suggestion status: `pending` | `accepted` | `rejected`
    
    **Filters:**
    - `status` — Filter by suggestion status
    - `risk_level` — Filter by clause risk level
    - `clause_type` — Filter by type (e.g., Confidentiality)
    """
)
async def get_suggestions(
    contract_id: str,
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: pending | accepted | rejected"
    ),
    risk_level: Optional[str] = Query(
        None,
        description="Filter by risk level: Low | Medium | High"
    ),
    clause_type: Optional[str] = Query(
        None,
        description="Filter by clause type e.g. Confidentiality, Payment"
    ),
    current_user: dict = Depends(require_legal_user)
):
    if status_filter and status_filter not in ["pending", "accepted", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'pending', 'accepted', or 'rejected'."
        )
    if risk_level and risk_level not in ["Low", "Medium", "High"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Risk level must be 'Low', 'Medium', or 'High'."
        )
    return await get_all_suggestions(
        contract_id=contract_id,
        status_filter=status_filter,
        risk_level=risk_level,
        clause_type=clause_type,
        current_user=current_user
    )


# ══════════════════════════════════════════════════════
# @route    GET /api/suggestions/{contract_id}/stats
# @desc     Get suggestion statistics for a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/stats",
    response_model=SuggestionStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get suggestion statistics for a contract",
    description="""
    Returns a summary of AI suggestion activity for the contract:
    
    - Total suggestions generated
    - Count by status: pending / accepted / rejected
    - Count by clause type
    - Acceptance rate percentage
    """
)
async def get_stats(
    contract_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await get_suggestion_stats(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/suggestions/{contract_id}/clause/{clause_id}
# @desc     Get AI suggestion for a specific clause
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/clause/{clause_id}",
    response_model=SuggestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI suggestion for a specific clause",
    description="""
    Returns the AI-generated fair alternative for a single clause
    identified by its **clause_id** within the contract.
    
    **Returns:** Original text, risk info, suggested alternative, and current status.
    """
)
async def get_clause_suggestion(
    contract_id: str,
    clause_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await get_suggestion_for_clause(contract_id, clause_id, current_user)


# ══════════════════════════════════════════════════════
# @route    PATCH /api/suggestions/{contract_id}/clause/{clause_id}/accept
# @desc     Accept an AI suggestion — apply to contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.patch(
    "/{contract_id}/clause/{clause_id}/accept",
    response_model=SuggestionActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept an AI suggestion and mark for inclusion",
    description="""
    Marks the AI suggestion for the specified clause as **accepted**.
    
    **Effect:**
    - Suggestion status is updated to `accepted`
    - This clause's AI alternative will be used in the generated contract
    - Accepted suggestions can still be reversed before generation
    """
)
async def accept(
    contract_id: str,
    clause_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await accept_suggestion(contract_id, clause_id, current_user)


# ══════════════════════════════════════════════════════
# @route    PATCH /api/suggestions/{contract_id}/clause/{clause_id}/reject
# @desc     Reject an AI suggestion — keep original clause
# @access   Private
# ══════════════════════════════════════════════════════
@router.patch(
    "/{contract_id}/clause/{clause_id}/reject",
    response_model=SuggestionActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject AI suggestion and retain original clause",
    description="""
    Marks the AI suggestion as **rejected**.
    
    **Effect:**
    - Suggestion status is updated to `rejected`
    - The original clause will be kept as-is in the generated contract
    - Rejection can be reversed until contract generation
    """
)
async def reject(
    contract_id: str,
    clause_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await reject_suggestion(contract_id, clause_id, current_user)


# ══════════════════════════════════════════════════════
# @route    PATCH /api/suggestions/{contract_id}/clause/{clause_id}/edit
# @desc     Manually edit a suggestion before accepting
# @access   Private
# ══════════════════════════════════════════════════════
@router.patch(
    "/{contract_id}/clause/{clause_id}/edit",
    response_model=SuggestionActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Manually edit an AI suggestion",
    description="""
    Allows the user to **manually edit** the AI-suggested text before
    accepting it into the final contract.
    
    **Body:** `{ "edited_text": "Your custom clause text here..." }`
    
    The edited version will be used in the generated contract
    when this clause's suggestion is accepted.
    """
)
async def edit_suggestion(
    contract_id: str,
    clause_id: str,
    payload: CustomEditRequest,
    current_user: dict = Depends(require_legal_user)
):
    return await custom_edit_suggestion(contract_id, clause_id, payload, current_user)


# ══════════════════════════════════════════════════════
# @route    POST /api/suggestions/{contract_id}/clause/{clause_id}/regenerate
# @desc     Regenerate AI suggestion for a clause
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/{contract_id}/clause/{clause_id}/regenerate",
    response_model=SuggestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate AI suggestion for a clause",
    description="""
    Discards the current AI suggestion and generates a **fresh alternative**
    for the specified clause using the latest AI model.
    
    Useful when:
    - The previous suggestion was inappropriate
    - The user wants more options
    - AI context has been updated
    
    ⚠️ The previous suggestion will be replaced permanently.
    """
)
async def regenerate(
    contract_id: str,
    clause_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await regenerate_suggestion(contract_id, clause_id, current_user)


# ══════════════════════════════════════════════════════
# @route    PATCH /api/suggestions/{contract_id}/accept-all
# @desc     Accept all pending AI suggestions at once
# @access   Private
# ══════════════════════════════════════════════════════
@router.patch(
    "/{contract_id}/accept-all",
    status_code=status.HTTP_200_OK,
    summary="Accept all pending AI suggestions",
    description="""
    Bulk accepts all suggestions with `pending` status.
    
    **Optional Filter:**
    - `risk_level` — Only accept suggestions for clauses with specified risk level
      (e.g., only accept `High` risk clause suggestions)
    
    **Returns:** Count of accepted suggestions.
    """
)
async def accept_all(
    contract_id: str,
    risk_level: Optional[str] = Query(
        None,
        description="Optionally limit to specific risk level: High | Medium | Low"
    ),
    current_user: dict = Depends(require_legal_user)
):
    return await accept_all_suggestions(contract_id, risk_level, current_user)


# ══════════════════════════════════════════════════════
# @route    PATCH /api/suggestions/{contract_id}/reject-all
# @desc     Reject all pending AI suggestions at once
# @access   Private
# ══════════════════════════════════════════════════════
@router.patch(
    "/{contract_id}/reject-all",
    status_code=status.HTTP_200_OK,
    summary="Reject all pending AI suggestions",
    description="""
    Bulk rejects all suggestions with `pending` status.
    All original clauses will be retained in the generated contract.
    
    **Returns:** Count of rejected suggestions.
    """
)
async def reject_all(
    contract_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await reject_all_suggestions(contract_id, current_user)
