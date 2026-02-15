# app/routes/contract_routes.py

from fastapi import (
    APIRouter, UploadFile, File,
    HTTPException, Depends, status,
    Query, BackgroundTasks
)
from fastapi.responses import StreamingResponse
from typing import Optional
from app.controllers.contract_controller import (
    upload_contract,
    initiate_chunked_upload,
    upload_chunk,
    complete_chunked_upload,
    compare_two_contracts,
    get_upload_status,
    get_all_contracts,
    get_contract_by_id,
    delete_contract,
    download_contract,
    get_contract_stats,
    search_contracts,
    update_contract_metadata,
    bulk_delete_contracts
)
from app.models.contract_model import (
    ContractResponse,
    ContractListResponse,
    ContractStatsResponse,
    ContractSearchResponse,
    ContractMetadataUpdateRequest,
    BulkDeleteRequest
)
from app.middleware.auth_middleware import require_legal_user

router = APIRouter(
    prefix="/contracts",
    tags=["📄 Contract Management"]
)

# ══════════════════════════════════════════════════════
# @route    POST /api/contracts/upload
# @desc     Upload a PDF or DOCX legal contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/upload",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a legal contract (PDF or DOCX)",
    description="""
    Upload a legal contract file for AI analysis.
    
    **Supported Formats:** PDF, DOCX
    **Max File Size:** 25 MB
    
    **Processing Pipeline:**
    1. File validation (type + size check)
    2. Text extraction (PyMuPDF for PDF, python-docx for DOCX)
    3. OCR fallback for scanned/image-based PDFs (Tesseract)
    4. Secure upload to cloud storage (AWS S3 / Firebase)
    5. Contract record created in MongoDB
    
    **Returns:** Contract ID, filename, status, upload timestamp
    """
)
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ...,
        description="Legal contract file — PDF or DOCX format only. Max 25MB."
    ),
    title: Optional[str] = Query(
        None,
        description="Optional custom title for the contract"
    ),
    tags: Optional[str] = Query(
        None,
        description="Comma-separated tags e.g. 'nda,employment,2024'"
    ),
    current_user: dict = Depends(require_legal_user)
):
    # ── Validate file type ──────────────────────────
    ALLOWED_TYPES = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": "Unsupported file type.",
                "allowed": ["application/pdf", ".docx"],
                "received": file.content_type
            }
        )

    # ── Validate file size (25 MB max) ─────────────
    MAX_SIZE = 25 * 1024 * 1024  # 25 MB
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds 25MB limit. Received: {len(contents) / (1024*1024):.2f} MB"
        )

    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    return await upload_contract(
        file=file,
        contents=contents,
        title=title,
        tags=tag_list,
        current_user=current_user,
        background_tasks=background_tasks
    )


# ══════════════════════════════════════════════════════
# Chunked Upload: Initiate
# POST /api/contracts/upload/initiate
# ══════════════════════════════════════════════════════
@router.post(
    "/upload/initiate",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a chunked upload",
    description="Creates an upload session and returns an `upload_id`."
)
async def initiate_upload(
    filename: str = Query(..., description="Original filename (e.g. contract.pdf)"),
    total_size: int = Query(..., description="Total size of file in bytes"),
    current_user: dict = Depends(require_legal_user)
):
    return await initiate_chunked_upload(filename=filename, total_size=total_size, current_user=current_user)


# ══════════════════════════════════════════════════════
# Chunked Upload: Upload Part
# POST /api/contracts/upload/{upload_id}/part
# ══════════════════════════════════════════════════════
@router.post(
    "/upload/{upload_id}/part",
    status_code=status.HTTP_200_OK,
    summary="Upload a single chunk/part of an upload"
)
async def upload_part(
    upload_id: str,
    chunk_index: int = Query(..., description="0-based chunk index"),
    chunk: UploadFile = File(..., description="Binary chunk data"),
    current_user: dict = Depends(require_legal_user)
):
    return await upload_chunk(upload_id=upload_id, chunk_index=chunk_index, chunk_file=chunk, current_user=current_user)


# ══════════════════════════════════════════════════════
# Chunked Upload: Complete
# POST /api/contracts/upload/{upload_id}/complete
# ══════════════════════════════════════════════════════
@router.post(
    "/upload/{upload_id}/complete",
    status_code=status.HTTP_200_OK,
    summary="Complete a chunked upload and trigger processing"
)
async def complete_upload(
    upload_id: str,
    filename: str = Query(..., description="Original filename provided at initiation"),
    title: Optional[str] = Query(None, description="Optional title for contract"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(require_legal_user)
):
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    return await complete_chunked_upload(
        upload_id=upload_id,
        filename=filename,
        title=title,
        tags=tag_list,
        current_user=current_user,
        background_tasks=background_tasks
    )


# ══════════════════════════════════════════════════════
# Upload Status - list uploaded parts
# GET /api/contracts/upload/{upload_id}/status
# ══════════════════════════════════════════════════════
@router.get(
    "/upload/{upload_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Get status of a chunked upload",
)
async def upload_status(
    upload_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await get_upload_status(upload_id)


# ══════════════════════════════════════════════════════
# Compare Two Contracts (upload two files)
# POST /api/contracts/compare
# ══════════════════════════════════════════════════════
@router.post(
    "/compare",
    status_code=status.HTTP_200_OK,
    summary="Compare two contract files",
    description="Uploads two files and returns a diff summary"
)
async def compare_contracts(
    file1: UploadFile = File(..., description="First contract file"),
    file2: UploadFile = File(..., description="Second contract file"),
    current_user: dict = Depends(require_legal_user)
):
    return await compare_two_contracts(file1, file2, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/contracts/
# @desc     Get all contracts of the logged-in user
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/",
    response_model=ContractListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all contracts of the current user",
    description="""
    Retrieves a paginated list of all contracts uploaded by the authenticated user.
    
    **Filtering Options:**
    - `status` — Filter by analysis status: `pending`, `processing`, `completed`, `failed`
    - `sort_by` — Sort field: `uploaded_at`, `filename`, `analysis_status`
    - `order` — Sort order: `asc` or `desc`
    - `page` + `limit` — Pagination controls
    
    **Returns:** List of contracts with metadata and analysis status.
    """
)
async def get_contracts(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by analysis status: pending | processing | completed | failed"
    ),
    sort_by: str = Query(
        "uploaded_at",
        description="Sort field: uploaded_at | filename | analysis_status"
    ),
    order: str = Query(
        "desc",
        description="Sort order: asc | desc"
    ),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Results per page (max 100)"),
    current_user: dict = Depends(require_legal_user)
):
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be 'asc' or 'desc'."
        )
    return await get_all_contracts(
        current_user=current_user,
        status_filter=status_filter,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit
    )


# ══════════════════════════════════════════════════════
# @route    GET /api/contracts/search
# @desc     Full-text search across user's contracts
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/search",
    response_model=ContractSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search contracts by filename, tags, or content",
    description="""
    Performs a full-text search across the user's contracts.
    
    **Searchable Fields:** filename, tags, extracted text content
    
    **Query Params:**
    - `q` — Search keyword (required, min 2 characters)
    - `field` — Restrict search to: `filename`, `tags`, or `content` (default: all)
    """
)
async def search(
    q: str = Query(..., min_length=2, description="Search keyword"),
    field: Optional[str] = Query(
        None,
        description="Search in specific field: filename | tags | content"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_legal_user)
):
    return await search_contracts(
        query=q,
        field=field,
        page=page,
        limit=limit,
        current_user=current_user
    )


# ══════════════════════════════════════════════════════
# @route    GET /api/contracts/stats
# @desc     Get contract usage statistics for dashboard
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/stats",
    response_model=ContractStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get contract statistics for dashboard",
    description="""
    Returns aggregated statistics for the user's contracts:
    
    - Total contracts uploaded
    - Breakdown by analysis status (pending / completed / failed)
    - Total high / medium / low risk clauses across all contracts
    - Contracts uploaded in the last 30 days
    - Most used contract types (NDA, Employment, etc.)
    """
)
async def get_stats(
    current_user: dict = Depends(require_legal_user)
):
    return await get_contract_stats(current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/contracts/{contract_id}
# @desc     Get a specific contract by its ID
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific contract by ID",
    description="""
    Fetches the full details of a single contract by its **contract_id**.
    
    **Returns:**
    - Contract metadata (filename, upload time, status)
    - Extracted text preview (first 500 characters)
    - Analysis summary (if analysis has been run)
    - Cloud storage URL
    
    **Access Control:** Users can only access their own contracts.
    """
)
async def get_contract(
    contract_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await get_contract_by_id(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    PATCH /api/contracts/{contract_id}
# @desc     Update contract title/tags metadata
# @access   Private
# ══════════════════════════════════════════════════════
@router.patch(
    "/{contract_id}",
    response_model=ContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Update contract metadata (title, tags)",
    description="""
    Update the editable metadata of a contract.
    
    **Updatable Fields:**
    - `title` — Custom label for the contract
    - `tags` — Array of classification tags
    
    **Note:** File content, extracted text, and analysis results
    cannot be modified through this endpoint.
    """
)
async def update_metadata(
    contract_id: str,
    payload: ContractMetadataUpdateRequest,
    current_user: dict = Depends(require_legal_user)
):
    return await update_contract_metadata(contract_id, payload, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/contracts/{contract_id}/download
# @desc     Download the original uploaded contract file
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download the original contract file",
    description="""
    Generates a **signed temporary download URL** for the original
    uploaded contract file from cloud storage.
    
    **URL Expiry:** 15 minutes from request time
    
    **Returns:** `{ "download_url": "https://..." }`
    """
)
async def download(
    contract_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await download_contract(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    DELETE /api/contracts/{contract_id}
# @desc     Delete a contract and all associated data
# @access   Private
# ══════════════════════════════════════════════════════
@router.delete(
    "/{contract_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a contract permanently",
    description="""
    Permanently deletes a contract and **all associated data** including:
    - Contract document from cloud storage (S3 / Firebase)
    - Contract record from MongoDB
    - All analysis results and clauses
    - All AI suggestions
    - All generated contract versions
    - Digital signature records
    
    ⚠️ **This action is irreversible.**
    """
)
async def delete(
    contract_id: str,
    current_user: dict = Depends(require_legal_user)
):
    return await delete_contract(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    DELETE /api/contracts/bulk-delete
# @desc     Delete multiple contracts at once
# @access   Private
# ══════════════════════════════════════════════════════
@router.delete(
    "/bulk-delete",
    status_code=status.HTTP_200_OK,
    summary="Bulk delete multiple contracts",
    description="""
    Deletes multiple contracts and all their associated data in a single request.
    
    **Body:** `{ "contract_ids": ["id1", "id2", "id3"] }`
    
    **Limit:** Maximum **20 contracts** per bulk delete request.
    
    Returns a summary of deleted and failed deletions.
    """
)
async def bulk_delete(
    payload: BulkDeleteRequest,
    current_user: dict = Depends(require_legal_user)
):
    if len(payload.contract_ids) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete more than 20 contracts at once."
        )
    return await bulk_delete_contracts(payload.contract_ids, current_user)
