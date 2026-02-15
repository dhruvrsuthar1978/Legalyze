# app/services/storage_service.py

import os
import uuid
import boto3
import logging
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime, timedelta
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger("legalyze.storage")

# ── S3 Client ─────────────────────────────────────────────────────
_s3_client = None

def _get_s3() -> boto3.client:
    """Lazy-initializes the S3 client on first call."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id     = settings.AWS_ACCESS_KEY,
            aws_secret_access_key = settings.AWS_SECRET_KEY,
            region_name           = settings.AWS_REGION,
            config                = Config(
                signature_version  = "s3v4",
                retries            = {"max_attempts": 3, "mode": "adaptive"}
            )
        )
        logger.info("S3 client initialized")
    return _s3_client


# ══════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════

async def upload_to_cloud(
    contents: bytes,
    filename: str,
    user_id: str,
    subfolder: str = "contracts"
) -> str:
    """
    Uploads a file to AWS S3.

    Key structure:
        {user_id}/{subfolder}/{uuid}_{filename}

    Returns:
        S3 object key (not a public URL)

    Raises:
        RuntimeError on upload failure
    """
    ext       = os.path.splitext(filename)[1].lower()
    safe_name = _sanitize_filename(filename)
    object_key = (
        f"users/{user_id}/{subfolder}/"
        f"{uuid.uuid4().hex}_{safe_name}"
    )

    content_type = (
        "application/pdf"
        if ext == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    try:
        _get_s3().put_object(
            Bucket=settings.S3_BUCKET,
            Key=object_key,
            Body=contents,
            ContentType=content_type,
            ServerSideEncryption="AES256",      # Encrypt at rest
            Metadata={
                "user_id":     user_id,
                "original_filename": filename,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"File uploaded to S3 | "
            f"bucket={settings.S3_BUCKET}, "
            f"key={object_key}, "
            f"size={len(contents) // 1024}KB"
        )

        return object_key

    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        raise RuntimeError(f"Cloud upload failed: {e.response['Error']['Message']}")


# ══════════════════════════════════════════════════════════════════
# DOWNLOAD URL
# ══════════════════════════════════════════════════════════════════

async def get_download_url(
    object_key: str,
    expiry_minutes: int = 15
) -> str:
    """
    Generates a pre-signed S3 URL for secure, temporary file access.

    Args:
        object_key     : S3 object key (from upload_to_cloud)
        expiry_minutes : URL validity period (default 15 min)

    Returns:
        Pre-signed HTTPS URL string

    Raises:
        RuntimeError if URL generation fails
    """
    try:
        url = _get_s3().generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET,
                "Key":    object_key
            },
            ExpiresIn=expiry_minutes * 60
        )
        logger.debug(
            f"Pre-signed URL generated | "
            f"key={object_key}, expiry={expiry_minutes}min"
        )
        return url

    except ClientError as e:
        logger.error(f"Pre-signed URL generation failed: {e}")
        raise RuntimeError(
            f"Download URL generation failed: {e.response['Error']['Message']}"
        )


# ══════════════════════════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════════════════════════

async def delete_from_cloud(object_key: str) -> bool:
    """
    Deletes a file from S3 by its object key.

    Returns:
        True on success, False on failure (non-raising)
    """
    try:
        _get_s3().delete_object(
            Bucket=settings.S3_BUCKET,
            Key=object_key
        )
        logger.info(f"S3 object deleted | key={object_key}")
        return True

    except ClientError as e:
        logger.error(f"S3 delete failed for {object_key}: {e}")
        return False


async def bulk_delete_from_cloud(object_keys: list) -> dict:
    """
    Deletes multiple S3 objects in a single API call (max 1000 per request).

    Returns:
        { "deleted": count, "errors": [keys_that_failed] }
    """
    if not object_keys:
        return {"deleted": 0, "errors": []}

    objects = [{"Key": key} for key in object_keys]

    try:
        response = _get_s3().delete_objects(
            Bucket=settings.S3_BUCKET,
            Delete={"Objects": objects, "Quiet": False}
        )

        deleted = len(response.get("Deleted", []))
        errors  = [e["Key"] for e in response.get("Errors", [])]

        logger.info(
            f"Bulk S3 delete | "
            f"requested={len(object_keys)}, "
            f"deleted={deleted}, "
            f"errors={len(errors)}"
        )
        return {"deleted": deleted, "errors": errors}

    except ClientError as e:
        logger.error(f"Bulk S3 delete failed: {e}")
        return {"deleted": 0, "errors": object_keys}


# ══════════════════════════════════════════════════════════════════
# CHECK FILE EXISTS
# ══════════════════════════════════════════════════════════════════

async def file_exists_in_cloud(object_key: str) -> bool:
    """Checks if an S3 object exists without downloading it."""
    try:
        _get_s3().head_object(
            Bucket=settings.S3_BUCKET,
            Key=object_key
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        logger.error(f"S3 existence check failed for {object_key}: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# DOWNLOAD FILE BYTES
# ══════════════════════════════════════════════════════════════════

async def download_file_bytes(object_key: str) -> bytes:
    """
    Downloads and returns the raw bytes of an S3 object.
    Used internally (e.g., for signature verification).

    Raises:
        RuntimeError if download fails
    """
    try:
        response = _get_s3().get_object(
            Bucket=settings.S3_BUCKET,
            Key=object_key
        )
        content = response["Body"].read()
        logger.debug(
            f"Downloaded {len(content) // 1024}KB from S3 | key={object_key}"
        )
        return content

    except ClientError as e:
        logger.error(f"S3 download failed for {object_key}: {e}")
        raise RuntimeError(
            f"File download failed: {e.response['Error']['Message']}"
        )


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _sanitize_filename(filename: str) -> str:
    """
    Makes a filename safe for use as an S3 key.
    Replaces spaces and special chars with underscores.
    """
    safe = ""
    for char in filename:
        if char.isalnum() or char in "._-":
            safe += char
        else:
            safe += "_"
    return safe


def url_expires_at(expiry_minutes: int = 15) -> datetime:
    """Returns the datetime when a pre-signed URL will expire."""
    return datetime.utcnow() + timedelta(minutes=expiry_minutes)