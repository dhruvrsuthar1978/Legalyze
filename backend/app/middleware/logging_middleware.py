# app/middleware/logging_middleware.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import time
import logging
import json

logger = logging.getLogger("legalyze.requests")


# ══════════════════════════════════════════════════════════════════
# REQUEST LOGGING MIDDLEWARE
# ══════════════════════════════════════════════════════════════════

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all incoming HTTP requests and responses.
    
    Logs:
    - Request method, path, query params
    - Client IP, User-Agent
    - Response status code
    - Processing time
    - User ID (if authenticated)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Extract request metadata
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract user ID if authenticated
        user_id = "anonymous"
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                from app.utils.jwt_utils import extract_user_id
                token = auth_header.replace("Bearer ", "")
                extracted_id = extract_user_id(token)
                if extracted_id:
                    user_id = extracted_id
            except Exception:
                pass
        
        # Log request
        logger.info(
            f"REQUEST | "
            f"{method} {path} | "
            f"user={user_id} | "
            f"ip={client_ip}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            # Log error
            logger.error(
                f"REQUEST FAILED | "
                f"{method} {path} | "
                f"error={str(e)}"
            )
            raise
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        log_level = logging.INFO
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        
        logger.log(
            log_level,
            f"RESPONSE | "
            f"{method} {path} | "
            f"status={status_code} | "
            f"time={process_time:.3f}s | "
            f"user={user_id}"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(id(request))
        
        return response


# ══════════════════════════════════════════════════════════════════
# DETAILED REQUEST LOGGER (for debugging)
# ══════════════════════════════════════════════════════════════════

class DetailedRequestLogger(BaseHTTPMiddleware):
    """
    Logs detailed request/response information for debugging.
    
    Should only be enabled in development/staging.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Log request details
        request_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None
            }
        }
        
        # Try to log body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Note: This consumes the body stream
                # In production, use a more sophisticated approach
                body = await request.body()
                if body:
                    try:
                        request_log["body"] = json.loads(body.decode())
                    except Exception:
                        request_log["body"] = body.decode()[:500]  # First 500 chars
            except Exception:
                request_log["body"] = "<unable to read>"
        
        logger.debug(f"DETAILED REQUEST: {json.dumps(request_log, indent=2)}")
        
        # Process request
        response = await call_next(request)
        
        # Log response details
        response_log = {
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }
        
        logger.debug(f"DETAILED RESPONSE: {json.dumps(response_log, indent=2)}")
        
        return response


# ══════════════════════════════════════════════════════════════════
# AUDIT LOGGING MIDDLEWARE
# ══════════════════════════════════════════════════════════════════

class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Logs security-sensitive operations to audit trail.
    
    Tracks:
    - Authentication attempts
    - Data modifications
    - Permission changes
    - File uploads/downloads
    - Signature operations
    """
    
    AUDIT_PATHS = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/contracts/upload",
        "/api/signatures",
        "/api/generate"
    ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Check if path should be audited
        should_audit = any(
            audit_path in path
            for audit_path in self.AUDIT_PATHS
        )
        
        if not should_audit:
            return await call_next(request)
        
        # Extract user info
        user_id = "anonymous"
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                from app.utils.jwt_utils import extract_user_id
                token = auth_header.replace("Bearer ", "")
                user_id = extract_user_id(token) or "anonymous"
            except Exception:
                pass
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log to audit trail
        from app.config.database import db
        
        audit_entry = {
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "action": f"{request.method} {path}",
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 400,
            "process_time_ms": int(process_time * 1000)
        }
        
        try:
            await db["audit_logs"].insert_one(audit_entry)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
        
        return response