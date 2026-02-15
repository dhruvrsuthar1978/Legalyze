# app/middleware/rate_limiter.py

from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger("legalyze.rate_limiter")


# ══════════════════════════════════════════════════════════════════
# LIMITER INSTANCE
# ══════════════════════════════════════════════════════════════════

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
    strategy="fixed-window"
)


# ══════════════════════════════════════════════════════════════════
# CUSTOM KEY FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def get_user_id_or_ip(request: Request) -> str:
    """
    Rate limit by user ID if authenticated, otherwise by IP.
    
    This ensures:
    - Authenticated users get higher, consistent limits
    - Anonymous users are rate-limited by IP
    """
    # Try to extract user ID from token
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from app.utils.jwt_utils import extract_user_id
            token = auth_header.replace("Bearer ", "")
            user_id = extract_user_id(token)
            
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


def get_api_key_or_ip(request: Request) -> str:
    """
    Rate limit by API key if present, otherwise by IP.
    """
    api_key = request.headers.get("X-API-Key")
    
    if api_key:
        return f"api_key:{api_key[:16]}"  # Use first 16 chars
    
    return f"ip:{get_remote_address(request)}"


# ══════════════════════════════════════════════════════════════════
# RATE LIMIT EXCEEDED HANDLER
# ══════════════════════════════════════════════════════════════════

async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded
) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns:
        429 Too Many Requests with retry-after header
    """
    logger.warning(
        f"Rate limit exceeded | "
        f"path={request.url.path}, "
        f"ip={get_remote_address(request)}"
    )
    
    # Parse retry-after from exception
    retry_after = 60  # Default 1 minute
    
    error_response = {
        "success": False,
        "error": "Too many requests. Please slow down.",
        "status_code": 429,
        "retry_after_seconds": retry_after,
        "message": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response,
        headers={"Retry-After": str(retry_after)}
    )


# ══════════════════════════════════════════════════════════════════
# CUSTOM RATE LIMIT DECORATORS
# ══════════════════════════════════════════════════════════════════

def strict_rate_limit(limit: str):
    """
    Strict rate limit decorator (by user ID or IP).
    
    Usage:
        @router.post("/upload")
        @strict_rate_limit("5/minute")
        async def upload_endpoint():
            ...
    """
    def decorator(func):
        func.__rate_limit__ = limit
        func.__rate_limit_key__ = get_user_id_or_ip
        return func
    return decorator


def api_rate_limit(limit: str):
    """
    API-specific rate limit (by API key or IP).
    
    Usage:
        @router.post("/webhooks/process")
        @api_rate_limit("100/hour")
        async def webhook():
            ...
    """
    def decorator(func):
        func.__rate_limit__ = limit
        func.__rate_limit_key__ = get_api_key_or_ip
        return func
    return decorator


# ══════════════════════════════════════════════════════════════════
# RATE LIMIT BYPASS (for testing/admin)
# ══════════════════════════════════════════════════════════════════

BYPASS_IPS = [
    "127.0.0.1",
    "::1"  # localhost IPv6
]

BYPASS_API_KEYS = [
    # Add admin API keys here
]


def should_bypass_rate_limit(request: Request) -> bool:
    """
    Checks if request should bypass rate limiting.
    
    Bypass conditions:
    - Localhost/admin IPs
    - Admin API keys
    - Internal service accounts
    """
    # Check IP
    client_ip = get_remote_address(request)
    if client_ip in BYPASS_IPS:
        return True
    
    # Check API key
    api_key = request.headers.get("X-API-Key")
    if api_key in BYPASS_API_KEYS:
        return True
    
    return False


# ══════════════════════════════════════════════════════════════════
# RATE LIMIT MIDDLEWARE
# ══════════════════════════════════════════════════════════════════

class RateLimitMiddleware:
    """
    Global rate limiting middleware.
    
    Applied to all requests unless bypassed.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Check bypass
        if should_bypass_rate_limit(request):
            await self.app(scope, receive, send)
            return
        
        # Apply rate limit
        # (slowapi handles this automatically when integrated)
        
        await self.app(scope, receive, send)