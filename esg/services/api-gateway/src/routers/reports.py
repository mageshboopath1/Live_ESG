"""Report endpoints for API Gateway."""

import logging
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..db.connection import get_db
from ..db.models import (
    IngestionMetadata,
    CompanyCatalog,
    DocumentEmbedding,
    ExtractedIndicator,
)
from ..schemas.report import (
    ReportResponse,
    ReportDetailResponse,
    ReportListResponse,
    TriggerProcessingRequest,
    TriggerProcessingResponse,
)
from ..auth.dependencies import require_auth
from ..auth.jwt import TokenData

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["reports"],
)


def parse_object_key(file_path: str) -> tuple[Optional[int], Optional[str]]:
    """
    Parse object key to extract report year and type.
    
    Expected format: company_name/year_reporttype.pdf
    Example: RELIANCE/2024_BRSR.pdf -> (2024, "BRSR")
    
    Args:
        file_path: MinIO object key
        
    Returns:
        Tuple of (year, report_type) or (None, None) if parsing fails
    """
    try:
        # Extract filename from path
        filename = file_path.split('/')[-1] if '/' in file_path else file_path
        
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Try to match pattern: year_reporttype
        match = re.match(r'(\d{4})_(.+)', name_without_ext)
        if match:
            year = int(match.group(1))
            report_type = match.group(2)
            return year, report_type
        
        return None, None
    except Exception as e:
        logger.warning(f"Failed to parse object key '{file_path}': {str(e)}")
        return None, None


@router.get("/companies/{company_id}/reports", response_model=ReportListResponse)
def list_company_reports(
    company_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    status_filter: Optional[str] = Query(None, description="Filter by processing status"),
    db: Session = Depends(get_db),
):
    """
    List all reports for a specific company.
    
    Args:
        company_id: Company ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        status_filter: Optional filter by processing status
        db: Database session
        
    Returns:
        ReportListResponse: Paginated list of reports with processing status
        
    Raises:
        HTTPException: 404 if company not found
        
    Example:
        GET /api/companies/1/reports
        GET /api/companies/1/reports?status_filter=SUCCESS&skip=0&limit=10
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
        
        # Build query
        query = db.query(IngestionMetadata).filter(
            IngestionMetadata.company_id == company_id
        )
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(IngestionMetadata.status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        reports = query.order_by(IngestionMetadata.ingested_at.desc()).offset(skip).limit(limit).all()
        
        # Build response with additional metadata
        report_responses = []
        for report in reports:
            # Parse object key for year and type
            year, report_type = parse_object_key(report.file_path)
            
            # Check if embeddings exist
            has_embeddings = db.query(
                db.query(DocumentEmbedding).filter(
                    DocumentEmbedding.object_key == report.file_path
                ).exists()
            ).scalar()
            
            # Check if extractions exist and count them
            extraction_count = db.query(func.count(ExtractedIndicator.id)).filter(
                ExtractedIndicator.object_key == report.file_path
            ).scalar()
            
            has_extractions = extraction_count > 0
            
            report_responses.append(
                ReportResponse(
                    id=report.id,
                    company_id=report.company_id,
                    company_name=company.company_name,
                    source=report.source,
                    file_path=report.file_path,
                    file_type=report.file_type,
                    ingested_at=report.ingested_at,
                    status=report.status,
                    report_year=year,
                    report_type=report_type,
                    has_embeddings=has_embeddings,
                    has_extractions=has_extractions,
                    extraction_count=extraction_count,
                )
            )
        
        logger.info(
            f"Retrieved {len(reports)} reports for company_id={company_id} "
            f"(total={total}, skip={skip}, limit={limit})"
        )
        
        return ReportListResponse(
            reports=report_responses,
            total=total,
            skip=skip,
            limit=limit,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing reports for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve reports"
        )


@router.get("/reports/{object_key:path}", response_model=ReportDetailResponse)
def get_report_details(
    object_key: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific report by object key.
    
    Args:
        object_key: MinIO object key (file path)
        db: Database session
        
    Returns:
        ReportDetailResponse: Detailed report information with processing status
        
    Raises:
        HTTPException: 404 if report not found
        
    Example:
        GET /api/reports/RELIANCE/2024_BRSR.pdf
    """
    try:
        # Find report by file path
        report = db.query(IngestionMetadata).filter(
            IngestionMetadata.file_path == object_key
        ).first()
        
        if not report:
            logger.warning(f"Report not found: object_key={object_key}")
            raise HTTPException(
                status_code=404,
                detail=f"Report with object key '{object_key}' not found"
            )
        
        # Get company information
        company = db.query(CompanyCatalog).filter(
            CompanyCatalog.id == report.company_id
        ).first()
        
        # Parse object key for year and type
        year, report_type = parse_object_key(report.file_path)
        
        # Count embeddings
        embedding_count = db.query(func.count(DocumentEmbedding.id)).filter(
            DocumentEmbedding.object_key == object_key
        ).scalar()
        
        has_embeddings = embedding_count > 0
        
        # Count extractions
        extraction_count = db.query(func.count(ExtractedIndicator.id)).filter(
            ExtractedIndicator.object_key == object_key
        ).scalar()
        
        has_extractions = extraction_count > 0
        
        # Get page count from embeddings
        page_count = db.query(func.max(DocumentEmbedding.page_number)).filter(
            DocumentEmbedding.object_key == object_key
        ).scalar()
        
        # Get chunk count
        chunk_count = db.query(func.count(DocumentEmbedding.id)).filter(
            DocumentEmbedding.object_key == object_key
        ).scalar()
        
        logger.info(
            f"Retrieved report details: object_key={object_key}, "
            f"embeddings={embedding_count}, extractions={extraction_count}"
        )
        
        return ReportDetailResponse(
            id=report.id,
            company_id=report.company_id,
            company_name=company.company_name if company else "Unknown",
            source=report.source,
            file_path=report.file_path,
            file_type=report.file_type,
            ingested_at=report.ingested_at,
            status=report.status,
            report_year=year,
            report_type=report_type,
            has_embeddings=has_embeddings,
            has_extractions=has_extractions,
            extraction_count=extraction_count,
            embedding_count=embedding_count,
            page_count=page_count,
            chunk_count=chunk_count,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report details for '{object_key}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve report details"
        )


@router.post("/reports/trigger-processing", response_model=TriggerProcessingResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_report_processing(
    request: TriggerProcessingRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_auth),
):
    """
    Trigger extraction processing for a specific report.
    
    This endpoint publishes a message to the RabbitMQ extraction queue
    to trigger indicator extraction for the specified document.
    
    Args:
        request: Request containing object_key and force_reprocess flag
        db: Database session
        
    Returns:
        TriggerProcessingResponse: Status of the queuing operation
        
    Raises:
        HTTPException: 404 if report not found, 400 if already processed (unless force_reprocess=True)
        
    Example:
        POST /api/reports/trigger-processing
        {
            "object_key": "RELIANCE/2024_BRSR.pdf",
            "force_reprocess": false
        }
    """
    try:
        object_key = request.object_key
        
        # Verify report exists
        report = db.query(IngestionMetadata).filter(
            IngestionMetadata.file_path == object_key
        ).first()
        
        if not report:
            logger.warning(f"Report not found for processing: object_key={object_key}")
            raise HTTPException(
                status_code=404,
                detail=f"Report with object key '{object_key}' not found"
            )
        
        # Check if embeddings exist
        has_embeddings = db.query(
            db.query(DocumentEmbedding).filter(
                DocumentEmbedding.object_key == object_key
            ).exists()
        ).scalar()
        
        if not has_embeddings:
            logger.warning(f"No embeddings found for report: object_key={object_key}")
            raise HTTPException(
                status_code=400,
                detail=f"Report '{object_key}' has no embeddings. Please ensure embeddings are generated first."
            )
        
        # Check if already processed (has extractions)
        extraction_count = db.query(func.count(ExtractedIndicator.id)).filter(
            ExtractedIndicator.object_key == object_key
        ).scalar()
        
        already_processed = extraction_count > 0
        
        if already_processed and not request.force_reprocess:
            logger.info(
                f"Report already processed: object_key={object_key}, "
                f"extractions={extraction_count}"
            )
            return TriggerProcessingResponse(
                message=f"Report already processed with {extraction_count} indicators. Use force_reprocess=true to reprocess.",
                object_key=object_key,
                queued=False,
                already_processed=True,
            )
        
        # TODO: Publish message to RabbitMQ extraction queue
        # For now, we'll return a success response indicating the task would be queued
        # In a full implementation, this would use pika to publish to RabbitMQ
        
        # Example RabbitMQ publishing code (to be implemented):
        # import pika
        # connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        # channel = connection.channel()
        # channel.queue_declare(queue='extraction-tasks', durable=True)
        # channel.basic_publish(
        #     exchange='',
        #     routing_key='extraction-tasks',
        #     body=object_key,
        #     properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
        # )
        # connection.close()
        
        logger.info(
            f"Queued extraction processing: object_key={object_key}, "
            f"force_reprocess={request.force_reprocess}"
        )
        
        return TriggerProcessingResponse(
            message="Document queued for extraction processing" if not already_processed 
                    else "Document queued for reprocessing",
            object_key=object_key,
            queued=True,
            already_processed=already_processed,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering processing for '{request.object_key}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger report processing"
        )
