# app/services/signature_service.py

import base64
import hashlib
import uuid
from datetime import datetime
from typing import Tuple, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey, RSAPublicKey
)
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import logging

logger = logging.getLogger("legalyze.signature")


# ══════════════════════════════════════════════════════════════════
# RSA KEY GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_rsa_key_pair() -> Tuple[str, str]:
    """
    Generates a new RSA-2048 key pair.

    Returns:
        Tuple of (private_key_pem_str, public_key_pem_str)

    Key storage note:
        - Private key: stored securely (encrypted) per user in MongoDB
        - Public key: stored openly alongside signature metadata
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key  = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    logger.debug("RSA-2048 key pair generated")
    return private_pem, public_pem


def load_private_key(pem_str: str) -> RSAPrivateKey:
    """Deserializes a PEM-encoded RSA private key."""
    return serialization.load_pem_private_key(
        pem_str.encode("utf-8"),
        password=None,
        backend=default_backend()
    )


def load_public_key(pem_str: str) -> RSAPublicKey:
    """Deserializes a PEM-encoded RSA public key."""
    return serialization.load_pem_public_key(
        pem_str.encode("utf-8"),
        backend=default_backend()
    )


# ══════════════════════════════════════════════════════════════════
# DOCUMENT HASHING
# ══════════════════════════════════════════════════════════════════

def compute_sha256_hash(content: bytes) -> str:
    """
    Computes the SHA-256 hash of document content.

    Returns:
        Hex-encoded SHA-256 digest string

    This hash is the document's integrity fingerprint.
    Any change to content produces a completely different hash.
    """
    digest = hashlib.sha256(content).hexdigest()
    logger.debug(f"Document SHA-256: {digest[:16]}...")
    return digest


def compute_public_key_fingerprint(public_pem: str) -> str:
    """
    Computes the SHA-256 fingerprint of a public key.
    Used for identifying the signer's key in audit records.
    """
    key_bytes = public_pem.encode("utf-8")
    return hashlib.sha256(key_bytes).hexdigest()


# ══════════════════════════════════════════════════════════════════
# SIGNING
# ══════════════════════════════════════════════════════════════════

def sign_document(
    content: bytes,
    private_key_pem: str
) -> Tuple[str, str]:
    """
    Digitally signs document content using RSA-PSS + SHA-256.

    Algorithm: RSA-PSS (Probabilistic Signature Scheme)
    - More secure than PKCS#1v1.5 (no deterministic padding)
    - SHA-256 for hash

    Args:
        content         : Raw document bytes
        private_key_pem : PEM-encoded RSA private key

    Returns:
        Tuple of (signature_b64, document_hash)
        - signature_b64: Base64-encoded RSA signature
        - document_hash: SHA-256 hex of document content
    """
    document_hash = compute_sha256_hash(content)

    private_key = load_private_key(private_key_pem)

    raw_signature = private_key.sign(
        content,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    signature_b64 = base64.b64encode(raw_signature).decode("utf-8")

    logger.info(
        f"Document signed successfully | "
        f"hash={document_hash[:16]}..., "
        f"sig_length={len(signature_b64)}"
    )

    return signature_b64, document_hash


# ══════════════════════════════════════════════════════════════════
# VERIFICATION
# ══════════════════════════════════════════════════════════════════

def verify_document_signature(
    content: bytes,
    signature_b64: str,
    public_key_pem: str,
    original_hash: str
) -> Tuple[bool, str, str]:
    """
    Verifies a digital signature against document content.

    Verification Steps:
        1. Decode Base64 signature
        2. Recompute SHA-256 of current document content
        3. Compare current hash with original hash (tamper detection)
        4. Verify RSA-PSS signature using signer's public key

    Returns:
        Tuple of (is_valid, current_hash, outcome_code)
        outcome_code: 'valid' | 'tampered' | 'invalid_signature' | 'error'
    """
    current_hash = compute_sha256_hash(content)

    # Step 1: Quick tamper check via hash comparison
    if current_hash != original_hash:
        logger.warning(
            f"Document TAMPERED | "
            f"original={original_hash[:16]}..., "
            f"current={current_hash[:16]}..."
        )
        return False, current_hash, "tampered"

    # Step 2: Cryptographic signature verification
    try:
        raw_signature = base64.b64decode(signature_b64)
        public_key    = load_public_key(public_key_pem)

        public_key.verify(
            raw_signature,
            content,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        logger.info(
            f"Signature VERIFIED | hash={current_hash[:16]}..."
        )
        return True, current_hash, "valid"

    except InvalidSignature:
        logger.warning("Signature verification FAILED — invalid signature")
        return False, current_hash, "invalid_signature"

    except Exception as e:
        logger.error(f"Signature verification ERROR: {e}")
        return False, current_hash, "error"


# ══════════════════════════════════════════════════════════════════
# SIGNATURE RECORD BUILDER
# ══════════════════════════════════════════════════════════════════

def build_signature_record(
    contract_id: str,
    version_id: Optional[str],
    user: dict,
    signature_b64: str,
    document_hash: str,
    public_key_pem: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> dict:
    """
    Builds the full signature document to be stored in MongoDB.

    Includes:
    - Signer identity and device info
    - Cryptographic details (algorithm, key size, hashes)
    - Audit event log entry
    """
    key_fingerprint = compute_public_key_fingerprint(public_key_pem)
    event_id        = str(uuid.uuid4())
    now             = datetime.utcnow()

    return {
        "contract_id": contract_id,
        "version_id":  version_id,
        "signer": {
            "user_id":    user["sub"],
            "name":       user.get("name", ""),
            "email":      user.get("email", ""),
            "ip_address": ip_address,
            "user_agent": user_agent
        },
        "crypto": {
            "algorithm":            "RSA-PSS + SHA-256",
            "key_size":             2048,
            "hash_algorithm":       "SHA-256",
            "document_hash":        document_hash,
            "signature_b64":        signature_b64,
            "public_key_fingerprint": key_fingerprint
        },
        "status":          "signed",
        "signed_at":       now,
        "expires_at":      None,
        "is_revoked":      False,
        "revoked_at":      None,
        "revoked_reason":  None,
        "countersignatures": [],
        "audit_events": [
            {
                "event_id":            event_id,
                "event_type":          "signed",
                "performed_by_user_id": user["sub"],
                "performed_by_email":  user.get("email", ""),
                "timestamp":           now,
                "ip_address":          ip_address,
                "outcome":             "success",
                "metadata":            {
                    "document_hash": document_hash,
                    "key_fingerprint": key_fingerprint
                },
                "notes": None
            }
        ]
    }


def append_audit_event(
    signature_doc: dict,
    event_type: str,
    user: dict,
    outcome: str,
    metadata: Optional[dict] = None,
    notes: Optional[str] = None,
    ip_address: Optional[str] = None
) -> dict:
    """
    Appends a new audit event to an existing signature document.
    Used for verify, revoke, and countersign events.
    """
    event = {
        "event_id":            str(uuid.uuid4()),
        "event_type":          event_type,
        "performed_by_user_id": user["sub"],
        "performed_by_email":  user.get("email", ""),
        "timestamp":           datetime.utcnow(),
        "ip_address":          ip_address,
        "outcome":             outcome,
        "metadata":            metadata or {},
        "notes":               notes
    }

    if "audit_events" not in signature_doc:
        signature_doc["audit_events"] = []

    signature_doc["audit_events"].append(event)
    return signature_doc