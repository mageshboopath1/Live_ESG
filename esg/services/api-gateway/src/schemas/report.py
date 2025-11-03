"""Pydantic schemas for report endpoints."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ReportResponse(BaseModel):
    """Response model for report data."""

    id: int = Field(..., description="Report ID")
    company_id: int = Field(..., description="Company ID")
    company_name: str = Field(..., description="Company name")
    source: str = Field(..., description="Report source (NSE, MCA, etc.)")
    file_path: str = Field(..., description="MinIO object key/file path")
    file_type: str = Field(..., description="File type (pdf, csv, json)")
    ingested_at: datetime = Field(..., description="Ingestion timestamp")
    status: str = Field(..., description="Processing status")
    report_year: Optional[int] = Field(None, description="Report year extracted from file path")
    report_type: Optional[str] = Field(None, description="Report type extracted from file path")
    has_embeddings: bool = Field(False, description="Whether embeddings have been generated")
    has_extractions: bool = Field(False, description="Whether indicators have been extracted")
    extraction_count: int = Field(0, description="Number of indicators extracted")

    class Config:
        """Pydantic config."""
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    """Detailed response model for single report with additional metadata."""

    embedding_count: int = Field(0, description="Number of embeddings generated")
    page_count: Optional[int] = Field(None, description="Number of pages in document")
    chunk_count: Optional[int] = Field(None, description="Number of text chunks")

    class Config:
        """Pydantic config."""
        from_attributes = True


class ReportListResponse(BaseModel):
    """Response model for paginated report list."""

    reports: List[ReportResponse] = Field(..., description="List of reports")
    total: int = Field(..., description="Total number of reports matching the query")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    class Config:
        """Pydantic config."""
        from_attributes = True


class TriggerProcessingRequest(BaseModel):
    """Request model for triggering report processing."""

    object_key: str = Field(..., description="MinIO object key for the document to process")
    force_reprocess: bool = Field(False, description="Force reprocessing even if already processed")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "object_key": "RELIANCE/2024_BRSR.pdf",
                "force_reprocess": False
            }
        }


class TriggerProcessingResponse(BaseModel):
    """Response model for trigger processing endpoint."""

    message: str = Field(..., description="Status message")
    object_key: str = Field(..., description="Object key that was queued for processing")
    queued: bool = Field(..., description="Whether the task was successfully queued")
    already_processed: bool = Field(False, description="Whether the document was already processed")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "message": "Document queued for extraction processing",
                "object_key": "RELIANCE/2024_BRSR.pdf",
                "queued": True,
                "already_processed": False
            }
        }
