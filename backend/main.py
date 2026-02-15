# main.py

"""
Legalyze API - AI-Powered Legal Contract Analysis Platform

Main application entry point.
"""

from fastapi import FastAPI, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging
import sys
import time
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────
from app.config.settings import settings
from app.config.database import connect_to_mongo, close_mongo_connection

# ── Middleware ────────────────────────────────────────────────────
from app.middleware.cors_middleware import get_cors_middleware
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
    rate_limit_exceeded_handler,
    legalyze_exception_handler,
    LegalyzeException
)
from app.middleware.rate_limiter import limiter
from app.middleware.auth_middleware import require_admin

# ── Routes ────────────────────────────────────────────────────────
from app.routes import (
    auth_routes,
    contract_routes,
    analysis_routes,
    suggestion_routes,
    generation_routes,
    signature_routes
)

# ── Logging Setup ─────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger("legalyze.main")


# ══════════════════════════════════════════════════════════════════
# LIFESPAN CONTEXT MANAGER
# ══════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    
    Startup:
    - Connect to MongoDB
    - Initialize AI models
    - Load vector store
    - Setup background tasks
    
    Shutdown:
    - Close database connections
    - Cleanup model cache
    """
    # ── STARTUP ───────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"[START] {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    try:
        # Connect to MongoDB
        logger.info("[DB] Connecting to MongoDB...")
        await connect_to_mongo()
        
        # Load AI models (lazy loading on first use is also fine)
        if settings.ENVIRONMENT == "production":
            logger.info("[AI] Pre-loading AI models...")
            try:
                from app.ai.nlp_pipeline import load_spacy_model
                from app.ai.embeddings import load_embedding_model
                from app.ai.rag_pipeline import load_vector_store, is_vector_store_ready
                
                # Load spaCy
                load_spacy_model()
                
                # Load embeddings
                load_embedding_model()
                
                # Load RAG vector store
                if is_vector_store_ready():
                    load_vector_store()
                    logger.info("[OK] Vector store loaded")
                else:
                    logger.warning("[WARN] Vector store not found - RAG features disabled")
                
            except Exception as e:
                logger.warning(f"[WARN] AI model loading failed (will lazy-load): {e}")
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"[OK] Startup complete in {elapsed:.2f}s")
        logger.info(f"[API] Available at: http://localhost:8000{settings.API_PREFIX}")
        logger.info(f"[DOCS] Available at: http://localhost:8000/docs")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"[ERROR] Startup failed: {e}")
        raise
    
    yield
    
    # ── SHUTDOWN ──────────────────────────────────────────────────
    logger.info("[SHUTDOWN] Shutting down...")
    
    try:
        # Close MongoDB connection
        await close_mongo_connection()
        
        # Clear AI model cache
        if settings.ENVIRONMENT == "production":
            from app.ai.transformer_model import clear_model_cache
            from app.ai.embeddings import clear_embedding_cache
            
            clear_model_cache()
            clear_embedding_cache()
        
        logger.info("[OK] Shutdown complete")
    
    except Exception as e:
        logger.error(f"[ERROR] Shutdown error: {e}")


# ══════════════════════════════════════════════════════════════════
# CREATE FASTAPI APP
# ══════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    **Legalyze** - AI-Powered Legal Contract Analysis Platform
    
    ## Features
    
    * 📄 **Upload & Extract**: PDF/DOCX contract upload with OCR support
    * 🔍 **AI Analysis**: Clause extraction, risk assessment, plain-English simplification
    * 💡 **Smart Suggestions**: AI-generated fair clause alternatives
    * ✍️ **Contract Generation**: Create balanced contracts with accepted suggestions
    * 🔐 **Digital Signatures**: RSA-PSS + SHA-256 cryptographic signing
    * 📊 **Analytics**: Contract dashboard with risk scoring and statistics
    
    ## Authentication
    
    All protected endpoints require a Bearer token in the Authorization header:
```
    Authorization: Bearer <access_token>
```
    
    Obtain tokens via `/api/auth/login` endpoint.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# ── Add Rate Limiter State ────────────────────────────────────────
app.state.limiter = limiter


# ══════════════════════════════════════════════════════════════════
# MIDDLEWARE REGISTRATION
# ══════════════════════════════════════════════════════════════════

# CORS (must be first)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging
app.add_middleware(RequestLoggingMiddleware)

# Rate Limiting (via slowapi)
# Note: slowapi integrates with app.state.limiter automatically


# ══════════════════════════════════════════════════════════════════
# EXCEPTION HANDLERS
# ══════════════════════════════════════════════════════════════════

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(LegalyzeException, legalyze_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


# ══════════════════════════════════════════════════════════════════
# ROUTES REGISTRATION
# ══════════════════════════════════════════════════════════════════

# Include all route modules
app.include_router(
    auth_routes.router,
    prefix=settings.API_PREFIX,
    tags=["Authentication"]
)

app.include_router(
    contract_routes.router,
    prefix=settings.API_PREFIX,
    tags=["Contracts"]
)

app.include_router(
    analysis_routes.router,
    prefix=settings.API_PREFIX,
    tags=["Analysis"]
)

app.include_router(
    suggestion_routes.router,
    prefix=settings.API_PREFIX,
    tags=["Suggestions"]
)

app.include_router(
    generation_routes.router,
    prefix=settings.API_PREFIX,
    tags=["Generation"]
)

app.include_router(
    signature_routes.router,
    prefix=settings.API_PREFIX,
    tags=["Signatures"]
)


# ══════════════════════════════════════════════════════════════════
# ROOT ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint.
    Returns basic information about the API.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
    - Application status
    - Database connectivity
    - Uptime
    - Version info
    """
    from app.config.database import get_database, get_db_stats
    from app.ai.rag_pipeline import is_vector_store_ready
    
    # Check database
    db_status = "connected"
    try:
        db = get_database()
        await db.command("ping")
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check vector store
    vector_store_status = "ready" if is_vector_store_ready() else "not_loaded"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
        "database": db_status,
        "vector_store": vector_store_status,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/stats", tags=["Stats"])
async def get_stats(current_user: dict = Depends(require_admin)):
    """
    Returns system statistics (admin only in production).
    """
    from app.config.database import get_db_stats
    
    db_stats = await get_db_stats()
    
    return {
        "database": db_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


# ══════════════════════════════════════════════════════════════════
# RUN SERVER (for development)
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
