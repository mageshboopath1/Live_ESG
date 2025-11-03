"""Pydantic schemas for score endpoints."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class PillarScoreResponse(BaseModel):
    """Response model for individual pillar score."""

    pillar: str = Field(..., description="Pillar name (Environmental, Social, or Governance)")
    pillar_code: str = Field(..., description="Pillar code (E, S, or G)")
    score: Optional[Decimal] = Field(None, description="Pillar score (0-100)")
    weight: Decimal = Field(..., description="Weight applied to this pillar in overall score calculation")

    class Config:
        """Pydantic config."""
        from_attributes = True


class ScoreResponse(BaseModel):
    """Response model for ESG scores."""

    id: int = Field(..., description="Score record ID")
    company_id: int = Field(..., description="Company ID")
    company_name: str = Field(..., description="Company name")
    report_year: int = Field(..., description="Report year")
    environmental_score: Optional[Decimal] = Field(None, description="Environmental pillar score (0-100)")
    social_score: Optional[Decimal] = Field(None, description="Social pillar score (0-100)")
    governance_score: Optional[Decimal] = Field(None, description="Governance pillar score (0-100)")
    overall_score: Optional[Decimal] = Field(None, description="Overall ESG score (0-100)")
    calculated_at: datetime = Field(..., description="Score calculation timestamp")

    class Config:
        """Pydantic config."""
        from_attributes = True


class IndicatorContribution(BaseModel):
    """Response model for indicator contribution to pillar score."""

    indicator_id: int = Field(..., description="BRSR indicator definition ID")
    indicator_code: str = Field(..., description="Indicator code")
    parameter_name: str = Field(..., description="Indicator parameter name")
    extracted_value: str = Field(..., description="Extracted value as text")
    numeric_value: Optional[Decimal] = Field(None, description="Numeric value if applicable")
    measurement_unit: Optional[str] = Field(None, description="Unit of measurement")
    weight: Decimal = Field(..., description="Weight of this indicator in pillar calculation")
    confidence_score: Optional[Decimal] = Field(None, description="Confidence score (0.0-1.0)")
    validation_status: str = Field(..., description="Validation status (valid, invalid, pending)")
    source_pages: List[int] = Field(default_factory=list, description="Source page numbers")
    object_key: str = Field(..., description="Source document object key")

    class Config:
        """Pydantic config."""
        from_attributes = True


class PillarBreakdown(BaseModel):
    """Response model for pillar score breakdown."""

    pillar: str = Field(..., description="Pillar name (Environmental, Social, or Governance)")
    pillar_code: str = Field(..., description="Pillar code (E, S, or G)")
    score: Optional[Decimal] = Field(None, description="Pillar score (0-100)")
    weight: Decimal = Field(..., description="Weight applied to this pillar in overall score calculation")
    indicators: List[IndicatorContribution] = Field(default_factory=list, description="Indicators contributing to this pillar")
    indicator_count: int = Field(..., description="Number of indicators in this pillar")
    calculation_method: str = Field(..., description="Method used to calculate pillar score")

    class Config:
        """Pydantic config."""
        from_attributes = True


class ScoreBreakdownResponse(BaseModel):
    """Response model for detailed score breakdown with full transparency."""

    company_id: int = Field(..., description="Company ID")
    company_name: str = Field(..., description="Company name")
    report_year: int = Field(..., description="Report year")
    overall_score: Optional[Decimal] = Field(None, description="Overall ESG score (0-100)")
    pillars: List[PillarBreakdown] = Field(..., description="Breakdown by pillar with indicator contributions")
    calculation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional calculation metadata")
    calculated_at: datetime = Field(..., description="Score calculation timestamp")
    total_indicators: int = Field(..., description="Total number of indicators used in calculation")

    class Config:
        """Pydantic config."""
        from_attributes = True
