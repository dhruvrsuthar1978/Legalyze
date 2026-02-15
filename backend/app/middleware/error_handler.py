# app/middleware/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
from datetime import datetime
from typing import Optional
import logging
import traceback

logger = logging.getLogger("legalyze.error_handler")


# ══════════════════════════════════════════════════════════════════
# HTTP EXCEPTION HANDLER
# ══════════════════════════════════════════════════════════════════

async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handles standard HTTP exceptions raised by FastAPI.
    
    Returns standardized JSON error response.
    """
    error_response = {
        "success": False,
        "error": exc.detail if isinstance(exc.detail, str) else "Request failed",
        "status_code": exc.status_code,
        "path": str(request.url.path),
        "method": request.method,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # If detail is a dict (structured error), merge it
    if isinstance(exc.detail, dict):
        error_response.update(exc.detail)
    
    # Log based on severity
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code} | "
            f"{request.method} {request.url.path} | "
            f"{exc.detail}"
        )
    elif exc.status_code >= 400:
        logger.warning(
            f"HTTP {exc.status_code} | "
            f"{request.method} {request.url.path} | "
            f"{exc.detail}"
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


# ══════════════════════════════════════════════════════════════════
# VALIDATION EXCEPTION HANDLER
# ══════════════════════════════════════════════════════════════════

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handles Pydantic validation errors from request bodies.
    
    Returns user-friendly validation error messages.
    """
    errors = []
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    error_response = {
        "success": False,
        "error": "Validation failed",
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "validation_errors": errors,
        "path": str(request.url.path),
        "method": request.method,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.warning(
        f"Validation error | "
        f"{request.method} {request.url.path} | "
        f"{len(errors)} error(s)"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


# ══════════════════════════════════════════════════════════════════
# PYDANTIC VALIDATION ERROR HANDLER
# ══════════════════════════════════════════════════════════════════

async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    Handles Pydantic ValidationError (internal model validation).
    """
    errors = []
    
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = {
        "success": False,
        "error": "Data validation failed",
        "validation_errors": errors,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.warning(f"Pydantic validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


# ══════════════════════════════════════════════════════════════════
# GLOBAL EXCEPTION HANDLER
# ══════════════════════════════════════════════════════════════════

async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catches all unhandled exceptions.
    
    Returns generic 500 error to user, logs full traceback.
    """
    # Get full traceback
    tb = traceback.format_exc()
    
    # Log full error with traceback
    logger.error(
        f"UNHANDLED EXCEPTION | "
        f"{request.method} {request.url.path} | "
        f"{type(exc).__name__}: {str(exc)}\n"
        f"{tb}"
    )
    
    # Don't expose internal error details to users in production
    from app.config.settings import settings
    
    if settings.DEBUG:
        error_detail = str(exc)
        traceback_info = tb
    else:
        error_detail = "An internal server error occurred."
        traceback_info = None
    
    error_response = {
        "success": False,
        "error": error_detail,
        "error_type": type(exc).__name__,
        "status_code": 500,
        "path": str(request.url.path),
        "method": request.method,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if traceback_info and settings.DEBUG:
        error_response["traceback"] = traceback_info
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# ══════════════════════════════════════════════════════════════════
# DATABASE ERROR HANDLER
# ══════════════════════════════════════════════════════════════════

async def database_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handles MongoDB/database-specific errors.
    """
    logger.error(
        f"Database error | "
        f"{request.method} {request.url.path} | "
        f"{str(exc)}"
    )
    
    error_response = {
        "success": False,
        "error": "Database operation failed. Please try again later.",
        "status_code": 503,
        "path": str(request.url.path),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response
    )


# ══════════════════════════════════════════════════════════════════
# CUSTOM ERROR CLASSES
# ══════════════════════════════════════════════════════════════════

class LegalyzeException(Exception):
    """
    Base exception class for custom application errors.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class AnalysisException(LegalyzeException):
    """Raised when contract analysis fails."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=500,
            error_code="ANALYSIS_ERROR"
        )


class GenerationException(LegalyzeException):
    """Raised when contract generation fails."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=500,
            error_code="GENERATION_ERROR"
        )


class SignatureException(LegalyzeException):
    """Raised when digital signature operation fails."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=500,
            error_code="SIGNATURE_ERROR"
        )


# ══════════════════════════════════════════════════════════════════
# CUSTOM EXCEPTION HANDLER
# ══════════════════════════════════════════════════════════════════

async def legalyze_exception_handler(
    request: Request,
    exc: LegalyzeException
) -> JSONResponse:
    """
    Handles custom Legalyze exceptions.
    """
    error_response = {
        "success": False,
        "error": exc.message,
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "path": str(request.url.path),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.error(
        f"Legalyze exception | "
        f"code={exc.error_code}, "
        f"message={exc.message}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


# ══════════════════════════════════════════════════════════════════
# RATE LIMIT EXCEPTION HANDLER
# ══════════════════════════════════════════════════════════════════

async def rate_limit_exceeded_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handles rate limit exceeded errors.
    """
    error_response = {
        "success": False,
        "error": "Rate limit exceeded. Please try again later.",
        "status_code": 429,
        "path": str(request.url.path),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.warning(f"Rate limit exceeded | {request.method} {request.url.path}")
    
    return JSONResponse(
        status_code=429,
        content=error_response
    )