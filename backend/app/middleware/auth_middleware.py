# app/middleware/auth_middleware.py

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt_utils import decode_token, is_token_blacklisted
from app.config.database import get_database
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("legalyze.auth_middleware")

# ── HTTP Bearer Security Scheme ───────────────────────────────────
security = HTTPBearer()


def normalize_role(role: Optional[str]) -> str:
    return (role or "user").strip().lower()


# ══════════════════════════════════════════════════════════════════
# VERIFY TOKEN DEPENDENCY
# ══════════════════════════════════════════════════════════════════

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Main authentication dependency for protected routes.
    
    Validates:
    1. Token signature and expiry
    2. Token type (must be 'access')
    3. Token not blacklisted (user logged out)
    4. User still exists and is active
    
    Returns:
        Decoded JWT payload with user info
    
    Raises:
        HTTPException 401 if invalid
    
    Usage:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(verify_token)):
            user_id = current_user["sub"]
            ...
    """
    token = credentials.credentials
    
    # ── Step 1: Decode and validate token ────────────────────────
    payload = decode_token(token)
    
    if not payload:
        logger.warning("Token verification failed: invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # ── Step 2: Check token type ──────────────────────────────────
    if payload.get("type") != "access":
        logger.warning(
            f"Token type mismatch | "
            f"expected=access, got={payload.get('type')}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # ── Step 3: Check if token is blacklisted ────────────────────
    db = get_database()
    is_blacklisted = await is_token_blacklisted(payload, db)
    
    if is_blacklisted:
        logger.warning(
            f"Blacklisted token used | user={payload.get('sub')}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # ── Step 4: Verify user still exists and is active ───────────
    from bson import ObjectId
    
    try:
        user_id = payload.get("sub")
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            logger.warning(f"Token valid but user not found | id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found. Token may be invalid."
            )
        
        if user.get("account_status") != "active":
            logger.warning(
                f"Inactive account attempted access | "
                f"id={user_id}, status={user.get('account_status')}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.get('account_status')}. Please contact support."
            )
        
        # Attach user metadata to payload
        payload["name"] = user.get("name")
        payload["account_status"] = user.get("account_status")
        payload["role"] = normalize_role(user.get("role", payload.get("role")))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication verification failed."
        )
    
    logger.debug(f"Token verified successfully | user={user_id}")
    
    return payload


# ══════════════════════════════════════════════════════════════════
# OPTIONAL AUTHENTICATION
# ══════════════════════════════════════════════════════════════════

async def optional_auth(
    request: Request
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.
    Returns user info if token is present and valid, None otherwise.
    
    Use for routes that work with or without authentication.
    
    Usage:
        @router.get("/public-or-private")
        async def route(user: Optional[dict] = Depends(optional_auth)):
            if user:
                # Authenticated behavior
                pass
            else:
                # Public behavior
                pass
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        return await verify_token(credentials)
    
    except HTTPException:
        # Invalid token, but route allows public access
        return None


# ══════════════════════════════════════════════════════════════════
# ROLE-BASED ACCESS CONTROL
# ══════════════════════════════════════════════════════════════════

class RoleChecker:
    """
    Dependency for role-based access control.
    
    Usage:
        admin_only = RoleChecker(["admin"])
        
        @router.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: dict = Depends(admin_only)
        ):
            ...
    """
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = [normalize_role(r) for r in allowed_roles]
    
    async def __call__(
        self,
        current_user: dict = Depends(verify_token)
    ) -> dict:
        user_role = normalize_role(current_user.get("role", "user"))
        
        if user_role not in self.allowed_roles:
            logger.warning(
                f"Unauthorized role access attempt | "
                f"user={current_user.get('sub')}, "
                f"role={user_role}, "
                f"required={self.allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(self.allowed_roles)}"
            )
        
        return current_user


# ── Common Role Checkers ──────────────────────────────────────────
require_admin = RoleChecker(["admin"])
require_user_or_admin = RoleChecker(["user", "admin"])
require_legal_user = RoleChecker(["admin", "lawyer", "client", "user"])
require_lawyer_or_admin = RoleChecker(["admin", "lawyer"])
require_client_or_admin = RoleChecker(["admin", "client"])


# ══════════════════════════════════════════════════════════════════
# API KEY AUTHENTICATION (alternative to JWT)
# ══════════════════════════════════════════════════════════════════

async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verifies API key authentication (alternative to JWT).
    
    Header: X-API-Key: <api_key>
    
    Use for:
    - Webhook endpoints
    - Server-to-server communication
    - Integrations
    
    Usage:
        @router.post("/webhooks/stripe")
        async def stripe_webhook(
            payload: dict,
            api_auth: dict = Depends(verify_api_key)
        ):
            ...
    """
    if not x_api_key:
        x_api_key = request.headers.get("X-API-Key")
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header."
        )
    
    db = get_database()
    
    # Lookup API key in database
    api_key_doc = await db["api_keys"].find_one({
        "key": x_api_key,
        "is_active": True
    })
    
    if not api_key_doc:
        logger.warning(f"Invalid API key used: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )
    
    # Check expiry
    from datetime import datetime
    if api_key_doc.get("expires_at"):
        if datetime.utcnow() > api_key_doc["expires_at"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired."
            )
    
    # Update last used timestamp
    await db["api_keys"].update_one(
        {"_id": api_key_doc["_id"]},
        {"$set": {"last_used_at": datetime.utcnow()}}
    )
    
    logger.debug(f"API key verified | owner={api_key_doc.get('owner_id')}")
    
    return {
        "api_key_id": str(api_key_doc["_id"]),
        "owner_id": api_key_doc.get("owner_id"),
        "permissions": api_key_doc.get("permissions", [])
    }


# ══════════════════════════════════════════════════════════════════
# EXTRACT CLIENT INFO
# ══════════════════════════════════════════════════════════════════

def get_client_ip(request: Request) -> Optional[str]:
    """
    Extracts client IP address from request.
    Handles proxy forwarding headers.
    """
    # Check X-Forwarded-For (proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extracts User-Agent string from request."""
    return request.headers.get("User-Agent")


def get_client_metadata(request: Request) -> dict:
    """
    Extracts comprehensive client metadata for audit logging.
    
    Returns:
        Dict with ip_address, user_agent, referer, etc.
    """
    return {
        "ip_address": get_client_ip(request),
        "user_agent": get_user_agent(request),
        "referer": request.headers.get("Referer"),
        "origin": request.headers.get("Origin"),
        "accept_language": request.headers.get("Accept-Language"),
        "method": request.method,
        "path": str(request.url.path),
        "query_params": dict(request.query_params)
    }
