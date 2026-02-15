# app/routes/generation_routes.py

from fastapi import (
    APIRouter, HTTPException,
    Depends, status, Query,
    BackgroundTasks
)
from app.controllers.generation_controller import (
    generate_contract,
    get_generated_contract,
    download_generated_contract,
    list_generated_versions,
    delete_generated_version,
    preview_generated_contract
)
from app.models.contract_model import (
    GeneratedContractResponse,
    GeneratedContractListResponse,
    GeneratedContractPreviewResponse
)
from app.middleware.auth_middleware import verify_token

router = APIRouter(
    prefix="/generate",
    tags=["⚙️ Contract Generation"]
)


# ══════════════════════════════════════════════════════
# @route    POST /api/generate/{contract_id}
# @desc     Generate a new balanced AI-reviewed contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/{contract_id}",
    response_model=GeneratedContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate new AI-reviewed balanced contract",
    description="""
    Creates a new, fair, and AI-reviewed version of the contract
    incorporating all **accepted suggestions**.
    
    **Generation Process:**
    1. Fetches all accepted suggestions for the contract
    2. Replaces original risky clauses with AI-suggested alternatives
    3. Retains rejected/pending clauses in their original form
    4. Formats and renders final document (PDF or DOCX)
    5. Uploads generated document to cloud storage
    6. Saves version record with applied changes log
    
    **Query Params:**
    - `format` — Output format: `pdf` (default) or `docx`
    - `include_summary` — Append AI analysis summary page to document
    
    **Returns:** Version ID, download URL, generation timestamp,
    list of applied suggestions.
    """
)
async def generate(
    contract_id: str,
    background_tasks: BackgroundTasks,
    format: str = Query(
        "pdf",
        description="Output format: pdf | docx"
    ),
    include_summary: bool = Query(
        True,
        description="Append analysis summary page to the generated document"
    ),
    current_user: dict = Depends(verify_token)
):
    if format not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'pdf' or 'docx'."
        )
    return await generate_contract(
        contract_id=contract_id,
        format=format,
        include_summary=include_summary,
        current_user=current_user,
        background_tasks=background_tasks
    )


# ══════════════════════════════════════════════════════
# @route    GET /api/generate/{contract_id}/preview
# @desc     Preview generated contract content (no file download)
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/preview",
    response_model=GeneratedContractPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview the generated contract content",
    description="""
    Returns a **text-based preview** of what the generated contract will look like,
    showing which clauses were replaced with AI alternatives.
    
    This does **not** generate or save any file — it's a dry run preview.
    
    **Returns:**
    - Full contract text with accepted suggestions applied
    - Change summary (original vs replacement for each modified clause)
    - Estimated document page count
    """
)
async def preview(
    contract_id: str,
    current_user: dict = Depends(verify_token)
):
    return await preview_generated_contract(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/generate/{contract_id}/versions
# @desc     List all generated versions of a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/versions",
    response_model=GeneratedContractListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all generated contract versions",
    description="""
    Returns the complete **version history** of AI-generated contracts
    derived from the original uploaded contract.
    
    Each version record includes:
    - Version number and ID
    - Generation timestamp
    - Output format (pdf/docx)
    - List of applied suggestion IDs
    - Download URL (if still valid)
    """
)
async def get_versions(
    contract_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(verify_token)
):
    return await list_generated_versions(
        contract_id=contract_id,
        page=page,
        limit=limit,
        current_user=current_user
    )


# ══════════════════════════════════════════════════════
# @route    GET /api/generate/{contract_id}/versions/{version_id}
# @desc     Get a specific generated contract version
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/versions/{version_id}",
    response_model=GeneratedContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific generated contract version",
    description="""
    Fetches the full metadata and details for a specific
    **generated contract version** by its `version_id`.
    """
)
async def get_version(
    contract_id: str,
    version_id: str,
    current_user: dict = Depends(verify_token)
):
    return await get_generated_contract(contract_id, version_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/generate/{contract_id}/versions/{version_id}/download
# @desc     Download a specific generated contract version
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/versions/{version_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download a generated contract version",
    description="""
    Generates and returns a **signed temporary download URL**
    for the specified generated contract version.
    
    - URL expires in **30 minutes**
    - File format is as specified during generation (pdf or docx)
    """
)
async def download(
    contract_id: str,
    version_id: str,
    current_user: dict = Depends(verify_token)
):
    return await download_generated_contract(contract_id, version_id, current_user)


# ══════════════════════════════════════════════════════
# @route    DELETE /api/generate/{contract_id}/versions/{version_id}
# @desc     Delete a specific generated version
# @access   Private
# ══════════════════════════════════════════════════════
@router.delete(
    "/{contract_id}/versions/{version_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a generated contract version",
    description="""
    Permanently deletes a specific generated contract version.
    
    - Removes file from cloud storage
    - Deletes version record from MongoDB
    
    ⚠️ **This action is irreversible.**
    The original contract and other versions are unaffected.
    """
)
async def delete_version(
    contract_id: str,
    version_id: str,
    current_user: dict = Depends(verify_token)
):
    return await delete_generated_version(contract_id, version_id, current_user)