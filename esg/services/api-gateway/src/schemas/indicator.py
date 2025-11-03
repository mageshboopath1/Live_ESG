"""Pydantic schemas for indicator endpoints."""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    """Response model for source citations."""

    pdf_name: str = Field(..., description="PDF file name/object key")
    pages: List[int] = Field(..., description="Page numbers where data was found")
    chunk_text: str = Field(..., description="Relevant text chunk from the document")
    chunk_ids: List[int] = Field(..., description="Chunk IDs in the embeddings table")

    class Config:
        """Pydantic config."""
        from_attributes = True


class IndicatorResponse(BaseModel):
    """Response model for indicator data."""

    id: int = Field(..., description="Extracted indicator ID")
    indicator_id: int = Field(..., description="BRSR indicator definition ID")
    indicator_code: str = Field(..., description="Indicator code (e.g., GHG_SCOPE1)")
    parameter_name: str = Field(..., description="Indicator parameter name")
    attribute_number: int = Field(..., description="BRSR attribute number (1-9)")
    pillar: str = Field(..., description="ESG pillar (E, S, or G)")
    extracted_value: str = Field(..., description="Extracted value as text")
    numeric_value: Optional[Decimal] = Field(None, description="Numeric value if applicable")
    measurement_unit: Optional[str] = Field(None, description="Unit of measurement")
    confidence_score: Optional[Decimal] = Field(None, description="Confidence score (0.0-1.0)")
    validation_status: str = Field(..., description="Validation status (valid, invalid, pending)")
    extracted_at: datetime = Field(..., description="Extraction timestamp")
    report_year: int = Field(..., description="Report year")
    object_key: str = Field(..., description="Source document object key")

    class Config:
        """Pydantic config."""
        from_attributes = True


class IndicatorDetailResponse(IndicatorResponse):
    """Detailed response model for single indicator with citations."""

    company_id: int = Field(..., description="Company ID")
    company_name: str = Field(..., description="Company name")
    description: Optional[str] = Field(None, description="Indicator description")
    citations: List[CitationResponse] = Field(default_factory=list, description="Source citations")

    class Config:
        """Pydantic config."""
        from_attributes = True


class IndicatorListResponse(BaseModel):
    """Response model for paginated indicator list."""

    indicators: List[IndicatorResponse] = Field(..., description="List of indicators")
    total: int = Field(..., description="Total number of indicators matching the query")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    class Config:
        """Pydantic config."""
        from_attributes = True


class CompanyIndicatorComparison(BaseModel):
    """Response model for a single company's indicator in comparison view."""

    company_id: int = Field(..., description="Company ID")
    company_name: str = Field(..., description="Company name")
    indicator_id: int = Field(..., description="BRSR indicator definition ID")
    indicator_code: str = Field(..., description="Indicator code")
    parameter_name: str = Field(..., description="Indicator parameter name")
    extracted_value: Optional[str] = Field(None, description="Extracted value as text")
    numeric_value: Optional[Decimal] = Field(None, description="Numeric value if applicable")
    measurement_unit: Optional[str] = Field(None, description="Unit of measurement")
    confidence_score: Optional[Decimal] = Field(None, description="Confidence score (0.0-1.0)")
    validation_status: Optional[str] = Field(None, description="Validation status")
    has_data: bool = Field(..., description="Whether data exists for this company")

    class Config:
        """Pydantic config."""
        from_attributes = True


class IndicatorComparisonResponse(BaseModel):
    """Response model for multi-company indicator comparison."""

    indicator_code: str = Field(..., description="Indicator code being compared")
    parameter_name: str = Field(..., description="Indicator parameter name")
    attribute_number: int = Field(..., description="BRSR attribute number (1-9)")
    pillar: str = Field(..., description="ESG pillar (E, S, or G)")
    measurement_unit: Optional[str] = Field(None, description="Unit of measurement")
    year: int = Field(..., description="Report year for comparison")
    companies: List[CompanyIndicatorComparison] = Field(..., description="Company-specific data")

    class Config:
        """Pydantic config."""
        from_attributes = True


class ComparisonListResponse(BaseModel):
    """Response model for list of indicator comparisons."""

    comparisons: List[IndicatorComparisonResponse] = Field(..., description="List of indicator comparisons")
    total_indicators: int = Field(..., description="Total number of indicators compared")
    year: int = Field(..., description="Report year")
    company_count: int = Field(..., description="Number of companies in comparison")

    class Config:
        """Pydantic config."""
        from_attributes = True
