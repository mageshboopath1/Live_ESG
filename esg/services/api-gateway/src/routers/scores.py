"""Score endpoints for API Gateway."""

import logging
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..db.connection import get_db
from ..db.models import (
    ESGScore,
    CompanyCatalog,
    ExtractedIndicator,
    BRSRIndicator,
)
from ..schemas.score import (
    ScoreResponse,
    ScoreBreakdownResponse,
    PillarBreakdown,
    IndicatorContribution,
)
from ..cache import cache_manager, cache_key
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["scores"],
)


@router.get("/companies/{company_id}/scores", response_model=ScoreResponse)
def get_company_scores(
    company_id: int,
    year: Optional[int] = Query(None, description="Filter by report year"),
    db: Session = Depends(get_db),
):
    """
    Get ESG scores for a specific company with caching.
    
    Args:
        company_id: Company ID
        year: Optional filter by report year (returns latest if not specified)
        db: Database session
        
    Returns:
        ScoreResponse: ESG scores including pillar scores and overall score
        
    Raises:
        HTTPException: 404 if company or scores not found
        
    Example:
        GET /api/companies/1/scores?year=2024
        GET /api/companies/1/scores (returns latest available year)
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
        
        # Build query for scores
        query = db.query(ESGScore).filter(ESGScore.company_id == company_id)
        
        if year is not None:
            query = query.filter(ESGScore.report_year == year)
        else:
            # Get latest year if not specified
            query = query.order_by(ESGScore.report_year.desc())
        
        score = query.first()
        
        if not score:
            year_msg = f" for year {year}" if year else ""
            logger.warning(f"Scores not found for company_id={company_id}{year_msg}")
            raise HTTPException(
                status_code=404,
                detail=f"Scores not found for company {company.company_name}{year_msg}"
            )
        
        # Try to get from cache (only cache when year is specified)
        if year is not None:
            cache_key_str = cache_key("scores", company_id, year)
            cached_data = cache_manager.get(cache_key_str)
            
            if cached_data:
                logger.debug(f"Cache hit for scores: company_id={company_id}, year={year}")
                return ScoreResponse(**cached_data)
        
        logger.info(
            f"Retrieved scores for company_id={company_id}, year={score.report_year}, "
            f"overall_score={score.overall_score}"
        )
        
        response = ScoreResponse(
            id=score.id,
            company_id=score.company_id,
            company_name=company.company_name,
            report_year=score.report_year,
            environmental_score=score.environmental_score,
            social_score=score.social_score,
            governance_score=score.governance_score,
            overall_score=score.overall_score,
            calculated_at=score.calculated_at,
        )
        
        # Cache the response (only when year is specified)
        if year is not None:
            cache_key_str = cache_key("scores", company_id, year)
            cache_manager.set(cache_key_str, response.model_dump(), settings.CACHE_TTL_SCORES)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scores for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve scores"
        )


@router.get("/scores/breakdown/{company_id}/{year}", response_model=ScoreBreakdownResponse)
def get_score_breakdown(
    company_id: int,
    year: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed score breakdown with full transparency showing how scores are calculated.
    
    This endpoint provides complete transparency by showing:
    - Overall ESG score and how it's derived from pillar scores
    - Each pillar score (E, S, G) and the weights applied
    - All indicators contributing to each pillar with their values, weights, and source citations
    - Calculation methodology and metadata
    
    Args:
        company_id: Company ID
        year: Report year
        db: Database session
        
    Returns:
        ScoreBreakdownResponse: Detailed breakdown with all indicators and citations
        
    Raises:
        HTTPException: 404 if company or scores not found
        
    Example:
        GET /api/scores/breakdown/1/2024
    """
    # Try to get from cache
    cache_key_str = cache_key("scores:breakdown", company_id, year)
    cached_data = cache_manager.get(cache_key_str)
    
    if cached_data:
        logger.debug(f"Cache hit for score breakdown: company_id={company_id}, year={year}")
        return ScoreBreakdownResponse(**cached_data)
    
    try:
        # Verify company exists
        company = db.query(CompanyCatalog).filter(CompanyCatalog.id == company_id).first()
        if not company:
            logger.warning(f"Company not found: id={company_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Company with id {company_id} not found"
            )
        
        # Get score record
        score = db.query(ESGScore).filter(
            and_(
                ESGScore.company_id == company_id,
                ESGScore.report_year == year
            )
        ).first()
        
        if not score:
            logger.warning(f"Scores not found for company_id={company_id}, year={year}")
            raise HTTPException(
                status_code=404,
                detail=f"Scores not found for company {company.company_name} in year {year}"
            )
        
        # Get all extracted indicators for this company and year
        extracted_indicators = db.query(
            ExtractedIndicator,
            BRSRIndicator
        ).join(
            BRSRIndicator,
            ExtractedIndicator.indicator_id == BRSRIndicator.id
        ).filter(
            and_(
                ExtractedIndicator.company_id == company_id,
                ExtractedIndicator.report_year == year
            )
        ).order_by(
            BRSRIndicator.pillar,
            BRSRIndicator.attribute_number,
            BRSRIndicator.indicator_code
        ).all()
        
        # Group indicators by pillar
        pillar_indicators: Dict[str, List] = {
            'E': [],
            'S': [],
            'G': []
        }
        
        for extracted, brsr in extracted_indicators:
            pillar_indicators[brsr.pillar].append((extracted, brsr))
        
        # Get pillar weights from calculation metadata
        calculation_metadata = score.calculation_metadata or {}
        pillar_weights = calculation_metadata.get('pillar_weights', {
            'E': 0.33,
            'S': 0.33,
            'G': 0.34
        })
        
        calculation_method = calculation_metadata.get('calculation_method', 'weighted_average')
        
        # Build pillar breakdowns
        pillars = []
        total_indicators = 0
        
        pillar_names = {
            'E': 'Environmental',
            'S': 'Social',
            'G': 'Governance'
        }
        
        pillar_scores = {
            'E': score.environmental_score,
            'S': score.social_score,
            'G': score.governance_score
        }
        
        for pillar_code in ['E', 'S', 'G']:
            indicators_list = []
            
            for extracted, brsr in pillar_indicators[pillar_code]:
                indicators_list.append(
                    IndicatorContribution(
                        indicator_id=brsr.id,
                        indicator_code=brsr.indicator_code,
                        parameter_name=brsr.parameter_name,
                        extracted_value=extracted.extracted_value,
                        numeric_value=extracted.numeric_value,
                        measurement_unit=brsr.measurement_unit,
                        weight=brsr.weight,
                        confidence_score=extracted.confidence_score,
                        validation_status=extracted.validation_status,
                        source_pages=extracted.source_pages or [],
                        object_key=extracted.object_key,
                    )
                )
            
            total_indicators += len(indicators_list)
            
            pillars.append(
                PillarBreakdown(
                    pillar=pillar_names[pillar_code],
                    pillar_code=pillar_code,
                    score=pillar_scores[pillar_code],
                    weight=pillar_weights.get(pillar_code, 0.33),
                    indicators=indicators_list,
                    indicator_count=len(indicators_list),
                    calculation_method=calculation_method,
                )
            )
        
        logger.info(
            f"Retrieved score breakdown for company_id={company_id}, year={year}, "
            f"total_indicators={total_indicators}"
        )
        
        response = ScoreBreakdownResponse(
            company_id=company.id,
            company_name=company.company_name,
            report_year=year,
            overall_score=score.overall_score,
            pillars=pillars,
            calculation_metadata=calculation_metadata,
            calculated_at=score.calculated_at,
            total_indicators=total_indicators,
        )
        
        # Cache the response
        cache_key_str = cache_key("scores:breakdown", company_id, year)
        cache_manager.set(cache_key_str, response.model_dump(), settings.CACHE_TTL_SCORES)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving score breakdown for company {company_id}, year {year}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve score breakdown"
        )
