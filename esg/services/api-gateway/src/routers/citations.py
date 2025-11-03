"""Citation endpoints for API Gateway."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_
import boto3
from botocore.exceptions import ClientError

from ..db.connection import get_db
from ..db.models import ExtractedIndicator, DocumentEmbedding
from ..schemas.indicator import CitationResponse
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["citations"],
)


def get_minio_client():
    """
    Create and return a MinIO/S3 client.
    
    Returns:
        boto3.client: S3 client configured for MinIO
    """
    return boto3.client(
        's3',
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}" if not settings.MINIO_SECURE else f"https://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name='us-east-1',  # MinIO doesn't care about region but boto3 requires it
    )


@router.get("/citations/{extracted_indicator_id}", response_model=List[CitationResponse])
def get_indicator_citations(
    extracted_indicator_id: int = Path(..., description="Extracted indicator ID"),
    db: Session = Depends(get_db),
):
    """
    Get source citations for a specific extracted indicator.
    
    Retrieves all source citations including PDF name, page numbers, and chunk text
    for the specified extracted indicator. Citations are grouped by page number.
    
    Args:
        extracted_indicator_id: Extracted indicator ID
        db: Database session
        
    Returns:
        List[CitationResponse]: List of citations with PDF info, pages, and chunk text
        
    Raises:
        HTTPException: 404 if indicator not found
        
    Example:
        GET /api/citations/123
        
        Response:
        [
            {
                "pdf_name": "RELIANCE/2024_BRSR.pdf",
                "pages": [45, 46],
                "chunk_text": "Our total Scope 1 emissions for FY 2024 were 1,250 MT CO2e...",
                "chunk_ids": [1234, 1235]
            }
        ]
    """
    try:
        # Query the extracted indicator
        extracted = db.query(ExtractedIndicator).filter(
            ExtractedIndicator.id == extracted_indicator_id
        ).first()
        
        if not extracted:
            logger.warning(f"Extracted indicator not found: id={extracted_indicator_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Extracted indicator with id {extracted_indicator_id} not found"
            )
        
        # Build citations from source pages and chunk IDs
        citations = []
        
        if extracted.source_pages and extracted.source_chunk_ids:
            # Group chunks by page
            page_chunks = {}
            for page, chunk_id in zip(extracted.source_pages, extracted.source_chunk_ids):
                if page not in page_chunks:
                    page_chunks[page] = []
                page_chunks[page].append(chunk_id)
            
            # Fetch chunk texts from database for each page
            for page, chunk_ids in sorted(page_chunks.items()):
                # Get chunk texts for these IDs
                chunks = db.query(DocumentEmbedding).filter(
                    DocumentEmbedding.id.in_(chunk_ids)
                ).order_by(DocumentEmbedding.chunk_index).all()
                
                if chunks:
                    # Combine chunk texts with ellipsis separator
                    chunk_text = " ... ".join([chunk.chunk_text for chunk in chunks])
                    
                    citations.append(
                        CitationResponse(
                            pdf_name=extracted.object_key,
                            pages=[page],
                            chunk_text=chunk_text,
                            chunk_ids=chunk_ids,
                        )
                    )
        
        logger.info(
            f"Retrieved {len(citations)} citations for extracted_indicator_id={extracted_indicator_id}"
        )
        
        return citations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving citations for indicator {extracted_indicator_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve citations"
        )


@router.get("/documents/{object_key:path}/page/{page_number}")
def get_document_page_url(
    object_key: str = Path(..., description="MinIO object key (e.g., RELIANCE/2024_BRSR.pdf)"),
    page_number: int = Path(..., ge=1, description="Page number to retrieve"),
    db: Session = Depends(get_db),
):
    """
    Get a presigned URL for accessing a specific page of a PDF document.
    
    Returns a presigned URL that allows temporary access to the PDF document stored in MinIO.
    The URL expires after a configured time period (default: 1 hour).
    
    Args:
        object_key: MinIO object key (e.g., "RELIANCE/2024_BRSR.pdf")
        page_number: Page number to retrieve (for reference, not used in URL generation)
        db: Database session
        
    Returns:
        dict: Response containing presigned URL, object key, and page number
        
    Raises:
        HTTPException: 404 if document not found in database or MinIO
        HTTPException: 500 if error generating presigned URL
        
    Example:
        GET /api/documents/RELIANCE/2024_BRSR.pdf/page/45
        
        Response:
        {
            "url": "http://localhost:9000/esg-reports/RELIANCE/2024_BRSR.pdf?X-Amz-Algorithm=...",
            "object_key": "RELIANCE/2024_BRSR.pdf",
            "page_number": 45,
            "expires_in": 3600
        }
    """
    try:
        # Verify document exists in database
        document_exists = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.object_key == object_key
        ).first()
        
        if not document_exists:
            logger.warning(f"Document not found in database: object_key={object_key}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with object_key '{object_key}' not found"
            )
        
        # Create MinIO client
        s3_client = get_minio_client()
        
        # Check if object exists in MinIO
        try:
            s3_client.head_object(Bucket=settings.MINIO_BUCKET, Key=object_key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Document not found in MinIO: object_key={object_key}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Document file not found in storage: {object_key}"
                )
            else:
                raise
        
        # Generate presigned URL (expires in 1 hour)
        expiration = 3600  # 1 hour in seconds
        
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.MINIO_BUCKET,
                    'Key': object_key,
                },
                ExpiresIn=expiration
            )
            
            logger.info(
                f"Generated presigned URL for object_key={object_key}, page={page_number}"
            )
            
            return {
                "url": presigned_url,
                "object_key": object_key,
                "page_number": page_number,
                "expires_in": expiration,
            }
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate document access URL"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document URL for {object_key}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document URL"
        )
