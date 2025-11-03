"""
Database repository for BRSR indicator extraction service.

This module provides functions for:
- Loading BRSR indicator definitions from the database
- Parsing object keys to extract company and year information
- Storing extracted indicators with source citations
- Checking if documents have already been processed
- Transaction handling for atomic batch inserts

Requirements: 6.4, 8.2, 12.4
"""

import logging
import re
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_batch

from ..config import config
from ..models.brsr_models import BRSRIndicatorDefinition, ExtractedIndicator

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Provides a database connection with automatic cleanup.
    
    Yields:
        psycopg2.connection: Database connection object
        
    Example:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM brsr_indicators")
    """
    conn = None
    try:
        conn = psycopg2.connect(config.database_url)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def load_brsr_indicators() -> List[BRSRIndicatorDefinition]:
    """
    Load all BRSR Core indicator definitions from the database.
    
    Retrieves all indicator definitions from the brsr_indicators table
    and returns them as validated Pydantic models.
    
    Returns:
        List[BRSRIndicatorDefinition]: List of BRSR indicator definitions
        
    Raises:
        psycopg2.Error: If database query fails
        
    Requirements: 6.4, 8.2
    """
    logger.info("Loading BRSR indicator definitions from database")
    
    query = """
        SELECT 
            indicator_code,
            attribute_number,
            parameter_name,
            measurement_unit,
            description,
            pillar,
            weight,
            data_assurance_approach,
            brsr_reference
        FROM brsr_indicators
        ORDER BY attribute_number, indicator_code
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                
                indicators = []
                for row in rows:
                    indicator = BRSRIndicatorDefinition(
                        indicator_code=row[0],
                        attribute_number=row[1],
                        parameter_name=row[2],
                        measurement_unit=row[3],
                        description=row[4],
                        pillar=row[5],
                        weight=float(row[6]),
                        data_assurance_approach=row[7],
                        brsr_reference=row[8],
                    )
                    indicators.append(indicator)
                
                logger.info(f"Loaded {len(indicators)} BRSR indicator definitions")
                return indicators
                
    except psycopg2.Error as e:
        logger.error(f"Failed to load BRSR indicators: {e}")
        raise


def parse_object_key(object_key: str) -> Tuple[str, int]:
    """
    Parse object key to extract company name and report year.
    
    Object keys can follow multiple formats:
    - Format 1: {company_name}/{year}_{report_type}.pdf (e.g., "RELIANCE/2024_BRSR.pdf")
    - Format 2: {company_name}/{year_range}/{filename}.pdf (e.g., "ADANIPORTS/2023_2024/report.pdf")
    
    Args:
        object_key: MinIO object key
        
    Returns:
        Tuple[str, int]: (company_name, report_year)
        
    Raises:
        ValueError: If object key format is invalid
        
    Requirements: 6.4
    """
    logger.debug(f"Parsing object key: {object_key}")
    
    # Try Format 1: company_name/year_reporttype.pdf
    pattern1 = r"^([^/]+)/(\d{4})_[^/]+\.pdf$"
    match = re.match(pattern1, object_key)
    
    if match:
        company_name = match.group(1)
        report_year = int(match.group(2))
        logger.debug(f"Parsed (Format 1): company={company_name}, year={report_year}")
        return company_name, report_year
    
    # Try Format 2: company_name/year_year/filename.pdf
    pattern2 = r"^([^/]+)/(\d{4})_\d{4}/[^/]+\.pdf$"
    match = re.match(pattern2, object_key)
    
    if match:
        company_name = match.group(1)
        report_year = int(match.group(2))  # Use the first year from the range
        logger.debug(f"Parsed (Format 2): company={company_name}, year={report_year}")
        return company_name, report_year
    
    # If neither format matches, raise an error
    raise ValueError(
        f"Invalid object key format: {object_key}. "
        f"Expected format: company_name/year_reporttype.pdf or company_name/year_year/filename.pdf"
    )


def get_company_id_by_name(company_name: str) -> Optional[int]:
    """
    Retrieve company ID from company_catalog by company name.
    
    Args:
        company_name: Name of the company (e.g., "RELIANCE")
        
    Returns:
        Optional[int]: Company ID if found, None otherwise
        
    Raises:
        psycopg2.Error: If database query fails
        
    Requirements: 6.4, 8.2
    """
    logger.debug(f"Looking up company ID for: {company_name}")
    
    query = """
        SELECT id 
        FROM company_catalog 
        WHERE company_name = %s OR symbol = %s
        LIMIT 1
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (company_name, company_name))
                result = cur.fetchone()
                
                if result:
                    company_id = result[0]
                    logger.debug(f"Found company ID: {company_id}")
                    return company_id
                else:
                    logger.warning(f"Company not found: {company_name}")
                    return None
                    
    except psycopg2.Error as e:
        logger.error(f"Failed to lookup company ID: {e}")
        raise


def check_embeddings_exist(object_key: str) -> bool:
    """
    Check if embeddings exist for a document.
    
    This function verifies that embeddings have been generated and stored
    for the specified document before extraction begins. This prevents
    premature extraction attempts when embeddings are not yet ready.
    
    Args:
        object_key: MinIO object key identifying the document
        
    Returns:
        bool: True if embeddings exist for the document, False otherwise
        
    Raises:
        psycopg2.Error: If database query fails
        
    Requirements: 4.1, 4.2
    """
    logger.debug(f"Checking if embeddings exist for: {object_key}")
    
    query = """
        SELECT EXISTS(
            SELECT 1 
            FROM document_embeddings 
            WHERE object_key = %s
            LIMIT 1
        )
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (object_key,))
                result = cur.fetchone()
                embeddings_exist = result[0] if result else False
                
                logger.debug(
                    f"Embeddings exist for {object_key}: {embeddings_exist}"
                )
                return embeddings_exist
                
    except psycopg2.Error as e:
        logger.error(f"Failed to check embeddings existence: {e}")
        raise


def check_document_processed(object_key: str) -> bool:
    """
    Check if a document has already been processed for indicator extraction.
    
    A document is considered processed if there are any extracted indicators
    associated with its object key in the database.
    
    Args:
        object_key: MinIO object key identifying the document
        
    Returns:
        bool: True if document has been processed, False otherwise
        
    Raises:
        psycopg2.Error: If database query fails
        
    Requirements: 6.4, 12.4
    """
    logger.debug(f"Checking if document is processed: {object_key}")
    
    query = """
        SELECT EXISTS(
            SELECT 1 
            FROM extracted_indicators 
            WHERE object_key = %s
            LIMIT 1
        )
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (object_key,))
                result = cur.fetchone()
                is_processed = result[0] if result else False
                
                logger.debug(
                    f"Document {object_key} processed: {is_processed}"
                )
                return is_processed
                
    except psycopg2.Error as e:
        logger.error(f"Failed to check document status: {e}")
        raise


def store_extracted_indicators(
    indicators: List[ExtractedIndicator],
    batch_size: int = 100
) -> int:
    """
    Store extracted indicators in the database with atomic transaction handling.
    
    This function performs a batch insert of extracted indicators with the following features:
    - Atomic transaction: All indicators are inserted or none (rollback on error)
    - Conflict handling: ON CONFLICT DO UPDATE for idempotency
    - Batch processing: Efficient insertion of large indicator sets
    - Source citation storage: Stores page numbers and chunk IDs as PostgreSQL arrays
    
    Args:
        indicators: List of ExtractedIndicator objects to store
        batch_size: Number of records to insert per batch (default: 100)
        
    Returns:
        int: Number of indicators successfully stored
        
    Raises:
        psycopg2.Error: If database operation fails (transaction is rolled back)
        ValueError: If indicators list is empty
        
    Requirements: 6.4, 8.2, 12.4, 14.2
    """
    if not indicators:
        raise ValueError("Cannot store empty list of indicators")
    
    logger.info(f"Storing {len(indicators)} extracted indicators")
    
    # SQL query with ON CONFLICT to handle duplicate (object_key, indicator_id) pairs
    query = """
        INSERT INTO extracted_indicators (
            object_key,
            company_id,
            report_year,
            indicator_id,
            extracted_value,
            numeric_value,
            confidence_score,
            validation_status,
            source_pages,
            source_chunk_ids
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (object_key, indicator_id) 
        DO UPDATE SET
            extracted_value = EXCLUDED.extracted_value,
            numeric_value = EXCLUDED.numeric_value,
            confidence_score = EXCLUDED.confidence_score,
            validation_status = EXCLUDED.validation_status,
            source_pages = EXCLUDED.source_pages,
            source_chunk_ids = EXCLUDED.source_chunk_ids,
            extracted_at = NOW()
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Prepare data tuples for batch insert
                data = [
                    (
                        ind.object_key,
                        ind.company_id,
                        ind.report_year,
                        ind.indicator_id,
                        ind.extracted_value,
                        ind.numeric_value,
                        ind.confidence_score,
                        ind.validation_status,
                        ind.source_pages,  # PostgreSQL array
                        ind.source_chunk_ids,  # PostgreSQL array
                    )
                    for ind in indicators
                ]
                
                # Execute batch insert with transaction
                execute_batch(cur, query, data, page_size=batch_size)
                
                # Commit transaction
                conn.commit()
                
                logger.info(
                    f"Successfully stored {len(indicators)} indicators "
                    f"for object_key: {indicators[0].object_key}"
                )
                return len(indicators)
                
    except psycopg2.Error as e:
        logger.error(f"Failed to store extracted indicators: {e}")
        # Transaction is automatically rolled back by context manager
        raise


def get_indicator_id_by_code(indicator_code: str) -> Optional[int]:
    """
    Retrieve indicator ID from brsr_indicators by indicator code.
    
    Args:
        indicator_code: BRSR indicator code (e.g., "GHG_SCOPE1")
        
    Returns:
        Optional[int]: Indicator ID if found, None otherwise
        
    Raises:
        psycopg2.Error: If database query fails
        
    Requirements: 6.4, 8.2
    """
    logger.debug(f"Looking up indicator ID for code: {indicator_code}")
    
    query = """
        SELECT id 
        FROM brsr_indicators 
        WHERE indicator_code = %s
        LIMIT 1
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (indicator_code,))
                result = cur.fetchone()
                
                if result:
                    indicator_id = result[0]
                    logger.debug(f"Found indicator ID: {indicator_id}")
                    return indicator_id
                else:
                    logger.warning(f"Indicator not found: {indicator_code}")
                    return None
                    
    except psycopg2.Error as e:
        logger.error(f"Failed to lookup indicator ID: {e}")
        raise


def get_indicators_by_attribute(attribute_number: int) -> List[BRSRIndicatorDefinition]:
    """
    Load BRSR indicators for a specific attribute number.
    
    This is useful for batch extraction where indicators are grouped by attribute.
    
    Args:
        attribute_number: BRSR attribute number (1-9)
        
    Returns:
        List[BRSRIndicatorDefinition]: List of indicators for the specified attribute
        
    Raises:
        ValueError: If attribute_number is not between 1 and 9
        psycopg2.Error: If database query fails
        
    Requirements: 6.4, 8.2, 12.1
    """
    if not 1 <= attribute_number <= 9:
        raise ValueError(f"attribute_number must be between 1 and 9, got {attribute_number}")
    
    logger.info(f"Loading indicators for attribute {attribute_number}")
    
    query = """
        SELECT 
            indicator_code,
            attribute_number,
            parameter_name,
            measurement_unit,
            description,
            pillar,
            weight,
            data_assurance_approach,
            brsr_reference
        FROM brsr_indicators
        WHERE attribute_number = %s
        ORDER BY indicator_code
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (attribute_number,))
                rows = cur.fetchall()
                
                indicators = []
                for row in rows:
                    indicator = BRSRIndicatorDefinition(
                        indicator_code=row[0],
                        attribute_number=row[1],
                        parameter_name=row[2],
                        measurement_unit=row[3],
                        description=row[4],
                        pillar=row[5],
                        weight=float(row[6]),
                        data_assurance_approach=row[7],
                        brsr_reference=row[8],
                    )
                    indicators.append(indicator)
                
                logger.info(
                    f"Loaded {len(indicators)} indicators for attribute {attribute_number}"
                )
                return indicators
                
    except psycopg2.Error as e:
        logger.error(f"Failed to load indicators for attribute {attribute_number}: {e}")
        raise


def store_esg_score(
    company_id: int,
    report_year: int,
    environmental_score: Optional[float],
    social_score: Optional[float],
    governance_score: Optional[float],
    overall_score: Optional[float],
    calculation_metadata: Dict,
) -> int:
    """
    Store ESG scores in the database with calculation metadata.
    
    This function stores the calculated ESG scores (overall and pillar scores) along with
    full calculation metadata in JSONB format for transparency. The metadata includes:
    - Pillar scores and weights
    - Detailed breakdown of indicator contributions
    - Calculation methodology description
    - Source citations for all indicators
    
    The function uses ON CONFLICT to handle duplicate (company_id, report_year) pairs,
    updating existing scores if they already exist.
    
    Args:
        company_id: Foreign key reference to company_catalog table
        report_year: Year of the report (e.g., 2024)
        environmental_score: Environmental pillar score (0-100) or None
        social_score: Social pillar score (0-100) or None
        governance_score: Governance pillar score (0-100) or None
        overall_score: Overall ESG score (0-100) or None
        calculation_metadata: Dictionary with full calculation details including:
            - pillar_scores: Individual E, S, G scores
            - pillar_weights: Weights used in calculation
            - pillar_breakdown: Detailed indicator contributions with citations
            - calculation_method: Description of methodology
            - calculated_at: Timestamp
    
    Returns:
        int: ID of the stored/updated esg_scores record
        
    Raises:
        psycopg2.Error: If database operation fails
        ValueError: If company_id or report_year is invalid
        
    Requirements: 15.4, 15.5
    """
    if company_id <= 0:
        raise ValueError(f"company_id must be positive, got {company_id}")
    if not 2000 <= report_year <= 2100:
        raise ValueError(f"report_year must be between 2000 and 2100, got {report_year}")
    
    logger.info(
        f"Storing ESG scores for company_id={company_id}, year={report_year}, "
        f"overall_score={overall_score}"
    )
    
    query = """
        INSERT INTO esg_scores (
            company_id,
            report_year,
            environmental_score,
            social_score,
            governance_score,
            overall_score,
            calculation_metadata
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (company_id, report_year)
        DO UPDATE SET
            environmental_score = EXCLUDED.environmental_score,
            social_score = EXCLUDED.social_score,
            governance_score = EXCLUDED.governance_score,
            overall_score = EXCLUDED.overall_score,
            calculation_metadata = EXCLUDED.calculation_metadata,
            calculated_at = NOW()
        RETURNING id
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Convert metadata dict to JSON
                import json
                metadata_json = json.dumps(calculation_metadata)
                
                cur.execute(
                    query,
                    (
                        company_id,
                        report_year,
                        environmental_score,
                        social_score,
                        governance_score,
                        overall_score,
                        metadata_json,
                    ),
                )
                
                result = cur.fetchone()
                score_id = result[0] if result else None
                
                # Commit transaction
                conn.commit()
                
                logger.info(
                    f"Successfully stored ESG scores with id={score_id} "
                    f"for company_id={company_id}, year={report_year}"
                )
                return score_id
                
    except psycopg2.Error as e:
        logger.error(f"Failed to store ESG scores: {e}")
        raise


def get_score_breakdown(
    company_id: int,
    report_year: int,
) -> Optional[Dict]:
    """
    Retrieve full ESG score breakdown with calculation details and citations.
    
    This function retrieves the complete ESG score record including:
    - Overall and pillar scores
    - Calculation metadata with full transparency
    - Indicator values, weights, and contributions
    - Source citations (PDF names, page numbers) for all indicators
    
    The breakdown enables users to understand exactly how the score was calculated
    and trace every data point back to its source document.
    
    Args:
        company_id: Foreign key reference to company_catalog table
        report_year: Year of the report (e.g., 2024)
    
    Returns:
        Optional[Dict]: Dictionary with complete score breakdown including:
            - id: Score record ID
            - company_id: Company ID
            - report_year: Report year
            - environmental_score: Environmental pillar score
            - social_score: Social pillar score
            - governance_score: Governance pillar score
            - overall_score: Overall ESG score
            - calculation_metadata: Full calculation details with citations
            - calculated_at: Timestamp of calculation
        Returns None if no score found for the company and year.
        
    Raises:
        psycopg2.Error: If database query fails
        ValueError: If company_id or report_year is invalid
        
    Requirements: 15.4, 15.5
    """
    if company_id <= 0:
        raise ValueError(f"company_id must be positive, got {company_id}")
    if not 2000 <= report_year <= 2100:
        raise ValueError(f"report_year must be between 2000 and 2100, got {report_year}")
    
    logger.info(
        f"Retrieving score breakdown for company_id={company_id}, year={report_year}"
    )
    
    query = """
        SELECT 
            id,
            company_id,
            report_year,
            environmental_score,
            social_score,
            governance_score,
            overall_score,
            calculation_metadata,
            calculated_at
        FROM esg_scores
        WHERE company_id = %s AND report_year = %s
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (company_id, report_year))
                result = cur.fetchone()
                
                if not result:
                    logger.warning(
                        f"No score found for company_id={company_id}, year={report_year}"
                    )
                    return None
                
                # Parse result into dictionary
                # Note: PostgreSQL JSONB is returned as dict by psycopg2, not string
                breakdown = {
                    "id": result[0],
                    "company_id": result[1],
                    "report_year": result[2],
                    "environmental_score": float(result[3]) if result[3] is not None else None,
                    "social_score": float(result[4]) if result[4] is not None else None,
                    "governance_score": float(result[5]) if result[5] is not None else None,
                    "overall_score": float(result[6]) if result[6] is not None else None,
                    "calculation_metadata": result[7] if result[7] else {},
                    "calculated_at": result[8].isoformat() if result[8] else None,
                }
                
                logger.info(
                    f"Retrieved score breakdown for company_id={company_id}, "
                    f"year={report_year}, overall_score={breakdown['overall_score']}"
                )
                return breakdown
                
    except psycopg2.Error as e:
        logger.error(f"Failed to retrieve score breakdown: {e}")
        raise


def update_document_status(
    object_key: str,
    status: str,
    error_message: Optional[str] = None,
) -> bool:
    """
    Update document processing status in ingestion_metadata table.
    
    This function updates the status of a document to track processing failures
    and provide visibility into extraction pipeline issues.
    
    Args:
        object_key: MinIO object key identifying the document
        status: Status string (e.g., 'FAILED', 'PROCESSING', 'SUCCESS')
        error_message: Optional error message to store with failed status
        
    Returns:
        bool: True if status was updated, False if document not found
        
    Raises:
        psycopg2.Error: If database operation fails
        
    Requirements: 9.1, 9.2
    """
    logger.info(f"Updating document status: {object_key} -> {status}")
    
    # Note: This assumes ingestion_metadata has a status column
    # If the table structure is different, this query may need adjustment
    query = """
        UPDATE ingestion_metadata
        SET status = %s,
            updated_at = NOW()
        WHERE file_path = %s
        RETURNING id
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, object_key))
                result = cur.fetchone()
                
                if result:
                    conn.commit()
                    logger.info(
                        f"Updated document status to '{status}' for {object_key}",
                        extra={
                            "object_key": object_key,
                            "status": status,
                            "error_message": error_message
                        }
                    )
                    return True
                else:
                    logger.warning(
                        f"Document not found in ingestion_metadata: {object_key}",
                        extra={
                            "object_key": object_key,
                            "status": status
                        }
                    )
                    return False
                    
    except psycopg2.Error as e:
        logger.error(
            f"Failed to update document status for {object_key}: {e}",
            exc_info=True,
            extra={
                "object_key": object_key,
                "status": status,
                "error_type": "database_error",
                "error_message": str(e)
            }
        )
        raise


def get_scores_by_company_and_year(
    company_id: int,
    report_year: Optional[int] = None,
) -> List[Dict]:
    """
    Retrieve ESG scores for a company, optionally filtered by year.
    
    This function retrieves ESG scores for a specific company. If report_year is provided,
    it returns only the score for that year. If report_year is None, it returns all
    available scores for the company across all years, sorted by year descending.
    
    Args:
        company_id: Foreign key reference to company_catalog table
        report_year: Optional year filter (e.g., 2024). If None, returns all years.
    
    Returns:
        List[Dict]: List of score dictionaries, each containing:
            - id: Score record ID
            - company_id: Company ID
            - report_year: Report year
            - environmental_score: Environmental pillar score
            - social_score: Social pillar score
            - governance_score: Governance pillar score
            - overall_score: Overall ESG score
            - calculated_at: Timestamp of calculation
        Returns empty list if no scores found.
        
    Raises:
        psycopg2.Error: If database query fails
        ValueError: If company_id or report_year is invalid
        
    Requirements: 15.4, 15.5
    """
    if company_id <= 0:
        raise ValueError(f"company_id must be positive, got {company_id}")
    if report_year is not None and not 2000 <= report_year <= 2100:
        raise ValueError(f"report_year must be between 2000 and 2100, got {report_year}")
    
    logger.info(
        f"Retrieving scores for company_id={company_id}, year={report_year or 'all'}"
    )
    
    if report_year is not None:
        query = """
            SELECT 
                id,
                company_id,
                report_year,
                environmental_score,
                social_score,
                governance_score,
                overall_score,
                calculated_at
            FROM esg_scores
            WHERE company_id = %s AND report_year = %s
            ORDER BY report_year DESC
        """
        params = (company_id, report_year)
    else:
        query = """
            SELECT 
                id,
                company_id,
                report_year,
                environmental_score,
                social_score,
                governance_score,
                overall_score,
                calculated_at
            FROM esg_scores
            WHERE company_id = %s
            ORDER BY report_year DESC
        """
        params = (company_id,)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                
                scores = []
                for row in rows:
                    score = {
                        "id": row[0],
                        "company_id": row[1],
                        "report_year": row[2],
                        "environmental_score": float(row[3]) if row[3] is not None else None,
                        "social_score": float(row[4]) if row[4] is not None else None,
                        "governance_score": float(row[5]) if row[5] is not None else None,
                        "overall_score": float(row[6]) if row[6] is not None else None,
                        "calculated_at": row[7].isoformat() if row[7] else None,
                    }
                    scores.append(score)
                
                logger.info(
                    f"Retrieved {len(scores)} score(s) for company_id={company_id}"
                )
                return scores
                
    except psycopg2.Error as e:
        logger.error(f"Failed to retrieve scores: {e}")
        raise
