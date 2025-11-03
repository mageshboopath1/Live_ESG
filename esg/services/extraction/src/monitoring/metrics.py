"""
Metrics collection for extraction service.

This module tracks:
- Extraction metrics (indicators extracted, confidence scores, processing time)
- API usage and costs
- Processing statistics per document

Requirements: 9.4
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetrics:
    """Metrics for a single document extraction."""
    
    object_key: str
    company_name: str
    report_year: int
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    
    # Extraction metrics
    indicators_extracted: int = 0
    indicators_valid: int = 0
    indicators_invalid: int = 0
    validation_warnings: int = 0
    
    # Confidence score statistics
    avg_confidence_score: Optional[float] = None
    min_confidence_score: Optional[float] = None
    max_confidence_score: Optional[float] = None
    
    # Score metrics
    overall_esg_score: Optional[float] = None
    environmental_score: Optional[float] = None
    social_score: Optional[float] = None
    governance_score: Optional[float] = None
    
    # API usage
    api_calls: int = 0
    api_errors: int = 0
    
    # Error tracking
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Calculate processing time in seconds."""
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for logging."""
        return {
            "object_key": self.object_key,
            "company_name": self.company_name,
            "report_year": self.report_year,
            "success": self.success,
            "processing_time_seconds": self.processing_time_seconds,
            "indicators_extracted": self.indicators_extracted,
            "indicators_valid": self.indicators_valid,
            "indicators_invalid": self.indicators_invalid,
            "validation_warnings": self.validation_warnings,
            "avg_confidence_score": self.avg_confidence_score,
            "min_confidence_score": self.min_confidence_score,
            "max_confidence_score": self.max_confidence_score,
            "overall_esg_score": self.overall_esg_score,
            "environmental_score": self.environmental_score,
            "social_score": self.social_score,
            "governance_score": self.governance_score,
            "api_calls": self.api_calls,
            "api_errors": self.api_errors,
            "error_message": self.error_message,
            "error_type": self.error_type,
        }


@dataclass
class AggregateMetrics:
    """Aggregate metrics across all documents."""
    
    # Document counts
    total_documents_processed: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    
    # Extraction metrics
    total_indicators_extracted: int = 0
    total_indicators_valid: int = 0
    total_indicators_invalid: int = 0
    total_validation_warnings: int = 0
    
    # Processing time statistics
    total_processing_time_seconds: float = 0.0
    avg_processing_time_seconds: Optional[float] = None
    min_processing_time_seconds: Optional[float] = None
    max_processing_time_seconds: Optional[float] = None
    
    # Confidence score statistics
    avg_confidence_score: Optional[float] = None
    
    # API usage
    total_api_calls: int = 0
    total_api_errors: int = 0
    
    # Timestamps
    first_document_time: Optional[datetime] = None
    last_document_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert aggregate metrics to dictionary."""
        return {
            "total_documents_processed": self.total_documents_processed,
            "successful_documents": self.successful_documents,
            "failed_documents": self.failed_documents,
            "success_rate": (
                self.successful_documents / self.total_documents_processed
                if self.total_documents_processed > 0
                else 0.0
            ),
            "total_indicators_extracted": self.total_indicators_extracted,
            "total_indicators_valid": self.total_indicators_valid,
            "total_indicators_invalid": self.total_indicators_invalid,
            "total_validation_warnings": self.total_validation_warnings,
            "validation_success_rate": (
                self.total_indicators_valid / self.total_indicators_extracted
                if self.total_indicators_extracted > 0
                else 0.0
            ),
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "avg_processing_time_seconds": self.avg_processing_time_seconds,
            "min_processing_time_seconds": self.min_processing_time_seconds,
            "max_processing_time_seconds": self.max_processing_time_seconds,
            "avg_confidence_score": self.avg_confidence_score,
            "total_api_calls": self.total_api_calls,
            "total_api_errors": self.total_api_errors,
            "api_error_rate": (
                self.total_api_errors / self.total_api_calls
                if self.total_api_calls > 0
                else 0.0
            ),
            "first_document_time": (
                self.first_document_time.isoformat()
                if self.first_document_time
                else None
            ),
            "last_document_time": (
                self.last_document_time.isoformat()
                if self.last_document_time
                else None
            ),
        }


class MetricsCollector:
    """
    Collects and tracks metrics for the extraction service.
    
    This class is thread-safe and maintains both per-document metrics
    and aggregate metrics across all processed documents.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._lock = threading.Lock()
        self._document_metrics: List[DocumentMetrics] = []
        self._aggregate_metrics = AggregateMetrics()
        self._current_document: Optional[DocumentMetrics] = None
    
    def start_document(
        self,
        object_key: str,
        company_name: str,
        report_year: int
    ) -> DocumentMetrics:
        """
        Start tracking metrics for a new document.
        
        Args:
            object_key: Document object key
            company_name: Company name
            report_year: Report year
            
        Returns:
            DocumentMetrics: Metrics object for this document
        """
        with self._lock:
            metrics = DocumentMetrics(
                object_key=object_key,
                company_name=company_name,
                report_year=report_year,
                start_time=time.time(),
            )
            self._current_document = metrics
            return metrics
    
    def end_document(
        self,
        metrics: DocumentMetrics,
        success: bool,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """
        Finish tracking metrics for a document.
        
        Args:
            metrics: Document metrics object
            success: Whether processing succeeded
            error_message: Error message if failed
            error_type: Error type if failed
        """
        with self._lock:
            metrics.end_time = time.time()
            metrics.success = success
            metrics.error_message = error_message
            metrics.error_type = error_type
            
            # Add to document metrics list
            self._document_metrics.append(metrics)
            
            # Update aggregate metrics
            self._update_aggregate_metrics(metrics)
            
            # Log document metrics
            logger.info(
                f"Document metrics for {metrics.object_key}",
                extra={"document_metrics": metrics.to_dict()}
            )
            
            # Clear current document
            if self._current_document == metrics:
                self._current_document = None
    
    def record_extraction_metrics(
        self,
        metrics: DocumentMetrics,
        indicators_extracted: int,
        indicators_valid: int,
        indicators_invalid: int,
        validation_warnings: int,
        confidence_scores: List[float],
    ):
        """
        Record extraction metrics for a document.
        
        Args:
            metrics: Document metrics object
            indicators_extracted: Number of indicators extracted
            indicators_valid: Number of valid indicators
            indicators_invalid: Number of invalid indicators
            validation_warnings: Number of validation warnings
            confidence_scores: List of confidence scores
        """
        with self._lock:
            metrics.indicators_extracted = indicators_extracted
            metrics.indicators_valid = indicators_valid
            metrics.indicators_invalid = indicators_invalid
            metrics.validation_warnings = validation_warnings
            
            if confidence_scores:
                metrics.avg_confidence_score = sum(confidence_scores) / len(confidence_scores)
                metrics.min_confidence_score = min(confidence_scores)
                metrics.max_confidence_score = max(confidence_scores)
    
    def record_score_metrics(
        self,
        metrics: DocumentMetrics,
        overall_score: Optional[float],
        environmental_score: Optional[float],
        social_score: Optional[float],
        governance_score: Optional[float],
    ):
        """
        Record ESG score metrics for a document.
        
        Args:
            metrics: Document metrics object
            overall_score: Overall ESG score
            environmental_score: Environmental pillar score
            social_score: Social pillar score
            governance_score: Governance pillar score
        """
        with self._lock:
            metrics.overall_esg_score = overall_score
            metrics.environmental_score = environmental_score
            metrics.social_score = social_score
            metrics.governance_score = governance_score
    
    def record_api_call(self, metrics: DocumentMetrics, success: bool = True):
        """
        Record an API call.
        
        Args:
            metrics: Document metrics object
            success: Whether the API call succeeded
        """
        with self._lock:
            metrics.api_calls += 1
            if not success:
                metrics.api_errors += 1
    
    def _update_aggregate_metrics(self, doc_metrics: DocumentMetrics):
        """Update aggregate metrics with document metrics."""
        agg = self._aggregate_metrics
        
        # Update document counts
        agg.total_documents_processed += 1
        if doc_metrics.success:
            agg.successful_documents += 1
        else:
            agg.failed_documents += 1
        
        # Update extraction metrics
        agg.total_indicators_extracted += doc_metrics.indicators_extracted
        agg.total_indicators_valid += doc_metrics.indicators_valid
        agg.total_indicators_invalid += doc_metrics.indicators_invalid
        agg.total_validation_warnings += doc_metrics.validation_warnings
        
        # Update processing time statistics
        if doc_metrics.processing_time_seconds is not None:
            agg.total_processing_time_seconds += doc_metrics.processing_time_seconds
            
            if agg.min_processing_time_seconds is None:
                agg.min_processing_time_seconds = doc_metrics.processing_time_seconds
            else:
                agg.min_processing_time_seconds = min(
                    agg.min_processing_time_seconds,
                    doc_metrics.processing_time_seconds
                )
            
            if agg.max_processing_time_seconds is None:
                agg.max_processing_time_seconds = doc_metrics.processing_time_seconds
            else:
                agg.max_processing_time_seconds = max(
                    agg.max_processing_time_seconds,
                    doc_metrics.processing_time_seconds
                )
            
            agg.avg_processing_time_seconds = (
                agg.total_processing_time_seconds / agg.total_documents_processed
            )
        
        # Update confidence score statistics
        if doc_metrics.avg_confidence_score is not None:
            if agg.avg_confidence_score is None:
                agg.avg_confidence_score = doc_metrics.avg_confidence_score
            else:
                # Running average
                total_docs = agg.total_documents_processed
                agg.avg_confidence_score = (
                    (agg.avg_confidence_score * (total_docs - 1) + doc_metrics.avg_confidence_score)
                    / total_docs
                )
        
        # Update API usage
        agg.total_api_calls += doc_metrics.api_calls
        agg.total_api_errors += doc_metrics.api_errors
        
        # Update timestamps
        now = datetime.now()
        if agg.first_document_time is None:
            agg.first_document_time = now
        agg.last_document_time = now
    
    def get_aggregate_metrics(self) -> Dict:
        """
        Get aggregate metrics across all documents.
        
        Returns:
            Dict: Aggregate metrics dictionary
        """
        with self._lock:
            return self._aggregate_metrics.to_dict()
    
    def get_recent_documents(self, limit: int = 10) -> List[Dict]:
        """
        Get metrics for recent documents.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List[Dict]: List of document metrics dictionaries
        """
        with self._lock:
            recent = self._document_metrics[-limit:]
            return [doc.to_dict() for doc in recent]
    
    def get_document_metrics(self, object_key: str) -> Optional[Dict]:
        """
        Get metrics for a specific document.
        
        Args:
            object_key: Document object key
            
        Returns:
            Optional[Dict]: Document metrics dictionary or None if not found
        """
        with self._lock:
            for doc in reversed(self._document_metrics):
                if doc.object_key == object_key:
                    return doc.to_dict()
            return None
    
    def log_aggregate_metrics(self):
        """Log aggregate metrics at INFO level."""
        metrics = self.get_aggregate_metrics()
        logger.info(
            "Aggregate extraction metrics",
            extra={"aggregate_metrics": metrics}
        )


# Global metrics collector instance
metrics_collector = MetricsCollector()
