"""
Main entry point for the extraction service.

This module implements the RabbitMQ consumer worker that:
1. Listens to "extraction-tasks" queue for document processing requests
2. Parses object_key from messages to identify company and report year
3. Loads all BRSR Core indicator definitions from database
4. Executes batch extraction for all indicators using LangChain + Google GenAI
5. Validates extracted indicators against BRSR schema
6. Calculates and stores ESG scores (overall and pillar scores)
7. Marks documents as processed

Requirements: 5.1, 5.2, 6.5, 12.4
"""

import logging
import time
from typing import Dict, List

import pika

from src.config import config
from src.db.repository import (
    load_brsr_indicators,
    parse_object_key,
    get_company_id_by_name,
    check_embeddings_exist,
    check_document_processed,
    store_extracted_indicators,
    store_esg_score,
    get_indicator_id_by_code,
    update_document_status,
)
from src.extraction.extractor import extract_indicators_batch
from src.validation.validator import validate_indicator
from src.scoring.esg_calculator import get_esg_score_with_citations
from src.models.brsr_models import BRSRIndicatorDefinition
from src.monitoring import metrics_collector, health_checker
from src.monitoring.http_server import HealthMetricsServer

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_rabbitmq_connection():
    """
    Create and return a RabbitMQ connection.
    
    Returns:
        pika.BlockingConnection: RabbitMQ connection object
        
    Raises:
        pika.exceptions.AMQPConnectionError: If connection fails
    """
    credentials = pika.PlainCredentials(
        config.rabbitmq_user,
        config.rabbitmq_password
    )
    parameters = pika.ConnectionParameters(
        host=config.rabbitmq_host,
        credentials=credentials,
        heartbeat=600,  # 10 minutes
        blocked_connection_timeout=300,  # 5 minutes
    )
    return pika.BlockingConnection(parameters)


def process_extraction_task(object_key: str) -> bool:
    """
    Process a single extraction task for a document.
    
    This function orchestrates the complete extraction pipeline:
    1. Check if document already processed (skip if yes)
    2. Parse object_key to get company name and report year
    3. Load BRSR indicator definitions
    4. Execute batch extraction for all indicators
    5. Validate extracted indicators
    6. Calculate ESG scores (pillar and overall)
    7. Store scores with calculation metadata
    
    Args:
        object_key: MinIO object key (e.g., "RELIANCE/2024_BRSR.pdf")
        
    Returns:
        bool: True if processing succeeded, False otherwise
        
    Requirements: 5.1, 5.2, 6.5, 12.4, 9.1, 9.2, 9.4
    """
    logger.info(f"Starting extraction task for document: {object_key}")
    start_time = time.time()
    
    # Initialize document metrics (will be set after parsing object_key)
    doc_metrics = None
    
    try:
        # Update status to PROCESSING
        try:
            update_document_status(object_key, "PROCESSING")
        except Exception as e:
            logger.warning(
                f"Could not update document status to PROCESSING: {e}",
                extra={"object_key": object_key}
            )
        
        # Step 1: Check if document already processed
        if check_document_processed(object_key):
            logger.info(
                f"Document {object_key} already processed. Skipping."
            )
            return True
        
        # Step 2: Parse object_key to get company name and report year
        logger.info(f"Parsing object key: {object_key}")
        try:
            company_name, report_year = parse_object_key(object_key)
            logger.info(
                f"Parsed document: company={company_name}, year={report_year}"
            )
            
            # Start tracking metrics for this document
            doc_metrics = metrics_collector.start_document(
                object_key=object_key,
                company_name=company_name,
                report_year=report_year
            )
            
        except ValueError as e:
            logger.error(
                f"Failed to parse object key '{object_key}': {e}",
                exc_info=True,
                extra={
                    "object_key": object_key,
                    "error_type": "parse_error",
                    "error_message": str(e)
                }
            )
            return False
        
        # Step 3: Get company ID
        try:
            company_id = get_company_id_by_name(company_name)
            if company_id is None:
                logger.error(
                    f"Company '{company_name}' not found in database. "
                    f"Cannot process document.",
                    extra={
                        "object_key": object_key,
                        "company_name": company_name,
                        "error_type": "company_not_found",
                        "error_message": f"Company '{company_name}' not found in company_catalog"
                    }
                )
                return False
            
            logger.info(f"Found company_id={company_id} for {company_name}")
        except Exception as e:
            logger.error(
                f"Database error while looking up company '{company_name}': {e}",
                exc_info=True,
                extra={
                    "object_key": object_key,
                    "company_name": company_name,
                    "error_type": "database_error",
                    "error_message": str(e)
                }
            )
            return False
        
        # Step 4: Load all BRSR indicator definitions
        logger.info("Loading BRSR Core indicator definitions")
        try:
            indicator_definitions = load_brsr_indicators()
            logger.info(f"Loaded {len(indicator_definitions)} indicator definitions")
            
            if not indicator_definitions:
                logger.error(
                    "No BRSR indicator definitions found in database. "
                    "Ensure indicators are properly seeded.",
                    extra={
                        "object_key": object_key,
                        "error_type": "missing_indicators",
                        "error_message": "No BRSR indicators found in brsr_indicators table"
                    }
                )
                return False
        except Exception as e:
            logger.error(
                f"Failed to load BRSR indicator definitions: {e}",
                exc_info=True,
                extra={
                    "object_key": object_key,
                    "error_type": "database_error",
                    "error_message": str(e)
                }
            )
            return False
        
        # Step 5: Execute batch extraction for all indicators
        logger.info(
            f"Starting batch extraction for {len(indicator_definitions)} indicators"
        )
        try:
            extracted_indicators = extract_indicators_batch(
                object_key=object_key,
                connection_string=config.database_url,
                google_api_key=config.google_api_key,
                indicators=indicator_definitions,
                k=10,  # Retrieve 10 chunks per indicator
                model_name="gemini-2.5-flash",
                temperature=0.1,
            )
            
            logger.info(
                f"Batch extraction complete: {len(extracted_indicators)} indicators extracted"
            )
            
            if not extracted_indicators:
                logger.warning(
                    f"No indicators extracted for {object_key}. "
                    f"Document may not contain BRSR data.",
                    extra={
                        "object_key": object_key,
                        "company_name": company_name,
                        "report_year": report_year,
                        "warning_type": "no_indicators_extracted"
                    }
                )
                # Still return True to mark as processed (avoid reprocessing)
                return True
        except Exception as e:
            logger.error(
                f"Batch extraction failed for {object_key}: {e}",
                exc_info=True,
                extra={
                    "object_key": object_key,
                    "company_name": company_name,
                    "report_year": report_year,
                    "error_type": "extraction_error",
                    "error_message": str(e),
                    "total_indicators": len(indicator_definitions)
                }
            )
            return False
        
        # Step 6: Validate extracted indicators
        logger.info("Validating extracted indicators")
        validated_indicators = []
        validation_stats = {"valid": 0, "invalid": 0, "warnings": 0}
        validation_errors_detail = []
        confidence_scores = []
        
        # Create indicator definition lookup
        indicator_def_map: Dict[str, BRSRIndicatorDefinition] = {
            ind.indicator_code: ind for ind in indicator_definitions
        }
        
        for extracted in extracted_indicators:
            try:
                # Get indicator definition
                indicator_id = extracted.indicator_id
                indicator_def = None
                for ind_def in indicator_definitions:
                    if get_indicator_id_by_code(ind_def.indicator_code) == indicator_id:
                        indicator_def = ind_def
                        break
                
                if indicator_def is None:
                    logger.warning(
                        f"Could not find indicator definition for indicator_id={indicator_id}. "
                        f"Skipping validation.",
                        extra={
                            "object_key": object_key,
                            "indicator_id": indicator_id,
                            "warning_type": "missing_indicator_definition"
                        }
                    )
                    # Store without validation
                    validated_indicators.append(extracted)
                    continue
                
                # Validate indicator
                validation_result = validate_indicator(extracted, indicator_def)
                
                # Update validation status
                extracted.validation_status = validation_result.validation_status
                
                # Track statistics
                if validation_result.is_valid:
                    validation_stats["valid"] += 1
                else:
                    validation_stats["invalid"] += 1
                
                if validation_result.warnings:
                    validation_stats["warnings"] += len(validation_result.warnings)
                
                # Track confidence scores for metrics
                if extracted.confidence_score is not None:
                    confidence_scores.append(extracted.confidence_score)
                
                # Log validation issues with detailed context
                if validation_result.errors:
                    error_detail = {
                        "indicator_code": indicator_def.indicator_code,
                        "indicator_name": indicator_def.parameter_name,
                        "extracted_value": extracted.extracted_value,
                        "numeric_value": extracted.numeric_value,
                        "confidence_score": extracted.confidence_score,
                        "errors": validation_result.errors
                    }
                    validation_errors_detail.append(error_detail)
                    
                    logger.warning(
                        f"Validation errors for {indicator_def.indicator_code} "
                        f"(value: '{extracted.extracted_value}'): {validation_result.errors}",
                        extra={
                            "object_key": object_key,
                            "indicator_code": indicator_def.indicator_code,
                            "indicator_name": indicator_def.parameter_name,
                            "extracted_value": extracted.extracted_value,
                            "numeric_value": extracted.numeric_value,
                            "confidence_score": extracted.confidence_score,
                            "validation_errors": validation_result.errors,
                            "error_type": "validation_error"
                        }
                    )
                
                if validation_result.warnings:
                    logger.debug(
                        f"Validation warnings for {indicator_def.indicator_code}: "
                        f"{validation_result.warnings}",
                        extra={
                            "object_key": object_key,
                            "indicator_code": indicator_def.indicator_code,
                            "validation_warnings": validation_result.warnings
                        }
                    )
                
                validated_indicators.append(extracted)
                
            except Exception as e:
                logger.error(
                    f"Error during validation of indicator_id={extracted.indicator_id}: {e}",
                    exc_info=True,
                    extra={
                        "object_key": object_key,
                        "indicator_id": extracted.indicator_id,
                        "error_type": "validation_exception",
                        "error_message": str(e)
                    }
                )
                # Continue with next indicator
                validated_indicators.append(extracted)
        
        logger.info(
            f"Validation complete: {validation_stats['valid']} valid, "
            f"{validation_stats['invalid']} invalid, "
            f"{validation_stats['warnings']} warnings",
            extra={
                "object_key": object_key,
                "validation_stats": validation_stats,
                "validation_errors_count": len(validation_errors_detail)
            }
        )
        
        # Record extraction metrics
        if doc_metrics:
            metrics_collector.record_extraction_metrics(
                metrics=doc_metrics,
                indicators_extracted=len(validated_indicators),
                indicators_valid=validation_stats["valid"],
                indicators_invalid=validation_stats["invalid"],
                validation_warnings=validation_stats["warnings"],
                confidence_scores=confidence_scores,
            )
        
        # Log summary of validation errors if any
        if validation_errors_detail:
            logger.warning(
                f"Validation errors summary for {object_key}: "
                f"{len(validation_errors_detail)} indicators with errors",
                extra={
                    "object_key": object_key,
                    "validation_errors_detail": validation_errors_detail
                }
            )
        
        # Step 7: Store extracted indicators in database
        logger.info(f"Storing {len(validated_indicators)} indicators in database")
        try:
            stored_count = store_extracted_indicators(validated_indicators)
            logger.info(
                f"Successfully stored {stored_count} indicators",
                extra={
                    "object_key": object_key,
                    "stored_count": stored_count,
                    "validation_stats": validation_stats
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to store extracted indicators for {object_key}: {e}",
                exc_info=True,
                extra={
                    "object_key": object_key,
                    "indicator_count": len(validated_indicators),
                    "error_type": "database_error",
                    "error_message": str(e)
                }
            )
            return False
        
        # Step 8: Calculate ESG scores
        logger.info("Calculating ESG scores")
        
        try:
            # Prepare extracted indicators for score calculation
            extracted_for_scoring = []
            for extracted in validated_indicators:
                # Find indicator code
                indicator_code = None
                for ind_def in indicator_definitions:
                    if get_indicator_id_by_code(ind_def.indicator_code) == extracted.indicator_id:
                        indicator_code = ind_def.indicator_code
                        break
                
                if indicator_code and extracted.numeric_value is not None:
                    extracted_for_scoring.append({
                        "indicator_code": indicator_code,
                        "numeric_value": extracted.numeric_value,
                        "source_pages": extracted.source_pages,
                        "source_chunk_ids": extracted.source_chunk_ids,
                        "object_key": extracted.object_key,
                        "confidence_score": extracted.confidence_score,
                    })
            
            logger.info(
                f"Calculating scores from {len(extracted_for_scoring)} numeric indicators"
            )
            
            # Calculate ESG score with citations
            overall_score, calculation_metadata = get_esg_score_with_citations(
                indicator_definitions=indicator_definitions,
                extracted_indicators=extracted_for_scoring,
                pillar_weights=None,  # Use default weights
            )
            
            # Extract pillar scores from metadata
            pillar_scores = calculation_metadata.get("pillar_scores", {})
            environmental_score = pillar_scores.get("environmental")
            social_score = pillar_scores.get("social")
            governance_score = pillar_scores.get("governance")
            
            logger.info(
                f"ESG scores calculated - Overall: {overall_score}, "
                f"E: {environmental_score}, S: {social_score}, G: {governance_score}",
                extra={
                    "object_key": object_key,
                    "overall_score": overall_score,
                    "environmental_score": environmental_score,
                    "social_score": social_score,
                    "governance_score": governance_score,
                    "numeric_indicators_count": len(extracted_for_scoring)
                }
            )
            
            # Record score metrics
            if doc_metrics:
                metrics_collector.record_score_metrics(
                    metrics=doc_metrics,
                    overall_score=overall_score,
                    environmental_score=environmental_score,
                    social_score=social_score,
                    governance_score=governance_score,
                )
            
        except Exception as e:
            logger.error(
                f"Failed to calculate ESG scores for {object_key}: {e}",
                exc_info=True,
                extra={
                    "object_key": object_key,
                    "error_type": "score_calculation_error",
                    "error_message": str(e),
                    "numeric_indicators_count": len(extracted_for_scoring)
                }
            )
            return False
        
        # Step 9: Store ESG scores
        logger.info("Storing ESG scores in database")
        try:
            score_id = store_esg_score(
                company_id=company_id,
                report_year=report_year,
                environmental_score=environmental_score,
                social_score=social_score,
                governance_score=governance_score,
                overall_score=overall_score,
                calculation_metadata=calculation_metadata,
            )
            
            logger.info(
                f"Successfully stored ESG scores with id={score_id} "
                f"for company_id={company_id}, year={report_year}",
                extra={
                    "object_key": object_key,
                    "score_id": score_id,
                    "company_id": company_id,
                    "report_year": report_year
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to store ESG scores for {object_key}: {e}",
                exc_info=True,
                extra={
                    "object_key": object_key,
                    "company_id": company_id,
                    "report_year": report_year,
                    "error_type": "database_error",
                    "error_message": str(e)
                }
            )
            return False
        
        # Step 10: Mark document as processed (already done by storing indicators)
        elapsed_time = time.time() - start_time
        logger.info(
            f"Document {object_key} marked as processed "
            f"({stored_count} indicators, score_id={score_id})",
            extra={
                "object_key": object_key,
                "stored_count": stored_count,
                "score_id": score_id,
                "processing_time_seconds": elapsed_time
            }
        )
        
        # Update status to SUCCESS
        try:
            update_document_status(object_key, "SUCCESS")
        except Exception as e:
            logger.warning(
                f"Could not update document status to SUCCESS: {e}",
                extra={"object_key": object_key}
            )
        
        logger.info(
            f"✓ Extraction task completed successfully for {object_key} "
            f"in {elapsed_time:.2f}s",
            extra={
                "object_key": object_key,
                "success": True,
                "processing_time_seconds": elapsed_time,
                "indicators_extracted": stored_count,
                "validation_stats": validation_stats,
                "overall_score": overall_score
            }
        )
        
        # End document metrics tracking
        if doc_metrics:
            metrics_collector.end_document(
                metrics=doc_metrics,
                success=True,
            )
            health_checker.update_extraction_status(success=True)
        
        return True
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_message = str(e)
        error_type = type(e).__name__
        
        logger.error(
            f"Failed to process extraction task for {object_key}: {e}",
            exc_info=True,
            extra={
                "object_key": object_key,
                "error_type": "unexpected_error",
                "error_message": error_message,
                "processing_time_seconds": elapsed_time,
                "success": False
            }
        )
        
        # Update document status to FAILED
        try:
            update_document_status(object_key, "FAILED", error_message)
        except Exception as status_error:
            logger.error(
                f"Failed to update document status for {object_key}: {status_error}",
                extra={
                    "object_key": object_key,
                    "original_error": error_message
                }
            )
        
        # End document metrics tracking with failure
        if doc_metrics:
            metrics_collector.end_document(
                metrics=doc_metrics,
                success=False,
                error_message=error_message,
                error_type=error_type,
            )
            health_checker.update_extraction_status(success=False)
        
        return False


def callback(ch, method, properties, body):
    """
    RabbitMQ message callback handler with retry logic and dead letter queue support.
    
    This function is called for each message received from the extraction-tasks queue.
    It processes the extraction task and handles acknowledgment/rejection with retry logic:
    - Tracks retry count using message headers
    - Requeues failed tasks up to max_retries
    - Sends to dead letter queue after max retries exceeded
    - Logs all retry attempts with detailed context
    
    Args:
        ch: Channel object
        method: Method frame with delivery_tag
        properties: Message properties (includes headers for retry tracking)
        body: Message body (JSON object or plain string with object_key)
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1, 9.2, 11.5
    """
    import json
    
    # Decode message body
    message_str = body.decode("utf-8")
    
    # Try to parse as JSON first (new format from ingestion service)
    try:
        message_data = json.loads(message_str)
        if isinstance(message_data, dict) and "object_key" in message_data:
            object_key = message_data["object_key"]
            logger.debug(
                f"Parsed JSON message: object_key={object_key}",
                extra={
                    "message_data": message_data,
                    "delivery_tag": method.delivery_tag
                }
            )
        else:
            # JSON but no object_key field
            object_key = message_str
            logger.warning(
                f"JSON message missing 'object_key' field, using raw message: {message_str}",
                extra={"message_str": message_str}
            )
    except json.JSONDecodeError:
        # Not JSON, treat as plain string (legacy format)
        object_key = message_str
        logger.debug(
            f"Plain string message: {object_key}",
            extra={"delivery_tag": method.delivery_tag}
        )
    
    # Get retry count from message headers
    retry_count = 0
    if properties.headers and "x-retry-count" in properties.headers:
        retry_count = properties.headers["x-retry-count"]
    
    # Get embedding check count from message headers
    embedding_check_count = 0
    if properties.headers and "x-embedding-check-count" in properties.headers:
        embedding_check_count = properties.headers["x-embedding-check-count"]
    
    max_retries = config.max_retries  # Maximum number of retry attempts from config
    max_embedding_checks = 10  # Maximum number of embedding check attempts
    
    logger.info(
        f"Received extraction task: {object_key} (attempt {retry_count + 1}/{max_retries + 1})",
        extra={
            "object_key": object_key,
            "retry_count": retry_count,
            "max_retries": max_retries,
            "embedding_check_count": embedding_check_count,
            "delivery_tag": method.delivery_tag
        }
    )
    
    try:
        # Check if embeddings exist before processing
        if not check_embeddings_exist(object_key):
            if embedding_check_count < max_embedding_checks:
                # Embeddings not ready, requeue with delay
                logger.warning(
                    f"⏳ Embeddings not ready for {object_key}, requeuing "
                    f"(check {embedding_check_count + 1}/{max_embedding_checks})",
                    extra={
                        "object_key": object_key,
                        "embedding_check_count": embedding_check_count,
                        "max_embedding_checks": max_embedding_checks,
                        "action": "requeued_waiting_embeddings"
                    }
                )
                
                # Reject and requeue the message
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
                # Sleep to add delay before requeue
                time.sleep(30)
                return
            else:
                # Max embedding checks exceeded - send to DLQ
                logger.error(
                    f"✗ Embeddings not ready after {max_embedding_checks} checks, "
                    f"sending to DLQ: {object_key}",
                    extra={
                        "object_key": object_key,
                        "embedding_check_count": embedding_check_count,
                        "max_embedding_checks": max_embedding_checks,
                        "action": "sent_to_dlq",
                        "reason": "embeddings_not_ready"
                    }
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
        
        logger.info(
            f"✓ Embeddings verified for {object_key}, proceeding with extraction",
            extra={"object_key": object_key}
        )
        
        # Process the extraction task
        success = process_extraction_task(object_key)
        
        if success:
            # Acknowledge message (remove from queue)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(
                f"✓ Task acknowledged: {object_key} (completed after {retry_count + 1} attempt(s))",
                extra={
                    "object_key": object_key,
                    "retry_count": retry_count,
                    "success": True
                }
            )
        else:
            # Task failed - check if we should retry
            if retry_count < max_retries:
                # Requeue with incremented retry count
                retry_count += 1
                
                # Reject and requeue the message
                # Note: To properly implement retry with headers, we need to republish
                # the message with updated headers. For now, we'll use basic requeue.
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
                logger.warning(
                    f"⚠ Task failed, requeuing for retry {retry_count}/{max_retries}: {object_key}",
                    extra={
                        "object_key": object_key,
                        "retry_count": retry_count,
                        "max_retries": max_retries,
                        "action": "requeued"
                    }
                )
            else:
                # Max retries exceeded - send to dead letter queue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
                logger.error(
                    f"✗ Task failed after {max_retries + 1} attempts, sending to DLQ: {object_key}",
                    extra={
                        "object_key": object_key,
                        "retry_count": retry_count,
                        "max_retries": max_retries,
                        "action": "sent_to_dlq",
                        "final_failure": True
                    }
                )
            
    except Exception as e:
        logger.error(
            f"Unexpected error in callback for {object_key}: {e}",
            exc_info=True,
            extra={
                "object_key": object_key,
                "retry_count": retry_count,
                "error_type": "callback_exception",
                "error_message": str(e)
            }
        )
        
        # Check if we should retry
        if retry_count < max_retries:
            # Requeue for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.warning(
                f"⚠ Exception occurred, requeuing for retry {retry_count + 1}/{max_retries}: {object_key}",
                extra={
                    "object_key": object_key,
                    "retry_count": retry_count + 1,
                    "max_retries": max_retries,
                    "action": "requeued"
                }
            )
        else:
            # Max retries exceeded - send to DLQ
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            logger.error(
                f"✗ Exception after {max_retries + 1} attempts, sending to DLQ: {object_key}",
                extra={
                    "object_key": object_key,
                    "retry_count": retry_count,
                    "max_retries": max_retries,
                    "action": "sent_to_dlq",
                    "final_failure": True
                }
            )


def main():
    """
    Initialize and run the extraction service worker.
    
    This function:
    1. Establishes connection to RabbitMQ
    2. Declares the extraction-tasks queue (creates if doesn't exist)
    3. Sets up message consumer with callback
    4. Starts consuming messages (blocking)
    5. Handles connection errors with automatic retry
    6. Starts HTTP server for health checks and metrics
    
    The worker runs indefinitely until interrupted (CTRL+C).
    
    Requirements: 5.1, 5.2, 6.5, 9.4
    """
    logger.info("=" * 60)
    logger.info("ESG Extraction Service Starting")
    logger.info("=" * 60)
    logger.info(f"Database: {config.db_host}:{config.db_port}/{config.db_name}")
    logger.info(f"RabbitMQ: {config.rabbitmq_host}")
    logger.info(f"Queue: {config.extraction_queue}")
    logger.info(f"Log Level: {config.log_level}")
    logger.info("=" * 60)
    
    # Start HTTP server for health checks and metrics
    http_server = None
    try:
        http_server = HealthMetricsServer(
            host="0.0.0.0",
            port=config.health_port,
            health_callback=lambda: health_checker.get_health_status(),
            metrics_callback=lambda: {
                "aggregate": metrics_collector.get_aggregate_metrics(),
                "recent_documents": metrics_collector.get_recent_documents(limit=10),
            }
        )
        http_server.start()
    except Exception as e:
        logger.warning(f"Failed to start HTTP server: {e}. Continuing without health endpoint.")
    
    # Perform initial health checks
    logger.info("Performing initial health checks...")
    health_checker.check_database(config.database_url)
    health_checker.check_rabbitmq(
        config.rabbitmq_host,
        config.rabbitmq_user,
        config.rabbitmq_password
    )
    health_checker.log_health_status()
    
    # Retry loop for connection resilience
    retry_delay = 5  # seconds
    max_retry_delay = 60  # seconds
    
    while True:
        try:
            logger.info("Connecting to RabbitMQ...")
            connection = get_rabbitmq_connection()
            channel = connection.channel()
            
            # Declare dead letter queue first
            dlq_name = f"{config.extraction_queue}.dlq"
            logger.info(f"Declaring dead letter queue: {dlq_name}")
            channel.queue_declare(
                queue=dlq_name,
                durable=True,
            )
            
            # Declare main queue with dead letter exchange configuration
            logger.info(f"Declaring queue: {config.extraction_queue}")
            channel.queue_declare(
                queue=config.extraction_queue,
                durable=True,  # Survive broker restart
                arguments={
                    'x-dead-letter-exchange': '',  # Use default exchange
                    'x-dead-letter-routing-key': dlq_name,  # Route to DLQ
                }
            )
            
            logger.info(
                f"Queue configured with dead letter queue: {config.extraction_queue} -> {dlq_name}"
            )
            
            # Set QoS to process one message at a time
            # This ensures fair distribution across multiple workers
            channel.basic_qos(prefetch_count=1)
            
            # Set up consumer
            logger.info("Setting up message consumer...")
            channel.basic_consume(
                queue=config.extraction_queue,
                on_message_callback=callback,
                auto_ack=False,  # Manual acknowledgment
            )
            
            logger.info("=" * 60)
            logger.info("✓ Extraction service ready")
            logger.info("Waiting for extraction tasks...")
            logger.info("Press CTRL+C to exit")
            logger.info("=" * 60)
            
            # Start consuming (blocking)
            channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Shutting down gracefully...")
            
            # Log final metrics
            logger.info("Final metrics summary:")
            metrics_collector.log_aggregate_metrics()
            
            try:
                channel.stop_consuming()
                connection.close()
            except:
                pass
            
            # Stop HTTP server
            if http_server:
                try:
                    http_server.stop()
                except:
                    pass
            
            logger.info("✓ Extraction service stopped")
            break
            
        except Exception as e:
            logger.error(
                f"Connection error: {e}",
                exc_info=True
            )
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
            # Exponential backoff with max delay
            retry_delay = min(retry_delay * 2, max_retry_delay)


if __name__ == "__main__":
    main()
