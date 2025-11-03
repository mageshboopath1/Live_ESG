"""Cache management endpoints for API Gateway."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from ..cache import (
    cache_manager,
    invalidate_company_cache,
    invalidate_indicators_cache,
    invalidate_scores_cache,
)
from ..auth.dependencies import require_auth
from ..auth.jwt import TokenData

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/cache",
    tags=["cache"],
)


@router.post("/invalidate/company/{company_id}")
def invalidate_company(
    company_id: int,
    current_user: TokenData = Depends(require_auth),
):
    """
    Invalidate all cache entries for a specific company.
    
    This will clear cached data for:
    - Company details
    - Company indicators
    - Company scores
    
    Args:
        company_id: Company ID
        
    Returns:
        dict: Success message
        
    Example:
        POST /api/cache/invalidate/company/1
    """
    if not cache_manager.enabled:
        raise HTTPException(
            status_code=503,
            detail="Cache is not enabled"
        )
    
    try:
        invalidate_company_cache(company_id)
        logger.info(f"Cache invalidated for company_id={company_id}")
        
        return {
            "message": f"Cache invalidated for company {company_id}",
            "company_id": company_id,
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate cache"
        )


@router.post("/invalidate/indicators")
def invalidate_indicators(
    current_user: TokenData = Depends(require_auth),
):
    """
    Invalidate all BRSR indicator definition cache entries.
    
    Use this when indicator definitions are updated in the database.
    
    Returns:
        dict: Success message
        
    Example:
        POST /api/cache/invalidate/indicators
    """
    if not cache_manager.enabled:
        raise HTTPException(
            status_code=503,
            detail="Cache is not enabled"
        )
    
    try:
        invalidate_indicators_cache()
        logger.info("Indicator definitions cache invalidated")
        
        return {
            "message": "Indicator definitions cache invalidated",
        }
        
    except Exception as e:
        logger.error(f"Error invalidating indicators cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate indicators cache"
        )


@router.post("/invalidate/scores/{company_id}")
def invalidate_scores(
    company_id: int,
    year: Optional[int] = Query(None, description="Specific year to invalidate (all years if not specified)"),
    current_user: TokenData = Depends(require_auth),
):
    """
    Invalidate score cache entries for a company.
    
    Args:
        company_id: Company ID
        year: Optional specific year to invalidate (invalidates all years if not specified)
        
    Returns:
        dict: Success message
        
    Example:
        POST /api/cache/invalidate/scores/1?year=2024
        POST /api/cache/invalidate/scores/1 (invalidates all years)
    """
    if not cache_manager.enabled:
        raise HTTPException(
            status_code=503,
            detail="Cache is not enabled"
        )
    
    try:
        invalidate_scores_cache(company_id, year)
        
        year_msg = f" for year {year}" if year else " for all years"
        logger.info(f"Scores cache invalidated for company_id={company_id}{year_msg}")
        
        return {
            "message": f"Scores cache invalidated for company {company_id}{year_msg}",
            "company_id": company_id,
            "year": year,
        }
        
    except Exception as e:
        logger.error(f"Error invalidating scores cache for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate scores cache"
        )


@router.post("/clear")
def clear_all_cache(
    current_user: TokenData = Depends(require_auth),
):
    """
    Clear all cache entries.
    
    WARNING: This will clear the entire cache. Use with caution.
    
    Returns:
        dict: Success message
        
    Example:
        POST /api/cache/clear
    """
    if not cache_manager.enabled:
        raise HTTPException(
            status_code=503,
            detail="Cache is not enabled"
        )
    
    try:
        cache_manager.clear_all()
        logger.warning("All cache entries cleared")
        
        return {
            "message": "All cache entries cleared",
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear cache"
        )


@router.get("/status")
def get_cache_status():
    """
    Get cache status and statistics.
    
    Returns:
        dict: Cache status information
        
    Example:
        GET /api/cache/status
    """
    return {
        "enabled": cache_manager.enabled,
        "host": cache_manager._client.connection_pool.connection_kwargs.get("host") if cache_manager.enabled else None,
        "port": cache_manager._client.connection_pool.connection_kwargs.get("port") if cache_manager.enabled else None,
        "db": cache_manager._client.connection_pool.connection_kwargs.get("db") if cache_manager.enabled else None,
    }
