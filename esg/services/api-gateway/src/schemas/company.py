"""Pydantic schemas for company endpoints."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CompanyResponse(BaseModel):
    """Response model for company data."""

    id: int = Field(..., description="Company ID")
    company_name: str = Field(..., description="Company name")
    symbol: str = Field(..., description="Stock symbol")
    industry: Optional[str] = Field(None, description="Industry sector")
    isin_code: str = Field(..., description="ISIN code")
    series: Optional[str] = Field(None, description="Stock series")

    class Config:
        """Pydantic config."""
        from_attributes = True


class CompanyDetailResponse(CompanyResponse):
    """Detailed response model for single company with additional metadata."""

    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")
    report_count: int = Field(0, description="Number of reports ingested for this company")
    indicator_count: int = Field(0, description="Number of indicators extracted for this company")
    available_years: List[int] = Field(default_factory=list, description="Years with available data")

    class Config:
        """Pydantic config."""
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Response model for paginated company list."""

    companies: List[CompanyResponse] = Field(..., description="List of companies")
    total: int = Field(..., description="Total number of companies matching the query")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    class Config:
        """Pydantic config."""
        from_attributes = True
