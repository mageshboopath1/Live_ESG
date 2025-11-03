"""
Tests for monitoring and metrics functionality.

This test verifies that the monitoring module works correctly.
"""

import time
from src.monitoring import metrics_collector, health_checker


def test_metrics_collector():
    """Test metrics collection functionality."""
    print("=" * 80)
    print("Testing MetricsCollector")
    print("=" * 80)
    
    # Start tracking a document
    doc_metrics = metrics_collector.start_document(
        object_key="TEST_COMPANY/2024_BRSR.pdf",
        company_name="TEST_COMPANY",
        report_year=2024
    )
    
    print(f"✓ Started tracking document: {doc_metrics.object_key}")
    
    # Simulate some processing
    time.sleep(0.1)
    
    # Record extraction metrics
    confidence_scores = [0.85, 0.90, 0.88, 0.92, 0.87]
    metrics_collector.record_extraction_metrics(
        metrics=doc_metrics,
        indicators_extracted=5,
        indicators_valid=4,
        indicators_invalid=1,
        validation_warnings=2,
        confidence_scores=confidence_scores,
    )
    
    print(f"✓ Recorded extraction metrics: {doc_metrics.indicators_extracted} indicators")
    print(f"  - Valid: {doc_metrics.indicators_valid}")
    print(f"  - Invalid: {doc_metrics.indicators_invalid}")
    print(f"  - Avg confidence: {doc_metrics.avg_confidence_score:.2f}")
    
    # Record score metrics
    metrics_collector.record_score_metrics(
        metrics=doc_metrics,
        overall_score=75.5,
        environmental_score=72.0,
        social_score=78.0,
        governance_score=76.5,
    )
    
    print(f"✓ Recorded score metrics: Overall ESG = {doc_metrics.overall_esg_score}")
    
    # Record API calls
    for _ in range(10):
        metrics_collector.record_api_call(doc_metrics, success=True)
    metrics_collector.record_api_call(doc_metrics, success=False)
    
    print(f"✓ Recorded API calls: {doc_metrics.api_calls} total, {doc_metrics.api_errors} errors")
    
    # End tracking
    metrics_collector.end_document(
        metrics=doc_metrics,
        success=True,
    )
    
    print(f"✓ Ended tracking: Processing time = {doc_metrics.processing_time_seconds:.2f}s")
    
    # Get aggregate metrics
    aggregate = metrics_collector.get_aggregate_metrics()
    print(f"\n✓ Aggregate metrics:")
    print(f"  - Total documents: {aggregate['total_documents_processed']}")
    print(f"  - Success rate: {aggregate['success_rate']:.2%}")
    print(f"  - Total indicators: {aggregate['total_indicators_extracted']}")
    print(f"  - Avg processing time: {aggregate['avg_processing_time_seconds']:.2f}s")
    
    # Get recent documents
    recent = metrics_collector.get_recent_documents(limit=5)
    print(f"\n✓ Recent documents: {len(recent)}")
    
    # Get specific document metrics
    doc_data = metrics_collector.get_document_metrics("TEST_COMPANY/2024_BRSR.pdf")
    assert doc_data is not None
    print(f"\n✓ Retrieved document metrics: {doc_data['object_key']}")
    
    print("\n" + "=" * 80)
    print("✓ All metrics collector tests passed!")
    print("=" * 80)


def test_health_checker():
    """Test health checker functionality."""
    print("\n" + "=" * 80)
    print("Testing HealthChecker")
    print("=" * 80)
    
    # Update extraction status
    health_checker.update_extraction_status(success=True)
    print("✓ Updated extraction status: success")
    
    # Get health status
    status = health_checker.get_health_status()
    print(f"\n✓ Health status:")
    print(f"  - Overall status: {status['status']}")
    print(f"  - Uptime: {status['uptime_seconds']:.2f}s")
    print(f"  - Components: {len(status['components'])}")
    print(f"  - Last successful extraction: {status['last_successful_extraction']}")
    
    # Check if healthy
    is_healthy = health_checker.is_healthy()
    print(f"\n✓ Is healthy: {is_healthy}")
    
    print("\n" + "=" * 80)
    print("✓ All health checker tests passed!")
    print("=" * 80)


def test_document_metrics_to_dict():
    """Test DocumentMetrics to_dict conversion."""
    print("\n" + "=" * 80)
    print("Testing DocumentMetrics.to_dict()")
    print("=" * 80)
    
    doc_metrics = metrics_collector.start_document(
        object_key="TEST/2024.pdf",
        company_name="TEST",
        report_year=2024
    )
    
    time.sleep(0.05)
    
    metrics_collector.record_extraction_metrics(
        metrics=doc_metrics,
        indicators_extracted=3,
        indicators_valid=3,
        indicators_invalid=0,
        validation_warnings=0,
        confidence_scores=[0.9, 0.85, 0.95],
    )
    
    metrics_collector.end_document(doc_metrics, success=True)
    
    data = doc_metrics.to_dict()
    
    print("✓ Converted to dict:")
    print(f"  - Keys: {list(data.keys())}")
    print(f"  - Object key: {data['object_key']}")
    print(f"  - Success: {data['success']}")
    print(f"  - Processing time: {data['processing_time_seconds']:.3f}s")
    
    assert data['object_key'] == "TEST/2024.pdf"
    assert data['success'] is True
    assert data['indicators_extracted'] == 3
    assert data['processing_time_seconds'] is not None
    
    print("\n" + "=" * 80)
    print("✓ DocumentMetrics.to_dict() test passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_metrics_collector()
    test_health_checker()
    test_document_metrics_to_dict()
    print("\n" + "=" * 80)
    print("✓✓✓ ALL MONITORING TESTS PASSED! ✓✓✓")
    print("=" * 80)
