# app/controllers/contract_controller.py

from fastapi import HTTPException, status, UploadFile, BackgroundTasks
from app.config.database import get_database
from app.services.extractor_service import (
    extract_text_from_file,
    get_file_size_kb,
    is_text_sufficient
)
from app.services.ocr_service import extract_text_with_ocr, get_ocr_confidence
from app.services.storage_service import (
    upload_to_cloud,
    delete_from_cloud,
    get_download_url,
    bulk_delete_from_cloud
)
from app.models.contract_model import (
    ContractMetadataUpdateRequest,
    BulkDeleteRequest
)
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional, List
import logging

logger = logging.getLogger("legalyze.contract")


# ══════════════════════════════════════════════════════════════════
# UPLOAD CONTRACT
# ══════════════════════════════════════════════════════════════════

async def upload_contract(
    file: UploadFile,
    contents: bytes,
    title: Optional[str],
    tags: List[str],
    current_user: dict,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Uploads and processes a contract document.
    
    Pipeline:
    1. Extract text from PDF/DOCX
    2. If extraction yields < 50 words → try OCR
    3. Upload file to S3
    4. Create contract record in MongoDB
    5. (Optional) Trigger background analysis
    
    Returns:
        Contract metadata response
    """
    
    db = get_database()
    user_id     = current_user["sub"]
    filename    = file.filename
    content_type = file.content_type
    
    logger.info(
        f"Contract upload started | "
        f"user={user_id}, file={filename}, size={len(contents)//1024}KB"
    )
    
    # ── Step 1: Text Extraction ──────────────────────────────────
    try:
        extracted_text, page_count, word_count = extract_text_from_file(
            contents, content_type
        )
        
        # If insufficient text, try OCR
        if not is_text_sufficient(extracted_text):
            logger.warning(
                f"Insufficient text extracted ({word_count} words) — trying OCR"
            )
            
            # Check OCR confidence before proceeding
            ocr_conf = get_ocr_confidence(contents)
            
            if ocr_conf < 40:
                logger.error(f"OCR confidence too low: {ocr_conf}%")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Document appears to be scanned with poor quality. "
                        f"OCR confidence: {ocr_conf}%. "
                        f"Please upload a clearer scan or a digital document."
                    )
                )
            
            extracted_text, page_count, word_count = extract_text_with_ocr(
                contents, content_type
            )
    
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from document: {str(e)}"
        )
    
    if word_count < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Document contains too little text ({word_count} words). "
                f"Please upload a valid legal contract."
            )
        )
    
    logger.info(
        f"Text extracted successfully | "
        f"pages={page_count}, words={word_count}"
    )
    
    # ── Step 2: Upload to Cloud ──────────────────────────────────
    try:
        cloud_url = await upload_to_cloud(
            contents=contents,
            filename=filename,
            user_id=user_id,
            subfolder="contracts"
        )
    except Exception as e:
        logger.error(f"Cloud upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to cloud storage: {str(e)}"
        )
    
    # ── Step 3: Create MongoDB Record ────────────────────────────
    contract = {
        "user_id": user_id,
        "filename": filename,
        "title": title or filename,
        "category": None,   # User can set later
        "tags": tags,
        "content_type": content_type,
        "file_size_kb": get_file_size_kb(contents),
        "page_count": page_count,
        "cloud_url": cloud_url,
        "extracted_text": extracted_text,
        "extracted_text_preview": extracted_text[:500] if extracted_text else None,
        "word_count": word_count,
        "analysis_status": "pending",
        "analysis_summary": None,
        "signature_status": {
            "is_signed": False,
            "signed_by": None,
            "signed_at": None,
            "is_verified": False,
            "is_revoked": False,
            "countersigned": False
        },
        "notes": None,
        "uploaded_at": datetime.utcnow(),
        "updated_at": None
    }
    
    result = await db["contracts"].insert_one(contract)
    contract_id = str(result.inserted_id)
    
    logger.info(
        f"Contract uploaded successfully | "
        f"id={contract_id}, words={word_count}"
    )
    
    return {
        "id": contract_id,
        "filename": filename,
        "title": title or filename,
        "tags": tags,
        "content_type": content_type,
        "file_size_kb": contract["file_size_kb"],
        "page_count": page_count,
        "analysis_status": "pending",
        "uploaded_at": contract["uploaded_at"],
        "message": "Contract uploaded successfully. Ready for analysis."
    }


# ══════════════════════════════════════════════════════════════════
# GET ALL CONTRACTS
# ══════════════════════════════════════════════════════════════════

async def get_all_contracts(
    current_user: dict,
    status_filter: Optional[str],
    sort_by: str,
    order: str,
    page: int,
    limit: int
) -> dict:
    """
    Retrieves paginated list of user's contracts with filters.
    
    Supports:
    - Status filtering (pending, processing, completed, failed)
    - Sorting (uploaded_at, filename, analysis_status)
    - Pagination
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Build query
    query = {"user_id": user_id}
    if status_filter:
        query["analysis_status"] = status_filter
    
    # Count total
    total = await db["contracts"].count_documents(query)
    
    # Sort order
    sort_order = 1 if order == "asc" else -1
    
    # Fetch paginated results
    skip = (page - 1) * limit
    
    cursor = db["contracts"].find(query).sort(
        sort_by, sort_order
    ).skip(skip).limit(limit)
    
    contracts = await cursor.to_list(length=limit)
    
    # Build lightweight response
    contract_list = []
    for c in contracts:
        summary = c.get("analysis_summary") or {}
        contract_list.append({
            "id": str(c["_id"]),
            "filename": c["filename"],
            "title": c.get("title"),
            "category": c.get("category"),
            "tags": c.get("tags", []),
            "analysis_status": c.get("analysis_status", "pending"),
            "high_risk_count": summary.get("high_risk_count", 0),
            "overall_risk_score": summary.get("overall_risk_score", 0),
            "is_signed": c.get("signature_status", {}).get("is_signed", False),
            "uploaded_at": c["uploaded_at"]
        })
    
    total_pages = (total + limit - 1) // limit
    
    logger.info(
        f"Contracts fetched | "
        f"user={user_id}, page={page}, total={total}"
    )
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "contracts": contract_list
    }


# ══════════════════════════════════════════════════════════════════
# GET CONTRACT BY ID
# ══════════════════════════════════════════════════════════════════

async def get_contract_by_id(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Fetches a single contract by ID.
    
    Access control: User can only access their own contracts.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    try:
        oid = ObjectId(contract_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contract ID format."
        )
    
    contract = await db["contracts"].find_one({
        "_id": oid,
        "user_id": user_id
    })
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or you don't have access to it."
        )
    
    # Build response
    contract["id"] = str(contract.pop("_id"))
    
    # Don't send full extracted_text in response (too large)
    # Client can download if needed
    contract.pop("extracted_text", None)
    
    return contract


# ══════════════════════════════════════════════════════════════════
# SEARCH CONTRACTS
# ══════════════════════════════════════════════════════════════════

async def search_contracts(
    query: str,
    field: Optional[str],
    page: int,
    limit: int,
    current_user: dict
) -> dict:
    """
    Full-text search across user's contracts.
    
    Search fields: filename, tags, extracted_text
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Build search filter
    search_filter = {"user_id": user_id}
    
    if field == "filename":
        search_filter["filename"] = {"$regex": query, "$options": "i"}
    elif field == "tags":
        search_filter["tags"] = {"$regex": query, "$options": "i"}
    elif field == "content":
        search_filter["extracted_text"] = {"$regex": query, "$options": "i"}
    else:
        # Search all fields
        search_filter["$or"] = [
            {"filename": {"$regex": query, "$options": "i"}},
            {"tags": {"$regex": query, "$options": "i"}},
            {"extracted_text": {"$regex": query, "$options": "i"}}
        ]
    
    total = await db["contracts"].count_documents(search_filter)
    
    skip = (page - 1) * limit
    cursor = db["contracts"].find(search_filter).sort(
        "uploaded_at", -1
    ).skip(skip).limit(limit)
    
    results = await cursor.to_list(length=limit)
    
    # Build result list
    result_list = []
    for c in results:
        summary = c.get("analysis_summary") or {}
        result_list.append({
            "id": str(c["_id"]),
            "filename": c["filename"],
            "title": c.get("title"),
            "category": c.get("category"),
            "tags": c.get("tags", []),
            "analysis_status": c.get("analysis_status", "pending"),
            "high_risk_count": summary.get("high_risk_count", 0),
            "overall_risk_score": summary.get("overall_risk_score", 0),
            "is_signed": c.get("signature_status", {}).get("is_signed", False),
            "uploaded_at": c["uploaded_at"]
        })
    
    logger.info(
        f"Contract search | "
        f"user={user_id}, query='{query}', results={total}"
    )
    
    return {
        "query": query,
        "field": field,
        "total_results": total,
        "page": page,
        "limit": limit,
        "results": result_list
    }


# ══════════════════════════════════════════════════════════════════
# GET CONTRACT STATS
# ══════════════════════════════════════════════════════════════════

async def get_contract_stats(current_user: dict) -> dict:
    """
    Computes aggregate statistics for dashboard.
    
    Returns:
    - Total contracts
    - Breakdown by status, category
    - Total risk clause counts
    - Contracts uploaded in last 30 days
    - Average risk score
    - Signed/unsigned count
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$facet": {
                "total": [{"$count": "count"}],
                "by_status": [
                    {"$group": {"_id": "$analysis_status", "count": {"$sum": 1}}}
                ],
                "by_category": [
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}}
                ],
                "risk_summary": [
                    {
                        "$group": {
                            "_id": None,
                            "total_high": {"$sum": "$analysis_summary.high_risk_count"},
                            "total_medium": {"$sum": "$analysis_summary.medium_risk_count"},
                            "total_low": {"$sum": "$analysis_summary.low_risk_count"},
                            "avg_risk": {"$avg": "$analysis_summary.overall_risk_score"}
                        }
                    }
                ],
                "recent": [
                    {
                        "$match": {
                            "uploaded_at": {
                                "$gte": datetime.utcnow() - timedelta(days=30)
                            }
                        }
                    },
                    {"$count": "count"}
                ],
                "signatures": [
                    {
                        "$group": {
                            "_id": "$signature_status.is_signed",
                            "count": {"$sum": 1}
                        }
                    }
                ]
            }
        }
    ]
    
    result = await db["contracts"].aggregate(pipeline).to_list(length=1)
    data   = result[0] if result else {}
    
    # Parse results - handle empty lists
    total_list = data.get("total", [])
    total = total_list[0].get("count", 0) if total_list else 0
    
    by_status = {
        item["_id"]: item["count"]
        for item in data.get("by_status", [])
    }
    
    by_category = {
        item["_id"]: item["count"]
        for item in data.get("by_category", [])
        if item["_id"] is not None
    }
    
    risk_data = data.get("risk_summary", [{}])[0] if data.get("risk_summary") else {}
    
    recent_list = data.get("recent", [])
    recent_count = recent_list[0].get("count", 0) if recent_list else 0
    
    sig_data = {
        item["_id"]: item["count"]
        for item in data.get("signatures", [])
    }
    
    return {
        "total_contracts": total,
        "by_status": by_status,
        "by_category": by_category,
        "total_high_risk_clauses": risk_data.get("total_high", 0),
        "total_medium_risk_clauses": risk_data.get("total_medium", 0),
        "total_low_risk_clauses": risk_data.get("total_low", 0),
        "contracts_last_30_days": recent_count,
        "avg_risk_score": round(risk_data.get("avg_risk", 0.0), 2),
        "most_common_clause_type": None,  # Requires analysis collection join
        "signed_contracts": sig_data.get(True, 0),
        "unsigned_contracts": sig_data.get(False, 0),
        "generated_at": datetime.utcnow()
    }


# ══════════════════════════════════════════════════════════════════
# UPDATE CONTRACT METADATA
# ══════════════════════════════════════════════════════════════════

async def update_contract_metadata(
    contract_id: str,
    payload: ContractMetadataUpdateRequest,
    current_user: dict
) -> dict:
    """
    Updates contract title, tags, category, notes.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    update_fields = {}
    
    if payload.title is not None:
        update_fields["title"] = payload.title
    
    if payload.tags is not None:
        update_fields["tags"] = payload.tags
    
    if payload.category is not None:
        update_fields["category"] = payload.category
    
    if payload.notes is not None:
        update_fields["notes"] = payload.notes
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update."
        )
    
    update_fields["updated_at"] = datetime.utcnow()
    
    result = await db["contracts"].update_one(
        {"_id": ObjectId(contract_id), "user_id": user_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found.")
    
    logger.info(
        f"Contract metadata updated | "
        f"id={contract_id}, fields={list(update_fields.keys())}"
    )
    
    return await get_contract_by_id(contract_id, current_user)


# ══════════════════════════════════════════════════════════════════
# DOWNLOAD CONTRACT
# ══════════════════════════════════════════════════════════════════

async def download_contract(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Generates a pre-signed download URL for the contract file.
    """
    
    db = get_database()
    contract = await get_contract_by_id(contract_id, current_user)
    
    cloud_url = contract.get("cloud_url")
    if not cloud_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract file not found in storage."
        )
    
    download_url = await get_download_url(cloud_url, expiry_minutes=15)
    
    return {
        "contract_id": contract_id,
        "filename": contract["filename"],
        "download_url": download_url,
        "expires_in_minutes": 15
    }


# ══════════════════════════════════════════════════════════════════
# DELETE CONTRACT
# ══════════════════════════════════════════════════════════════════

async def delete_contract(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Permanently deletes a contract and all associated data:
    - Contract file from S3
    - Contract record from MongoDB
    - Analysis results
    - Generated versions
    - Signatures
    """
    
    db = get_database()
    contract = await get_contract_by_id(contract_id, current_user)
    
    # Delete from cloud storage
    if contract.get("cloud_url"):
        await delete_from_cloud(contract["cloud_url"])
    
    # Delete contract record
    await db["contracts"].delete_one({"_id": ObjectId(contract_id)})
    
    # Delete analysis
    await db["analyses"].delete_many({"contract_id": contract_id})
    
    # Delete generated versions
    versions = await db["generated_contracts"].find(
        {"contract_id": contract_id}
    ).to_list(length=100)
    
    for v in versions:
        if v.get("cloud_url"):
            await delete_from_cloud(v["cloud_url"])
    
    await db["generated_contracts"].delete_many({"contract_id": contract_id})
    
    # Delete signatures
    await db["signatures"].delete_many({"contract_id": contract_id})
    
    logger.info(
        f"Contract deleted | "
        f"id={contract_id}, versions_deleted={len(versions)}"
    )
    
    return {
        "success": True,
        "message": f"Contract '{contract['filename']}' and all associated data deleted permanently."
    }


# ══════════════════════════════════════════════════════════════════
# BULK DELETE
# ══════════════════════════════════════════════════════════════════

async def bulk_delete_contracts(
    contract_ids: List[str],
    current_user: dict
) -> dict:
    """
    Deletes multiple contracts in a single operation.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    deleted_count = 0
    failed_ids = []
    
    for cid in contract_ids:
        try:
            await delete_contract(cid, current_user)
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete contract {cid}: {e}")
            failed_ids.append(cid)
    
    logger.info(
        f"Bulk delete | "
        f"requested={len(contract_ids)}, "
        f"deleted={deleted_count}, "
        f"failed={len(failed_ids)}"
    )
    
    return {
        "requested": len(contract_ids),
        "deleted": deleted_count,
        "failed": len(failed_ids),
        "failed_ids": failed_ids,
        "message": f"Successfully deleted {deleted_count} of {len(contract_ids)} contracts."
    }