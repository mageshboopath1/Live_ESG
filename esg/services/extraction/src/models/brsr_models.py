"""
Pydantic models for BRSR Core indicator definitions and extraction.

This module defines the data models used throughout the extraction service:
- BRSRIndicatorDefinition: Schema for BRSR Core indicator definitions from the database
- ExtractedIndicator: Model for storing extracted indicator values with validation
- BRSRIndicatorOutput: Structured output model for LLM extraction responses

Requirements: 6.3, 13.1, 14.2
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Pillar(str, Enum):
    """ESG pillar classification for BRSR indicators."""

    ENVIRONMENTAL = "E"
    SOCIAL = "S"
    GOVERNANCE = "G"


class BRSRIndicatorDefinition(BaseModel):
    """
    Model for BRSR Core indicator definitions loaded from the database.

    This model represents the schema of BRSR Core indicators as defined in the
    official BRSR framework, including all 9 attributes and ~50 indicators.
    """

    indicator_code: str = Field(
        ...,
        description="Unique code identifying the BRSR indicator (e.g., 'GHG_SCOPE1')",
    )
    attribute_number: int = Field(
        ...,
        ge=1,
        le=9,
        description="BRSR attribute number (1-9) this indicator belongs to",
    )
    parameter_name: str = Field(
        ..., description="Human-readable name of the parameter being measured"
    )
    measurement_unit: Optional[str] = Field(
        None, description="Unit of measurement (e.g., 'MT CO2e', 'MWh', '%')"
    )
    description: str = Field(
        ..., description="Detailed description of what this indicator measures"
    )
    pillar: Pillar = Field(
        ..., description="ESG pillar: Environmental (E), Social (S), or Governance (G)"
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weight of this indicator in score calculation (0.0-1.0)",
    )
    data_assurance_approach: str = Field(
        ..., description="Approach for data assurance as per BRSR framework"
    )
    brsr_reference: str = Field(
        ...,
        description="Cross-reference to BRSR Essential Indicators questions",
    )

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True


class ExtractedIndicator(BaseModel):
    """
    Model for extracted indicator values with validation and source citations.

    This model is used to store extracted indicator values in the database,
    including confidence scores, validation status, and source citations for
    transparency and traceability.

    Requirements: 6.3, 13.1, 14.2
    """

    object_key: str = Field(
        ...,
        description="MinIO object key identifying the source document (e.g., 'RELIANCE/2024_BRSR.pdf')",
    )
    company_id: int = Field(
        ..., description="Foreign key reference to company_catalog table"
    )
    report_year: int = Field(
        ..., ge=2000, le=2100, description="Year of the report (e.g., 2024)"
    )
    indicator_id: int = Field(
        ..., description="Foreign key reference to brsr_indicators table"
    )
    extracted_value: str = Field(
        ...,
        description="Raw extracted value as text (e.g., '1250 MT CO2e', 'Yes', '45%')",
    )
    numeric_value: Optional[float] = Field(
        None,
        description="Numeric representation of the value if applicable (e.g., 1250.0)",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="LLM confidence score for this extraction (0.0-1.0)",
    )
    validation_status: str = Field(
        default="pending",
        description="Validation status: 'valid', 'invalid', or 'pending'",
    )
    source_pages: List[int] = Field(
        default_factory=list,
        description="List of PDF page numbers where this indicator was found",
    )
    source_chunk_ids: List[int] = Field(
        default_factory=list,
        description="List of document_embeddings IDs used for extraction",
    )

    @field_validator("validation_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate that status is one of the allowed values."""
        allowed_statuses = {"valid", "invalid", "pending"}
        if v not in allowed_statuses:
            raise ValueError(
                f"validation_status must be one of {allowed_statuses}, got '{v}'"
            )
        return v

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence score is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence_score must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("source_pages")
    @classmethod
    def validate_source_pages(cls, v: List[int]) -> List[int]:
        """Ensure all page numbers are positive."""
        if any(page < 1 for page in v):
            raise ValueError("All page numbers must be positive integers")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "object_key": "RELIANCE/2024_BRSR.pdf",
                "company_id": 1,
                "report_year": 2024,
                "indicator_id": 5,
                "extracted_value": "1250 MT CO2e",
                "numeric_value": 1250.0,
                "confidence_score": 0.95,
                "validation_status": "valid",
                "source_pages": [45, 46],
                "source_chunk_ids": [123, 124, 125],
            }
        }


class BRSRIndicatorOutput(BaseModel):
    """
    Structured output model for LLM extraction responses.

    This model is used with LangChain's PydanticOutputParser to ensure the LLM
    returns structured, validated data for each indicator extraction. It includes
    all necessary fields for transparency and traceability.

    Requirements: 6.3, 13.1, 14.2
    """

    indicator_code: str = Field(
        ...,
        description="The BRSR indicator code being extracted (e.g., 'GHG_SCOPE1')",
    )
    value: str = Field(
        ...,
        description="The extracted value as found in the document (e.g., '1250 MT CO2e')",
    )
    numeric_value: Optional[float] = Field(
        None,
        description="Numeric representation if the value is quantitative (e.g., 1250.0)",
    )
    unit: str = Field(
        ...,
        description="Unit of measurement (e.g., 'MT CO2e', 'MWh', '%', 'N/A' for qualitative)",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this extraction (0.0 = no confidence, 1.0 = very confident)",
    )
    source_pages: List[int] = Field(
        ...,
        description="List of page numbers where this information was found",
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence score is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("source_pages")
    @classmethod
    def validate_source_pages(cls, v: List[int]) -> List[int]:
        """Ensure all page numbers are positive and list is not empty."""
        if not v:
            raise ValueError("source_pages cannot be empty")
        if any(page < 1 for page in v):
            raise ValueError("All page numbers must be positive integers")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "indicator_code": "GHG_SCOPE1",
                "value": "1250 MT CO2e",
                "numeric_value": 1250.0,
                "unit": "MT CO2e",
                "confidence": 0.95,
                "source_pages": [45, 46],
            }
        }
