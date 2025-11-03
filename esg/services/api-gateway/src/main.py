"""Main FastAPI application for API Gateway."""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db.connection import check_database_connection, close_database_connections
from .cache import cache_manager
from .routers import companies, reports, indicators, scores, citations, auth, cache
from .auth.middleware import APIKeyMiddleware, RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ESG Intelligence Platform API",
    description="API Gateway for ESG Intelligence Platform - Transparent ESG Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(reports.router)
app.include_router(indicators.router)
app.include_router(scores.router)
app.include_router(citations.router)
app.include_router(cache.router)

# Configure CORS (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Note: API key authentication middleware removed from global scope
# Authentication is now applied per-router for POST/PUT/DELETE operations only
# GET operations are public and do not require authentication


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting ESG Intelligence Platform API Gateway")
    
    # Check database connection on startup
    if not check_database_connection():
        logger.error("Failed to connect to database on startup")
        raise RuntimeError("Database connection failed")
    
    logger.info("Database connection established successfully")
    
    # Log cache status
    if cache_manager.enabled:
        logger.info("Redis cache enabled")
    else:
        logger.warning("Redis cache disabled - running without caching")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down ESG Intelligence Platform API Gateway")
    close_database_connections()
    cache_manager.close()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ESG Intelligence Platform API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with database and cache connectivity verification.
    
    Returns:
        dict: Health status including database and cache connectivity
        
    Raises:
        HTTPException: If database is not accessible
    """
    db_healthy = check_database_connection()
    
    if not db_healthy:
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy: Database connection failed"
        )
    
    return {
        "status": "healthy",
        "service": "api-gateway",
        "database": "connected",
        "cache": "enabled" if cache_manager.enabled else "disabled",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
