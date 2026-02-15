# app/controllers/signature_controller.py

from fastapi import HTTPException, status, Request
from app.config.database import get_database
from app.services.signature_service import (
    generate_rsa_key_pair,
    sign_document,
    verify_document_signature,
    build_signature_record,
    append_audit_event
)
from app.services.storage_service import download_file_bytes
from app.utils.email_utils import send_countersign_request_email
from app.models.signature_model import CountersignRequestPayload
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional
import secrets
import logging

logger = logging.getLogger("legalyze.signature")


# ══════════════════════════════════════════════════════════════════
# SIGN CONTRACT
# ══════════════════════════════════════════════════════════════════

async def sign_contract(
    contract_id: str,
    version_id: Optional[str],
    current_user: dict,
    request: Optional[Request] = None
) -> dict:
    """
    Digitally signs a generated contract using RSA-PSS + SHA-256.
    
    Process:
    1. Fetch/generate user's RSA key pair
    2. Download contract file from S3
    3. Compute SHA-256 hash
    4. Sign hash with private key
    5. Store signature metadata in MongoDB
    6. Update contract signature status
    
    Returns:
        Signature metadata including hash and timestamp
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
    
    # Determine which version to sign (latest if not specified)
    if version_id:
        gen_contract = await db["generated_contracts"].find_one({
            "_id": ObjectId(version_id),
            "contract_id": contract_id,
            "user_id": user_id
        })
    else:
        # Get latest version
        gen_contract = await db["generated_contracts"].find_one(
            {"contract_id": contract_id, "user_id": user_id},
            sort=[("generated_at", -1)]
        )
    
    if not gen_contract:
        raise HTTPException(
            status_code=404,
            detail="No generated contract version found. Please generate a contract first."
        )
    
    version_id = str(gen_contract["_id"])
    
    # Check if already signed
    existing_sig = await db["signatures"].find_one({
        "contract_id": contract_id,
        "version_id": version_id,
        "signer.user_id": user_id,
        "status": {"$ne": "revoked"}
    })
    
    if existing_sig:
        raise HTTPException(
            status_code=409,
            detail="You have already signed this contract version. Revoke the existing signature first if you need to re-sign."
        )
    
    logger.info(
        f"Signing contract | "
        f"contract_id={contract_id}, version_id={version_id}, user={user_id}"
    )
    
    # Get or generate RSA keys for user
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    if not user.get("rsa_private_key"):
        logger.info(f"Generating RSA key pair for user {user_id}")
        private_pem, public_pem = generate_rsa_key_pair()
        
        await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "rsa_private_key": private_pem,
                    "rsa_public_key": public_pem
                }
            }
        )
    else:
        private_pem = user["rsa_private_key"]
        public_pem = user["rsa_public_key"]
    
    # Download contract file
    try:
        file_bytes = await download_file_bytes(gen_contract["cloud_url"])
    except Exception as e:
        logger.error(f"Failed to download contract file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to access contract file for signing."
        )
    
    # Sign the document
    try:
        signature_b64, document_hash = sign_document(file_bytes, private_pem)
    except Exception as e:
        logger.error(f"Signing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Digital signature creation failed: {str(e)}"
        )
    
    # Get client info
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    
    # Build signature record
    signature_doc = build_signature_record(
        contract_id=contract_id,
        version_id=version_id,
        user={
            "sub": user_id,
            "name": user.get("name", ""),
            "email": user.get("email", "")
        },
        signature_b64=signature_b64,
        document_hash=document_hash,
        public_key_pem=public_pem,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Store signature
    result = await db["signatures"].insert_one(signature_doc)
    signature_id = str(result.inserted_id)
    
    # Update generated contract status
    await db["generated_contracts"].update_one(
        {"_id": ObjectId(version_id)},
        {"$set": {"is_signed": True}}
    )
    
    # Update main contract signature status
    await db["contracts"].update_one(
        {"_id": ObjectId(contract_id)},
        {
            "$set": {
                "signature_status.is_signed": True,
                "signature_status.signed_by": user_id,
                "signature_status.signed_at": signature_doc["signed_at"],
                "signature_status.is_verified": True,
                "signature_status.is_revoked": False
            }
        }
    )
    
    logger.info(
        f"Contract signed successfully | "
        f"signature_id={signature_id}, hash={document_hash[:16]}..."
    )
    
    return {
        "id": signature_id,
        "contract_id": contract_id,
        "version_id": version_id,
        "signer": signature_doc["signer"],
        "crypto": signature_doc["crypto"],
        "status": "signed",
        "signed_at": signature_doc["signed_at"],
        "expires_at": None,
        "countersignatures": [],
        "message": "Contract signed successfully."
    }


# ══════════════════════════════════════════════════════════════════
# VERIFY SIGNATURE
# ══════════════════════════════════════════════════════════════════

async def verify_contract_signature(
    contract_id: str,
    version_id: Optional[str],
    current_user: dict,
    request: Optional[Request] = None
) -> dict:
    """
    Verifies the digital signature of a contract.
    
    Verification checks:
    1. Signature exists and is not revoked
    2. Document hash matches original
    3. RSA signature is cryptographically valid
    4. No tampering detected
    
    Returns:
        Verification status and details
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Find signature
    query = {"contract_id": contract_id}
    if version_id:
        query["version_id"] = version_id
    
    signature_doc = await db["signatures"].find_one(
        query,
        sort=[("signed_at", -1)]
    )
    
    if not signature_doc:
        return {
            "contract_id": contract_id,
            "version_id": version_id,
            "is_valid": False,
            "verification_outcome": "not_found",
            "verification_message": "No signature found for this contract.",
            "signed_by_name": None,
            "signed_by_email": None,
            "signed_at": None,
            "document_hash_at_signing": None,
            "current_document_hash": None,
            "hashes_match": None,
            "verified_at": datetime.utcnow()
        }
    
    # Check if revoked
    if signature_doc.get("is_revoked"):
        return {
            "contract_id": contract_id,
            "version_id": signature_doc.get("version_id"),
            "is_valid": False,
            "verification_outcome": "revoked",
            "verification_message": f"Signature was revoked on {signature_doc.get('revoked_at')}.",
            "signed_by_name": signature_doc["signer"]["name"],
            "signed_by_email": signature_doc["signer"]["email"],
            "signed_at": signature_doc["signed_at"],
            "document_hash_at_signing": signature_doc["crypto"]["document_hash"],
            "current_document_hash": None,
            "hashes_match": None,
            "verified_at": datetime.utcnow()
        }
    
    # Check expiry
    if signature_doc.get("expires_at"):
        if datetime.utcnow() > signature_doc["expires_at"]:
            return {
                "contract_id": contract_id,
                "version_id": signature_doc.get("version_id"),
                "is_valid": False,
                "verification_outcome": "expired",
                "verification_message": f"Signature expired on {signature_doc['expires_at']}.",
                "signed_by_name": signature_doc["signer"]["name"],
                "signed_by_email": signature_doc["signer"]["email"],
                "signed_at": signature_doc["signed_at"],
                "document_hash_at_signing": signature_doc["crypto"]["document_hash"],
                "current_document_hash": None,
                "hashes_match": None,
                "verified_at": datetime.utcnow()
            }
    
    # Download current file
    gen_contract = await db["generated_contracts"].find_one({
        "_id": ObjectId(signature_doc["version_id"])
    })
    
    if not gen_contract:
        raise HTTPException(
            status_code=404,
            detail="Contract file not found."
        )
    
    try:
        file_bytes = await download_file_bytes(gen_contract["cloud_url"])
    except Exception as e:
        logger.error(f"Failed to download contract for verification: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to access contract file for verification."
        )
    
    # Get signer's public key
    signer = await db["users"].find_one({
        "_id": ObjectId(signature_doc["signer"]["user_id"])
    })
    
    if not signer or not signer.get("rsa_public_key"):
        raise HTTPException(
            status_code=500,
            detail="Signer's public key not found. Cannot verify signature."
        )
    
    # Verify signature
    is_valid, current_hash, outcome = verify_document_signature(
        content=file_bytes,
        signature_b64=signature_doc["crypto"]["signature_b64"],
        public_key_pem=signer["rsa_public_key"],
        original_hash=signature_doc["crypto"]["document_hash"]
    )
    
    # Log verification event
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None
    
    signature_doc = append_audit_event(
        signature_doc=signature_doc,
        event_type="verified",
        user=current_user,
        outcome="success" if is_valid else "failure",
        metadata={
            "verification_outcome": outcome,
            "current_hash": current_hash
        },
        ip_address=ip_address
    )
    
    # Update signature record
    await db["signatures"].update_one(
        {"_id": signature_doc["_id"]},
        {"$set": {"audit_events": signature_doc["audit_events"]}}
    )
    
    # Build response message
    messages = {
        "valid": "Signature is valid. Document has not been tampered with.",
        "tampered": "Document has been modified since signing. Hash mismatch detected.",
        "invalid_signature": "Signature verification failed. Digital signature is invalid.",
        "error": "Verification error occurred."
    }
    
    logger.info(
        f"Signature verified | "
        f"contract_id={contract_id}, outcome={outcome}, valid={is_valid}"
    )
    
    return {
        "contract_id": contract_id,
        "version_id": signature_doc.get("version_id"),
        "is_valid": is_valid,
        "verification_outcome": outcome,
        "verification_message": messages.get(outcome, "Unknown outcome."),
        "signed_by_name": signature_doc["signer"]["name"],
        "signed_by_email": signature_doc["signer"]["email"],
        "signed_at": signature_doc["signed_at"],
        "document_hash_at_signing": signature_doc["crypto"]["document_hash"],
        "current_document_hash": current_hash,
        "hashes_match": (current_hash == signature_doc["crypto"]["document_hash"]),
        "verified_at": datetime.utcnow()
    }


# ══════════════════════════════════════════════════════════════════
# GET SIGNATURE INFO
# ══════════════════════════════════════════════════════════════════

async def get_signature_info(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Returns signature metadata for a contract without performing verification.
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
    
    # Get latest signature
    signature_doc = await db["signatures"].find_one(
        {"contract_id": contract_id},
        sort=[("signed_at", -1)]
    )
    
    if not signature_doc:
        return {
            "contract_id": contract_id,
            "has_signature": False,
            "status": "unsigned",
            "signer": None,
            "algorithm": None,
            "document_hash": None,
            "signed_at": None,
            "is_verified": False,
            "last_verified_at": None,
            "countersignatures": [],
            "total_countersigners": 0,
            "pending_countersigners": 0,
            "all_parties_signed": False
        }
    
    # Count countersignatures
    countersigs = signature_doc.get("countersignatures", [])
    pending = sum(1 for cs in countersigs if cs["status"] == "pending")
    signed = sum(1 for cs in countersigs if cs["status"] == "signed")
    all_signed = (pending == 0 and len(countersigs) > 0)
    
    return {
        "contract_id": contract_id,
        "version_id": signature_doc.get("version_id"),
        "has_signature": True,
        "status": signature_doc["status"],
        "signer": signature_doc["signer"],
        "algorithm": signature_doc["crypto"]["algorithm"],
        "document_hash": signature_doc["crypto"]["document_hash"],
        "signed_at": signature_doc["signed_at"],
        "is_verified": not signature_doc.get("is_revoked", False),
        "last_verified_at": None,  # Would need to parse audit events
        "countersignatures": countersigs,
        "total_countersigners": len(countersigs),
        "pending_countersigners": pending,
        "all_parties_signed": all_signed
    }


# ══════════════════════════════════════════════════════════════════
# GET SIGNATURE HISTORY
# ══════════════════════════════════════════════════════════════════

async def get_signature_history(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Returns the complete audit trail of all signature events.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    contract = await db["contracts"].find_one({
        "_id": ObjectId(contract_id),
        "user_id": user_id
    })
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    
    signature_doc = await db["signatures"].find_one(
        {"contract_id": contract_id},
        sort=[("signed_at", -1)]
    )
    
    if not signature_doc:
        return {
            "contract_id": contract_id,
            "total_events": 0,
            "events": [],
            "first_signed_at": None,
            "last_activity_at": None
        }
    
    events = signature_doc.get("audit_events", [])
    
    return {
        "contract_id": contract_id,
        "total_events": len(events),
        "events": events,
        "first_signed_at": signature_doc["signed_at"],
        "last_activity_at": events[-1]["timestamp"] if events else signature_doc["signed_at"]
    }


# ══════════════════════════════════════════════════════════════════
# REQUEST COUNTERSIGNATURE
# ══════════════════════════════════════════════════════════════════

async def request_countersign(
    contract_id: str,
    payload: CountersignRequestPayload,
    current_user: dict
) -> dict:
    """
    Sends a countersignature request to another party.
    
    Process:
    1. Verify primary signer has already signed
    2. Generate secure invitation token
    3. Create countersignature record
    4. Send email invitation
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Get signature
    signature_doc = await db["signatures"].find_one({
        "contract_id": contract_id,
        "signer.user_id": user_id,
        "status": "signed"
    })
    
    if not signature_doc:
        raise HTTPException(
            status_code=400,
            detail="You must sign the contract before requesting countersignatures."
        )
    
    # Check if already requested from this email
    existing = next(
        (
            cs for cs in signature_doc.get("countersignatures", [])
            if cs["party_email"] == payload.counterparty_email
        ),
        None
    )
    
    if existing and existing["status"] == "pending":
        raise HTTPException(
            status_code=409,
            detail=f"A pending countersignature request already exists for {payload.counterparty_email}."
        )
    
    # Generate invitation token
    invite_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=payload.expiry_hours)
    
    # Create countersignature record
    countersig = {
        "party_email": payload.counterparty_email,
        "party_name": payload.counterparty_name,
        "status": "pending",
        "invited_at": datetime.utcnow(),
        "signed_at": None,
        "declined_at": None,
        "expires_at": expires_at,
        "signature_hash": None,
        "decline_reason": None,
        "invite_token": invite_token
    }
    
    # Add to signature document
    await db["signatures"].update_one(
        {"_id": signature_doc["_id"]},
        {"$push": {"countersignatures": countersig}}
    )
    
    # Send email invitation
    try:
        await send_countersign_request_email(
            to_email=payload.counterparty_email,
            to_name=payload.counterparty_name or payload.counterparty_email,
            from_name=current_user.get("name", "A party"),
            contract_id=contract_id,
            invite_token=invite_token,
            expires_hours=payload.expiry_hours,
            personal_message=payload.message
        )
        
        logger.info(
            f"Countersign request sent | "
            f"contract_id={contract_id}, to={payload.counterparty_email}"
        )
    
    except Exception as e:
        logger.error(f"Failed to send countersign email: {e}")
        # Don't fail the request, just log
    
    return {
        "success": True,
        "contract_id": contract_id,
        "counterparty_email": payload.counterparty_email,
        "status": "pending",
        "invited_at": countersig["invited_at"],
        "expires_at": expires_at,
        "message": f"Countersignature request sent to {payload.counterparty_email}."
    }


# ══════════════════════════════════════════════════════════════════
# GET COUNTERSIGN STATUS
# ══════════════════════════════════════════════════════════════════

async def get_countersign_status(
    contract_id: str,
    current_user: dict
) -> dict:
    """
    Returns the status of all countersignature requests.
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    signature_doc = await db["signatures"].find_one({
        "contract_id": contract_id,
        "signer.user_id": user_id
    })
    
    if not signature_doc:
        raise HTTPException(
            status_code=404,
            detail="No signature found for this contract."
        )
    
    countersigs = signature_doc.get("countersignatures", [])
    
    # Count by status
    total_requested = len(countersigs)
    total_signed = sum(1 for cs in countersigs if cs["status"] == "signed")
    total_pending = sum(1 for cs in countersigs if cs["status"] == "pending")
    total_declined = sum(1 for cs in countersigs if cs["status"] == "declined")
    total_expired = sum(1 for cs in countersigs if cs["status"] == "expired")
    
    all_signed = (total_pending == 0 and total_requested > 0 and total_signed == total_requested)
    
    return {
        "contract_id": contract_id,
        "total_requested": total_requested,
        "total_signed": total_signed,
        "total_pending": total_pending,
        "total_declined": total_declined,
        "total_expired": total_expired,
        "all_signed": all_signed,
        "parties": countersigs,
        "computed_at": datetime.utcnow()
    }


# ══════════════════════════════════════════════════════════════════
# REVOKE SIGNATURE
# ══════════════════════════════════════════════════════════════════

async def revoke_signature(
    contract_id: str,
    reason: Optional[str],
    current_user: dict,
    request: Optional[Request] = None
) -> dict:
    """
    Revokes a digital signature.
    
    Effects:
    - Signature status set to 'revoked'
    - All countersignatures invalidated
    - Logged in audit trail
    - Contract must be re-signed before distribution
    """
    
    db = get_database()
    user_id = current_user["sub"]
    
    # Find signature
    signature_doc = await db["signatures"].find_one({
        "contract_id": contract_id,
        "signer.user_id": user_id,
        "status": {"$ne": "revoked"}
    })
    
    if not signature_doc:
        raise HTTPException(
            status_code=404,
            detail="No active signature found for this contract."
        )
    
    previous_status = signature_doc["status"]
    
    # Get IP address
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None
    
    # Log revocation event
    signature_doc = append_audit_event(
        signature_doc=signature_doc,
        event_type="revoked",
        user=current_user,
        outcome="success",
        metadata={"reason": reason or "No reason provided"},
        notes=reason,
        ip_address=ip_address
    )
    
    # Count countersignatures being invalidated
    countersig_count = len([
        cs for cs in signature_doc.get("countersignatures", [])
        if cs["status"] == "signed"
    ])
    
    # Update signature
    await db["signatures"].update_one(
        {"_id": signature_doc["_id"]},
        {
            "$set": {
                "status": "revoked",
                "is_revoked": True,
                "revoked_at": datetime.utcnow(),
                "revoked_reason": reason,
                "audit_events": signature_doc["audit_events"]
            }
        }
    )
    
    # Update contract status
    await db["contracts"].update_one(
        {"_id": ObjectId(contract_id)},
        {
            "$set": {
                "signature_status.is_revoked": True,
                "signature_status.is_verified": False
            }
        }
    )
    
    # Update generated contract
    if signature_doc.get("version_id"):
        await db["generated_contracts"].update_one(
            {"_id": ObjectId(signature_doc["version_id"])},
            {"$set": {"is_signed": False}}
        )
    
    logger.info(
        f"Signature revoked | "
        f"contract_id={contract_id}, reason={reason}"
    )
    
    return {
        "contract_id": contract_id,
        "previous_status": previous_status,
        "new_status": "revoked",
        "revoked_by_email": current_user.get("email"),
        "revoked_at": datetime.utcnow(),
        "reason": reason,
        "countersignatures_invalidated": countersig_count,
        "message": (
            f"Signature revoked successfully. "
            f"{countersig_count} countersignature(s) invalidated."
        )
    }