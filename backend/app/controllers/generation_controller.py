# app/controllers/generation_controller.py

from fastapi import HTTPException, status, BackgroundTasks
from app.config.database import get_database
from app.services.generation_service import generate_contract_document
from app.services.contract_template_service import (
    list_templates,
    render_template_preview
)
from app.services.storage_service import (
    upload_to_cloud,
    get_download_url,
    delete_from_cloud
)
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional
import logging

logger = logging.getLogger("legalyze.generation")


# ══════════════════════════════════════════════════════════════════
# GENERATE CONTRACT
# ══════════════════════════════════════════════════════════════════

async def generate_contract(
    contract_id: str,
    format: str,
    include_summary: bool,
    current_user: dict,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Generates a new AI-reviewed contract with accepted suggestions applied.
    
    Steps:
    1. Fetch contract and analysis
    2. Filter accepted/edited clauses
    3. Generate PDF/DOCX document
    4. Upload to S3
    5. Create version record in MongoDB
    6. Return download link
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Fetch contract
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
            status_code=404,
            detail="Analysis not found. Please run analysis first."
        )
    
    # Get accepted/edited clauses
    accepted_clauses = [
        c for c in analysis["clauses"]
        if c.get("suggestion_status") in ["accepted", "edited"]
    ]
    
    if not accepted_clauses:
        logger.warning(
            f"No accepted suggestions for contract {contract_id}. "
            f"Generating original contract."
        )
    
    logger.info(
        f"Generating contract | "
        f"id={contract_id}, format={format}, "
        f"accepted_suggestions={len(accepted_clauses)}"
    )
    
    # Determine version number
    existing_versions = await db["generated_contracts"].count_documents({
        "contract_id": contract_id
    })
    version = existing_versions + 1
    
    try:
        # Generate document
        file_bytes, filename, file_size = generate_contract_document(
            original_contract=contract,
            clauses=analysis["clauses"],
            accepted_clauses=accepted_clauses,
            format=format,
            include_summary=include_summary,
            version=version
        )
        
        # Upload to S3
        cloud_url = await upload_to_cloud(
            contents=file_bytes,
            filename=filename,
            user_id=user_id,
            subfolder="generated"
        )
        
        # Create version record
        generated_doc = {
            "contract_id": contract_id,
            "user_id": user_id,
            "version": version,
            "format": format,
            "filename": filename,
            "file_size_kb": file_size,
            "cloud_url": cloud_url,
            "total_clauses": len(analysis["clauses"]),
            "applied_suggestions_count": len(accepted_clauses),
            "applied_suggestions": [
                {
                    "clause_id": c["clause_id"],
                    "clause_type": c["clause_type"],
                    "original_text": c["original_text"],
                    "replacement_text": (
                        c.get("edited_suggestion") or c.get("suggestion")
                    ),
                    "accepted_at": c.get("updated_at") or datetime.utcnow()
                }
                for c in accepted_clauses
            ],
            "includes_summary_page": include_summary,
            "is_signed": False,
            "generated_at": datetime.utcnow()
        }
        
        result = await db["generated_contracts"].insert_one(generated_doc)
        version_id = str(result.inserted_id)
        
        # Generate download URL
        download_url = await get_download_url(cloud_url, expiry_minutes=30)
        
        logger.info(
            f"Contract generated | "
            f"version_id={version_id}, size={file_size}KB"
        )
        
        return {
            "id": version_id,
            "contract_id": contract_id,
            "user_id": user_id,
            "version": version,
            "format": format,
            "filename": filename,
            "file_size_kb": file_size,
            "download_url": download_url,
            "url_expires_at": datetime.utcnow() + timedelta(minutes=30),
            "total_clauses": generated_doc["total_clauses"],
            "applied_suggestions_count": len(accepted_clauses),
            "applied_suggestions": generated_doc["applied_suggestions"],
            "includes_summary_page": include_summary,
            "is_signed": False,
            "generated_at": generated_doc["generated_at"],
            "message": f"Contract v{version} generated successfully."
        }
    
    except Exception as e:
        logger.error(f"Contract generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate contract: {str(e)}"
        )


# ══════════════════════════════════════════════════════════════════
# PREVIEW GENERATED CONTRACT
# ══════════════════════════════════════════════════════════════════

async def preview_generated_contract(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Returns a text preview of what the generated contract will look like
    without actually creating a file.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    contract = await db["contracts"].find_one({
        "_id": ObjectId(contract_id),
        "user_id": user_id
    })
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    
    analysis = await db["analyses"].find_one({"contract_id": contract_id})
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    # Get accepted clauses
    accepted = [
        c for c in analysis["clauses"]
        if c.get("suggestion_status") in ["accepted", "edited"]
    ]
    
    # Build preview text
    preview_parts = []
    changes = []
    
    for clause in analysis["clauses"]:
        is_replaced = clause.get("suggestion_status") in ["accepted", "edited"]
        
        if is_replaced:
            replacement = (
                clause.get("edited_suggestion") or clause.get("suggestion")
            )
            preview_parts.append(f"[✦ AI-IMPROVED] {replacement}")
            
            changes.append({
                "clause_type": clause["clause_type"],
                "original": clause["original_text"][:200] + "...",
                "replacement": replacement[:200] + "..."
            })
        else:
            preview_parts.append(clause["original_text"])
    
    preview_text = "\n\n".join(preview_parts)
    
    # Estimate pages (300 words per page)
    word_count = len(preview_text.split())
    estimated_pages = max(1, word_count // 300)
    
    pending_count = sum(
        1 for c in analysis["clauses"]
        if c.get("suggestion_status") == "pending"
    )
    
    return {
        "contract_id": contract_id,
        "preview_text": preview_text[:5000],  # First 5000 chars
        "changes": changes,
        "total_changes": len(changes),
        "estimated_pages": estimated_pages,
        "pending_suggestions": pending_count,
        "generated_at": datetime.utcnow()
    }


async def generate_adhoc_preview(payload: dict, current_user: dict) -> dict:
    """Generate a preview for an ad-hoc contract built from user inputs.

    Payload expected fields: contract_type, party1, party2, duration, requirements
    """
    try:
        contract_type = payload.get("contract_type", "agreement")
        party1 = payload.get("party1_name", "Party 1")
        party2 = payload.get("party2_name", "Party 2")
        duration = payload.get("duration", "")
        requirements = payload.get("requirements", "")

        # Build a pseudo-original contract
        original_contract = {
            "filename": f"adhoc_{contract_type}.txt",
            "title": f"Adhoc {contract_type}",
            "category": contract_type,
            "uploaded_at": datetime.utcnow(),
        }

        # Create a single 'clause' from requirements to include in document
        clauses = []
        if requirements:
            clauses.append({
                "clause_id": "req-1",
                "clause_type": "custom_requirements",
                "original_text": requirements,
                "suggestion_status": "pending"
            })

        # Use generation_service to build document bytes for preview, but we only return text preview
        from app.services.generation_service import generate_contract_document

        file_bytes, filename, file_size = generate_contract_document(
            original_contract=original_contract,
            clauses=clauses,
            accepted_clauses=[],
            format="pdf",
            include_summary=False,
            version=1
        )

        # For preview, return a simple text summary
        preview_text = f"Adhoc {contract_type} between {party1} and {party2}. Duration: {duration or 'Indefinite'}.\n\nRequirements:\n{requirements}\n"

        return {
            "preview_text": preview_text,
            "filename": filename,
            "estimated_pages": max(1, len(preview_text.split()) // 300)
        }
    except Exception as e:
        raise Exception(f"Adhoc generation preview failed: {e}")


async def list_contract_templates(current_user: dict) -> dict:
    """Return supported contract templates for guided draft generation."""
    return {"templates": list_templates()}


async def preview_template_contract(payload: dict, current_user: dict) -> dict:
    """
    Build a template-based contract preview from structured user fields.

    Expected payload:
    {
      "template_id": "...",
      "data": { ... template fields ... }
    }
    """
    template_id = payload.get("template_id")
    data = payload.get("data", {}) or {}

    if not template_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="template_id is required."
        )

    try:
        return render_template_preview(template_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc


# ══════════════════════════════════════════════════════════════════
# LIST GENERATED VERSIONS
# ══════════════════════════════════════════════════════════════════

async def list_generated_versions(
    contract_id: str,
    page: int,
    limit: int,
    current_user: dict
) -> dict:
    """
    Returns all generated versions for a contract.
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
    
    # Count total
    total = await db["generated_contracts"].count_documents({
        "contract_id": contract_id
    })
    
    # Fetch paginated
    skip = (page - 1) * limit
    cursor = db["generated_contracts"].find({
        "contract_id": contract_id
    }).sort("generated_at", -1).skip(skip).limit(limit)
    
    versions = await cursor.to_list(length=limit)
    
    # Build response
    version_list = []
    for v in versions:
        # Generate fresh download URL
        download_url = None
        if v.get("cloud_url"):
            try:
                download_url = await get_download_url(
                    v["cloud_url"],
                    expiry_minutes=30
                )
            except Exception as e:
                logger.warning(f"Failed to generate download URL: {e}")
        
        version_list.append({
            "id": str(v["_id"]),
            "contract_id": contract_id,
            "version": v["version"],
            "format": v["format"],
            "filename": v["filename"],
            "file_size_kb": v.get("file_size_kb"),
            "download_url": download_url,
            "url_expires_at": (
                datetime.utcnow() + timedelta(minutes=30)
                if download_url else None
            ),
            "applied_suggestions_count": v.get("applied_suggestions_count", 0),
            "is_signed": v.get("is_signed", False),
            "generated_at": v["generated_at"]
        })
    
    return {
        "contract_id": contract_id,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "versions": version_list
    }


# ══════════════════════════════════════════════════════════════════
# GET SPECIFIC VERSION
# ══════════════════════════════════════════════════════════════════

async def get_generated_contract(
    contract_id: str,
    version_id: str,
    current_user: dict
) -> dict:
    """
    Fetches a specific generated contract version.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    version = await db["generated_contracts"].find_one({
        "_id": ObjectId(version_id),
        "contract_id": contract_id,
        "user_id": user_id
    })
    
    if not version:
        raise HTTPException(
            status_code=404,
            detail="Generated contract version not found."
        )
    
    # Generate download URL
    download_url = None
    if version.get("cloud_url"):
        download_url = await get_download_url(
            version["cloud_url"],
            expiry_minutes=30
        )
    
    version["id"] = str(version.pop("_id"))
    version["download_url"] = download_url
    version["url_expires_at"] = (
        datetime.utcnow() + timedelta(minutes=30)
        if download_url else None
    )
    
    return version


# ══════════════════════════════════════════════════════════════════
# DOWNLOAD VERSION
# ══════════════════════════════════════════════════════════════════

async def download_generated_contract(
    contract_id: str,
    version_id: str,
    current_user: dict
) -> dict:
    """
    Generates a download URL for a specific version.
    """
    
    db = get_database()
    version = await get_generated_contract(contract_id, version_id, current_user)
    
    if not version.get("download_url"):
        raise HTTPException(
            status_code=404,
            detail="File not found in storage."
        )
    
    return {
        "version_id": version_id,
        "contract_id": contract_id,
        "filename": version["filename"],
        "download_url": version["download_url"],
        "expires_in_minutes": 30
    }


# ══════════════════════════════════════════════════════════════════
# DELETE VERSION
# ══════════════════════════════════════════════════════════════════

async def delete_generated_version(
    contract_id: str,
    version_id: str,
    current_user: dict
) -> dict:
    """
    Deletes a specific generated version.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    version = await db["generated_contracts"].find_one({
        "_id": ObjectId(version_id),
        "contract_id": contract_id,
        "user_id": user_id
    })
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found.")
    
    # Delete from S3
    if version.get("cloud_url"):
        await delete_from_cloud(version["cloud_url"])
    
    # Delete record
    await db["generated_contracts"].delete_one({"_id": ObjectId(version_id)})
    
    logger.info(
        f"Generated version deleted | "
        f"version_id={version_id}, version={version['version']}"
    )
    
    return {
        "success": True,
        "message": f"Version {version['version']} deleted successfully."
    }
