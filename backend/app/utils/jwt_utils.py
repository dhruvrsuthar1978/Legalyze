# app/utils/jwt_utils.py

from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.config.settings import settings
import logging

logger = logging.getLogger("legalyze.jwt")

ALGORITHM = "HS256"

# Token expiry defaults
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict) -> str:
    """Creates a JWT access token."""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["iat"] = datetime.utcnow()
    payload["type"] = "access"
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(data: dict, ttl_days: int = REFRESH_TOKEN_EXPIRE_DAYS) -> str:
    """Creates a JWT refresh token with longer expiry."""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=ttl_days)
    payload["iat"] = datetime.utcnow()
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def is_token_blacklisted(payload: dict, db) -> bool:
    """
    Check if token is blacklisted (user logged out).
    
    Args:
        payload: Decoded JWT payload containing user info
        db: MongoDB database instance
    
    Returns:
        True if token is blacklisted, False otherwise
    """
    user_id = payload.get("sub")
    if not user_id:
        return True
    
    # Check if user has a logout record after token was issued
    iat = payload.get("iat")
    if not iat:
        return False
    
    issued_at = datetime.fromtimestamp(iat)
    
    # Query blacklist collection
    blacklist_entry = await db["token_blacklist"].find_one({
        "user_id": user_id,
        "logged_out_at": {"$gte": issued_at}
    })
    
    return blacklist_entry is not None


def extract_user_id(token: str) -> Optional[str]:
    """Quick extraction of user ID from token without full validation."""
    payload = decode_token(token)
    return payload.get("sub") if payload else None