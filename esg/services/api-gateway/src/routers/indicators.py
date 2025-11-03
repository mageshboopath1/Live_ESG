"""Indicator endpoints for API Gateway."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..db.connection import get_db
from ..db.models import (
    ExtractedIndicator,
    BRSRIndicator,
    CompanyCatalog,
    DocumentEmbedding,
)
from ..schemas.indicator import (
    IndicatorResponse,
    IndicatorDetailResponse,
    IndicatorListResponse,
    CitationResponse,
    IndicatorComparisonResponse,
    CompanyIndicatorComparison,
    ComparisonListResponse,
)
from ..cache import cache_manager, cache_key
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["indicators"],
)


def get_cached_brsr_indicators(db: Session) -> List[BRSRIndicator]:
    """
    Get all BRSR indicator definitions with caching.
    
    Args:
        db: Database session
        
    Returns:
        List of BRSR indicator definitions
    """
    cache_key_str = cache_key("indicators", "definitions", "all")
    cached_data = cache_manager.get(cache_key_str)
    
    if cached_data:
        logger.debug("Cache hit for BRSR indicator definitions")
        # Convert cached data back to model instances
        return [BRSRIndicator(**item) for item in cached_data]
    
    # Query from database
    indicators = db.query(BRSRIndicator).order_by(
        BRSRIndicator.attribute_number,
        BRSRIndicator.indicator_code
    ).all()
    
    # Cache the results
    cache_data = [
        {
            "id": ind.id,
            "indicator_code": ind.indicator_code,
            "attribute_number": ind.attribute_number,
            "parameter_name": ind.parameter_name,
            "measurement_unit": ind.measurement_unit,
            "description": ind.description,
            "pillar": ind.pillar,
            "weight": float(ind.weight) if ind.weight else None,
            "data_assurance_approach": ind.data_assurance_approach,
            "brsr_reference": ind.brsr_reference,
        }
        for ind in indicators
    ]
    cache_manager.set(cache_key_str, cache_data, settings.CACHE_TTL_INDICATORS)
    
    return indicators


@router.get("/brsr/indicators")
def get_indicator_definitions(
    attribute: Optional[int] = Query(None, ge=1, le=9, description="Filter by BRSR attribute (1-9)"),
    pillar: Optional[str] = Query(None, regex="^[ESG]$", description="Filter by pillar (E, S, or G)"),
    db: Session = Depends(get_db),
):
    """
    Get all BRSR indicator definitions.
    
    This endpoint returns the complete set of BRSR Core indicators from Annexure I
    that are used for extraction and scoring. No authentication required.
    
    Args:
        attribute: Optional filter by BRSR attribute number (1-9)
        pillar: Optional filter by ESG pillar (E, S, or G)
        db: Database session
        
    Returns:
        List of BRSR indicator definitions
        
    Example:
        GET /api/brsr/indicators
        GET /api/brsr/indicators?pillar=E
        GET /api/brsr/indicators?attribute=1
    """
    try:
        # Get all indicators with caching
        indicators = get_cached_brsr_indicators(db)
        
        # Apply filters in memory
        if attribute is not None:
            indicators = [ind for ind in indicators if ind.attribute_number == attribute]
        
        if pillar is not None:
            indicators = [ind for ind in indicators if ind.pillar == pillar]
        
        logger.info(
            f"Retrieved {len(indicators)} indicator definitions "
            f"(attribute={attribute}, pillar={pillar})"
        )
        
        # Convert to dict for response
        return [
            {
                "id": ind.id,
                "indicator_code": ind.indicator_code,
                "attribute_number": ind.attribute_number,
                "parameter_name": ind.parameter_name,
                "measurement_unit": ind.measurement_unit,
                "description": ind.description,
                "pillar": ind.pillar,
                "weight": float(ind.weight) if ind.weight else None,
                "data_assurance_approach": ind.data_assurance_approach,
                "brsr_reference": ind.brsr_reference,
            }
            for ind in indicators
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving indicator definitions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve indicator definitions"
        )


@router.get("/companies/{company_id}/indicators", response_model=IndicatorListResponse)
def list_company_indicators(
    company_id: int,
    year: Optional[int] = Query(None, description="Filter by report year"),
    attribute: Optional[int] = Query(None, ge=1, le=9, description="Filter by BRSR attribute (1-9)"),
    pillar: Optional[str] = Query(None, regex="^[ESG]$", description="Filter by pillar (E, S, or G)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    validation_status: Optional[str] = Query(None, regex="^(valid|invalid|pending)$", description="Filter by validation status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    List all indicators for a specific company with optional filters.
    
    Args:
        company_id: Company ID
        year: Optional filter by report year
        attribute: Optional filter by BRSR attribute number (1-9)
        pillar: Optional filter by ESG pillar (E, S, or G)
        min_confidence: Optional minimum confidence score threshold
        validation_status: Optional filter by validation status
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        db: Database session
        
    Returns:
        IndicatorListResponse: Paginated list of indicators with metadata
        
    Raises:
        HTTPException: 404 if company not found
        
    Example:
        GET /api/companies/1/indicators?year=2024
        GET /api/companies/1/indicators?year=2024&pillar=E&min_confidence=0.8
        GET /api/companies/1/indicators?attribute=1&validation_status=valid
    """
    try:
        # Verify company exists
        company = db.query(CompanyCatalog).filter(CompanyCatalog.id == company_id).first()
        if not company:
            logger.warning(f"Company not found: id={company_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Company with id {company_id} not found"
            )
        
        # Build query with join to get indicator details
        query = db.query(
            ExtractedIndicator,
            BRSRIndicator
        ).join(
            BRSRIndicator,
            ExtractedIndicator.indicator_id == BRSRIndicator.id
        ).filter(
            ExtractedIndicator.company_id == company_id
        )
        
        # Apply filters
        if year is not None:
            query = query.filter(ExtractedIndicator.report_year == year)
        
        if attribute is not None:
            query = query.filter(BRSRIndicator.attribute_number == attribute)
        
        if pillar is not None:
            query = query.filter(BRSRIndicator.pillar == pillar)
        
        if min_confidence is not None:
            query = query.filter(ExtractedIndicator.confidence_score >= min_confidence)
        
        if validation_status is not None:
            query = query.filter(ExtractedIndicator.validation_status == validation_status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        results = query.order_by(
            BRSRIndicator.attribute_number,
            BRSRIndicator.indicator_code
        ).offset(skip).limit(limit).all()
        
        # Build response
        indicators = []
        for extracted, brsr in results:
            indicators.append(
                IndicatorResponse(
                    id=extracted.id,
                    indicator_id=extracted.indicator_id,
                    indicator_code=brsr.indicator_code,
                    parameter_name=brsr.parameter_name,
                    attribute_number=brsr.attribute_number,
                    pillar=brsr.pillar,
                    extracted_value=extracted.extracted_value,
                    numeric_value=extracted.numeric_value,
                    measurement_unit=brsr.measurement_unit,
                    confidence_score=extracted.confidence_score,
                    validation_status=extracted.validation_status,
                    extracted_at=extracted.extracted_at,
                    report_year=extracted.report_year,
                    object_key=extracted.object_key,
                )
            )
        
        logger.info(
            f"Retrieved {len(indicators)} indicators for company_id={company_id} "
            f"(year={year}, attribute={attribute}, pillar={pillar}, total={total})"
        )
        
        return IndicatorListResponse(
            indicators=indicators,
            total=total,
            skip=skip,
            limit=limit,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing indicators for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve indicators"
        )


@router.get("/indicators/compare", response_model=ComparisonListResponse)
def compare_company_indicators(
    companies: str = Query(..., description="Comma-separated company IDs (e.g., '1,2,3')"),
    year: int = Query(..., description="Report year for comparison"),
    attribute: Optional[int] = Query(None, ge=1, le=9, description="Filter by BRSR attribute (1-9)"),
    pillar: Optional[str] = Query(None, regex="^[ESG]$", description="Filter by pillar (E, S, or G)"),
    db: Session = Depends(get_db),
):
    """
    Compare indicators across multiple companies for a specific year.
    
    Args:
        companies: Comma-separated list of company IDs (e.g., "1,2,3")
        year: Report year for comparison
        attribute: Optional filter by BRSR attribute number (1-9)
        pillar: Optional filter by ESG pillar (E, S, or G)
        db: Database session
        
    Returns:
        ComparisonListResponse: List of indicators with data for each company
        
    Raises:
        HTTPException: 400 if invalid company IDs provided
        
    Example:
        GET /api/indicators/compare?companies=1,2,3&year=2024
        GET /api/indicators/compare?companies=1,2,3&year=2024&pillar=E
        GET /api/indicators/compare?companies=1,2,3&year=2024&attribute=1
    """
    try:
        # Parse company IDs
        try:
            company_ids = [int(cid.strip()) for cid in companies.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid company IDs format. Expected comma-separated integers."
            )
        
        if len(company_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 companies are required for comparison"
            )
        
        if len(company_ids) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 companies allowed for comparison"
            )
        
        # Verify all companies exist
        companies_data = db.query(CompanyCatalog).filter(
            CompanyCatalog.id.in_(company_ids)
        ).all()
        
        if len(companies_data) != len(company_ids):
            found_ids = {c.id for c in companies_data}
            missing_ids = set(company_ids) - found_ids
            raise HTTPException(
                status_code=404,
                detail=f"Companies not found: {missing_ids}"
            )
        
        # Create company lookup
        company_lookup = {c.id: c for c in companies_data}
        
        # Get all BRSR indicators with caching
        all_indicators = get_cached_brsr_indicators(db)
        
        # Apply filters in memory
        indicators = all_indicators
        if attribute is not None:
            indicators = [ind for ind in indicators if ind.attribute_number == attribute]
        
        if pillar is not None:
            indicators = [ind for ind in indicators if ind.pillar == pillar]
        
        # Build comparison response
        comparisons = []
        
        for indicator in indicators:
            # Get extracted data for each company
            company_data = []
            
            for company_id in company_ids:
                company = company_lookup[company_id]
                
                # Query extracted indicator for this company, indicator, and year
                extracted = db.query(ExtractedIndicator).filter(
                    and_(
                        ExtractedIndicator.company_id == company_id,
                        ExtractedIndicator.indicator_id == indicator.id,
                        ExtractedIndicator.report_year == year
                    )
                ).first()
                
                if extracted:
                    company_data.append(
                        CompanyIndicatorComparison(
                            company_id=company.id,
                            company_name=company.company_name,
                            indicator_id=indicator.id,
                            indicator_code=indicator.indicator_code,
                            parameter_name=indicator.parameter_name,
                            extracted_value=extracted.extracted_value,
                            numeric_value=extracted.numeric_value,
                            measurement_unit=indicator.measurement_unit,
                            confidence_score=extracted.confidence_score,
                            validation_status=extracted.validation_status,
                            has_data=True,
                        )
                    )
                else:
                    # No data for this company
                    company_data.append(
                        CompanyIndicatorComparison(
                            company_id=company.id,
                            company_name=company.company_name,
                            indicator_id=indicator.id,
                            indicator_code=indicator.indicator_code,
                            parameter_name=indicator.parameter_name,
                            extracted_value=None,
                            numeric_value=None,
                            measurement_unit=indicator.measurement_unit,
                            confidence_score=None,
                            validation_status=None,
                            has_data=False,
                        )
                    )
            
            comparisons.append(
                IndicatorComparisonResponse(
                    indicator_code=indicator.indicator_code,
                    parameter_name=indicator.parameter_name,
                    attribute_number=indicator.attribute_number,
                    pillar=indicator.pillar,
                    measurement_unit=indicator.measurement_unit,
                    year=year,
                    companies=company_data,
                )
            )
        
        logger.info(
            f"Compared {len(comparisons)} indicators across {len(company_ids)} companies "
            f"for year {year}"
        )
        
        return ComparisonListResponse(
            comparisons=comparisons,
            total_indicators=len(comparisons),
            year=year,
            company_count=len(company_ids),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing indicators: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to compare indicators"
        )


@router.get("/indicators/{indicator_id}", response_model=IndicatorDetailResponse)
def get_indicator_detail(
    indicator_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific extracted indicator including citations.
    
    Args:
        indicator_id: Extracted indicator ID
        db: Database session
        
    Returns:
        IndicatorDetailResponse: Detailed indicator information with source citations
        
    Raises:
        HTTPException: 404 if indicator not found
        
    Example:
        GET /api/indicators/123
    """
    try:
        # Query indicator with joins
        result = db.query(
            ExtractedIndicator,
            BRSRIndicator,
            CompanyCatalog
        ).join(
            BRSRIndicator,
            ExtractedIndicator.indicator_id == BRSRIndicator.id
        ).join(
            CompanyCatalog,
            ExtractedIndicator.company_id == CompanyCatalog.id
        ).filter(
            ExtractedIndicator.id == indicator_id
        ).first()
        
        if not result:
            logger.warning(f"Indicator not found: id={indicator_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Indicator with id {indicator_id} not found"
            )
        
        extracted, brsr, company = result
        
        # Build citations from source pages and chunk IDs
        citations = []
        if extracted.source_pages and extracted.source_chunk_ids:
            # Group chunks by page
            page_chunks = {}
            for page, chunk_id in zip(extracted.source_pages, extracted.source_chunk_ids):
                if page not in page_chunks:
                    page_chunks[page] = []
                page_chunks[page].append(chunk_id)
            
            # Fetch chunk texts from database
            for page, chunk_ids in page_chunks.items():
                # Get chunk texts for these IDs
                chunks = db.query(DocumentEmbedding).filter(
                    DocumentEmbedding.id.in_(chunk_ids)
                ).all()
                
                if chunks:
                    # Combine chunk texts
                    chunk_text = " ... ".join([chunk.chunk_text for chunk in chunks])
                    
                    citations.append(
                        CitationResponse(
                            pdf_name=extracted.object_key,
                            pages=[page],
                            chunk_text=chunk_text[:500] + "..." if len(chunk_text) > 500 else chunk_text,
                            chunk_ids=chunk_ids,
                        )
                    )
        
        logger.info(
            f"Retrieved indicator detail: id={indicator_id}, "
            f"company={company.company_name}, citations={len(citations)}"
        )
        
        return IndicatorDetailResponse(
            id=extracted.id,
            indicator_id=extracted.indicator_id,
            indicator_code=brsr.indicator_code,
            parameter_name=brsr.parameter_name,
            attribute_number=brsr.attribute_number,
            pillar=brsr.pillar,
            extracted_value=extracted.extracted_value,
            numeric_value=extracted.numeric_value,
            measurement_unit=brsr.measurement_unit,
            confidence_score=extracted.confidence_score,
            validation_status=extracted.validation_status,
            extracted_at=extracted.extracted_at,
            report_year=extracted.report_year,
            object_key=extracted.object_key,
            company_id=company.id,
            company_name=company.company_name,
            description=brsr.description,
            citations=citations,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving indicator {indicator_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve indicator details"
        )
