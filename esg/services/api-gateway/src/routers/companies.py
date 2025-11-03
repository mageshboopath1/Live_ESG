"""Company endpoints for API Gateway."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ..db.connection import get_db
from ..db.models import CompanyCatalog
from ..schemas.company import (
    CompanyResponse,
    CompanyListResponse,
    CompanyDetailResponse,
)
from ..cache import cache_manager, cache_key
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/companies",
    tags=["companies"],
)


@router.get("/search", response_model=CompanyListResponse)
def search_companies(
    q: str = Query(..., min_length=1, description="Search query (company name or symbol)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Search companies by name or symbol.
    
    Args:
        q: Search query string (searches in company name and symbol)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        db: Database session
        
    Returns:
        CompanyListResponse: Paginated list of matching companies
        
    Example:
        GET /api/companies/search?q=reliance
        GET /api/companies/search?q=HDFC&skip=0&limit=10
    """
    try:
        # Build search query (case-insensitive partial match)
        search_pattern = f"%{q}%"
        query = db.query(CompanyCatalog).filter(
            or_(
                CompanyCatalog.company_name.ilike(search_pattern),
                CompanyCatalog.symbol.ilike(search_pattern),
            )
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        companies = query.order_by(CompanyCatalog.company_name).offset(skip).limit(limit).all()
        
        logger.info(f"Search for '{q}' returned {len(companies)} companies (total={total})")
        
        return CompanyListResponse(
            companies=[
                CompanyResponse(
                    id=company.id,
                    company_name=company.company_name,
                    symbol=company.symbol,
                    industry=company.industry,
                    isin_code=company.isin_code,
                    series=company.series,
                )
                for company in companies
            ],
            total=total,
            skip=skip,
            limit=limit,
        )
        
    except Exception as e:
        logger.error(f"Error searching companies with query '{q}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search companies"
        )


@router.get("", response_model=CompanyListResponse)
def list_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    db: Session = Depends(get_db),
):
    """
    List all companies with pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        industry: Optional filter by industry
        db: Database session
        
    Returns:
        CompanyListResponse: Paginated list of companies with metadata
        
    Example:
        GET /api/companies?skip=0&limit=50
        GET /api/companies?skip=0&limit=50&industry=Banking
    """
    try:
        # Build query
        query = db.query(CompanyCatalog)
        
        # Apply industry filter if provided
        if industry:
            query = query.filter(CompanyCatalog.industry == industry)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        companies = query.order_by(CompanyCatalog.company_name).offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(companies)} companies (skip={skip}, limit={limit}, industry={industry})")
        
        return CompanyListResponse(
            companies=[
                CompanyResponse(
                    id=company.id,
                    company_name=company.company_name,
                    symbol=company.symbol,
                    industry=company.industry,
                    isin_code=company.isin_code,
                    series=company.series,
                )
                for company in companies
            ],
            total=total,
            skip=skip,
            limit=limit,
        )
        
    except Exception as e:
        logger.error(f"Error listing companies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve companies"
        )


@router.get("/{company_id}", response_model=CompanyDetailResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a single company by ID with caching.
    
    Args:
        company_id: Company ID
        db: Database session
        
    Returns:
        CompanyDetailResponse: Detailed company information
        
    Raises:
        HTTPException: 404 if company not found
        
    Example:
        GET /api/companies/1
    """
    # Try to get from cache
    cache_key_str = cache_key("company", company_id)
    cached_data = cache_manager.get(cache_key_str)
    
    if cached_data:
        logger.debug(f"Cache hit for company_id={company_id}")
        return CompanyDetailResponse(**cached_data)
    
    try:
        company = db.query(CompanyCatalog).filter(CompanyCatalog.id == company_id).first()
        
        if not company:
            logger.warning(f"Company not found: id={company_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Company with id {company_id} not found"
            )
        
        # Count reports for this company
        from ..db.models import IngestionMetadata
        report_count = db.query(func.count(IngestionMetadata.id)).filter(
            IngestionMetadata.company_id == company_id
        ).scalar()
        
        # Count extracted indicators for this company
        from ..db.models import ExtractedIndicator
        indicator_count = db.query(func.count(ExtractedIndicator.id)).filter(
            ExtractedIndicator.company_id == company_id
        ).scalar()
        
        # Get available report years
        report_years = db.query(ExtractedIndicator.report_year).filter(
            ExtractedIndicator.company_id == company_id
        ).distinct().order_by(ExtractedIndicator.report_year.desc()).all()
        
        logger.info(f"Retrieved company: id={company_id}, name={company.company_name}")
        
        response = CompanyDetailResponse(
            id=company.id,
            company_name=company.company_name,
            symbol=company.symbol,
            industry=company.industry,
            isin_code=company.isin_code,
            series=company.series,
            created_at=company.created_at,
            updated_at=company.updated_at,
            report_count=report_count,
            indicator_count=indicator_count,
            available_years=[year[0] for year in report_years] if report_years else [],
        )
        
        # Cache the response
        cache_manager.set(cache_key_str, response.model_dump(), settings.CACHE_TTL_COMPANY)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve company"
        )
