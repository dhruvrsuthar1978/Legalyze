# app/routes/signature_routes.py

from fastapi import (
    APIRouter, HTTPException,
    Depends, status, Query
)
from typing import Optional
from app.controllers.signature_controller import (
    sign_contract,
    verify_contract_signature,
    get_signature_info,
    revoke_signature,
    get_signature_history,
    request_countersign,
    get_countersign_status
)
from app.models.signature_model import (
    SignatureResponse,
    VerifySignatureResponse,
    SignatureInfoResponse,
    SignatureHistoryResponse,
    CountersignRequestPayload,
    CountersignStatusResponse
)
from app.middleware.auth_middleware import verify_token

router = APIRouter(
    prefix="/signatures",
    tags=["✍️ Digital Signatures"]
)


# ══════════════════════════════════════════════════════
# @route    POST /api/signatures/{contract_id}/sign
# @desc     Digitally sign a contract (RSA + SHA-256)
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/{contract_id}/sign",
    response_model=SignatureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Digitally sign a contract using RSA + SHA-256",
    description="""
    Applies a **cryptographic digital signature** to the specified contract.
    
    **Signing Process:**
    1. SHA-256 hash computed from contract file content (integrity fingerprint)
    2. Hash encrypted using the user's **RSA-2048 private key**
    3. Signature stored in MongoDB with signer identity and timestamp
    4. Contract marked as `signed` in the database
    
    **Security Guarantees:**
    - **Integrity** — Any document modification invalidates the signature
    - **Authenticity** — Only the private key holder can generate a valid signature
    - **Non-repudiation** — Signer cannot deny having signed the document
    
    **Note:** A generated contract version must exist before signing.
    Use `/api/generate/{contract_id}` first.
    """
)
async def sign(
    contract_id: str,
    version_id: Optional[str] = Query(
        None,
        description="Specific generated version to sign. Signs latest version if omitted."
    ),
    current_user: dict = Depends(verify_token)
):
    return await sign_contract(contract_id, version_id, current_user)


# ══════════════════════════════════════════════════════
# @route    POST /api/signatures/{contract_id}/verify
# @desc     Verify the digital signature of a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/{contract_id}/verify",
    response_model=VerifySignatureResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify digital signature of a contract",
    description="""
    Cryptographically verifies the digital signature of the contract.
    
    **Verification Process:**
    1. Fetches stored signature hash and signer's public key
    2. Recomputes SHA-256 hash of the current document content
    3. Decrypts stored signature with signer's RSA public key
    4. Compares hashes — match = valid, mismatch = tampered
    
    **Possible Verification Outcomes:**
    - `valid` — Document is authentic and unmodified
    - `invalid` — Document has been tampered with
    - `expired` — Signature has passed its validity period
    - `revoked` — Signature was manually revoked by the signer
    - `not_found` — No signature exists for this contract
    """
)
async def verify_signature(
    contract_id: str,
    version_id: Optional[str] = Query(
        None,
        description="Specific version to verify. Verifies latest version if omitted."
    ),
    current_user: dict = Depends(verify_token)
):
    return await verify_contract_signature(contract_id, version_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/signatures/{contract_id}
# @desc     Get signature metadata for a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}",
    response_model=SignatureInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get digital signature details for a contract",
    description="""
    Returns the full digital signature metadata for a contract including:
    
    - Signer identity (user ID + email)
    - Signature hash (SHA-256 + RSA encoded)
    - Signing timestamp
    - Current verification status
    - Countersignature details (if applicable)
    """
)
async def get_signature(
    contract_id: str,
    current_user: dict = Depends(verify_token)
):
    return await get_signature_info(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/signatures/{contract_id}/history
# @desc     Get full signature audit trail for a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/history",
    response_model=SignatureHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full signature audit trail",
    description="""
    Returns the complete **audit history** of all signature events
    for a contract, including:
    
    - All sign, verify, revoke events in chronological order
    - Timestamps and actor (user ID + email) for each event
    - IP address and device info (if available)
    - Event outcome (success / failure)
    
    Useful for compliance, audit trails, and dispute resolution.
    """
)
async def get_history(
    contract_id: str,
    current_user: dict = Depends(verify_token)
):
    return await get_signature_history(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    POST /api/signatures/{contract_id}/countersign/request
# @desc     Request countersignature from another party
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/{contract_id}/countersign/request",
    status_code=status.HTTP_201_CREATED,
    summary="Request a countersignature from another party",
    description="""
    Sends a **countersignature request** to another user by email.
    
    **Flow:**
    1. Requester submits the counterparty's email
    2. System sends a signing invitation email with a secure link
    3. Counterparty signs using their own credentials
    4. Both signatures are stored and linked to the contract
    
    **Body:**
```json
    {
      "counterparty_email": "other@example.com",
      "message": "Please review and sign the attached NDA."
    }
```
    
    **Note:** The contract must already be signed by the requester.
    """
)
async def request_countersignature(
    contract_id: str,
    payload: CountersignRequestPayload,
    current_user: dict = Depends(verify_token)
):
    return await request_countersign(contract_id, payload, current_user)


# ══════════════════════════════════════════════════════
# @route    GET /api/signatures/{contract_id}/countersign/status
# @desc     Get countersignature request status
# @access   Private
# ══════════════════════════════════════════════════════
@router.get(
    "/{contract_id}/countersign/status",
    response_model=CountersignStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check the status of a countersignature request",
    description="""
    Returns the current status of a pending countersignature request:
    
    - `pending` — Invitation sent, awaiting counterparty action
    - `signed` — Counterparty has signed the document
    - `declined` — Counterparty declined to sign
    - `expired` — Invitation link expired (after 72 hours)
    """
)
async def countersign_status(
    contract_id: str,
    current_user: dict = Depends(verify_token)
):
    return await get_countersign_status(contract_id, current_user)


# ══════════════════════════════════════════════════════
# @route    DELETE /api/signatures/{contract_id}/revoke
# @desc     Revoke a digital signature from a contract
# @access   Private
# ══════════════════════════════════════════════════════
@router.delete(
    "/{contract_id}/revoke",
    status_code=status.HTTP_200_OK,
    summary="Revoke the digital signature on a contract",
    description="""
    Revokes the digital signature applied to a contract.
    
    **Effect:**
    - Signature status is set to `revoked`
    - Contract verification will return `revoked` status
    - The document must be re-signed before redistribution
    - Revocation is logged in the signature audit trail
    
    **Use Cases:**
    - Contract terms need to be renegotiated
    - Signer identity was compromised
    - Signing was done in error
    
    ⚠️ **Countersignatures are also invalidated upon revocation.**
    """
)
async def revoke(
    contract_id: str,
    reason: Optional[str] = Query(
        None,
        description="Optional reason for revocation (logged in audit trail)"
    ),
    current_user: dict = Depends(verify_token)
):
    return await revoke_signature(contract_id, reason, current_user)