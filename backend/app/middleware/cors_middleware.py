# app/middleware/cors_middleware.py

from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings


# ══════════════════════════════════════════════════════════════════
# CORS CONFIGURATION
# ══════════════════════════════════════════════════════════════════

def get_cors_middleware():
    """
    Returns configured CORS middleware.
    
    CORS (Cross-Origin Resource Sharing) allows frontend apps
    running on different domains to access the API.
    """
    return CORSMiddleware(
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=[
            "X-Process-Time",
            "X-Request-ID",
            "Content-Disposition"
        ],
        max_age=3600  # Cache preflight requests for 1 hour
    )


# ══════════════════════════════════════════════════════════════════
# PRODUCTION CORS (stricter)
# ══════════════════════════════════════════════════════════════════

def get_production_cors_middleware():
    """
    Stricter CORS configuration for production.
    """
    return CORSMiddleware(
        allow_origins=[
            "https://legalyze.com",
            "https://www.legalyze.com",
            "https://app.legalyze.com"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID"
        ],
        expose_headers=[
            "X-Process-Time",
            "X-Request-ID",
            "Content-Disposition"
        ],
        max_age=3600
    )