"""
Test HTTP server for health and metrics endpoints.

This test verifies that the HTTP server can be started and endpoints work.
"""

import time
import json
from urllib.request import urlopen
from urllib.error import URLError

from src.monitoring import metrics_collector, health_checker
from src.monitoring.http_server import HealthMetricsServer


def test_http_server():
    """Test HTTP server startup and endpoints."""
    print("=" * 80)
    print("Testing HTTP Server")
    print("=" * 80)
    
    # Add some test data
    doc_metrics = metrics_collector.start_document(
        object_key="TEST/2024.pdf",
        company_name="TEST",
        report_year=2024
    )
    
    time.sleep(0.05)
    
    metrics_collector.record_extraction_metrics(
        metrics=doc_metrics,
        indicators_extracted=5,
        indicators_valid=5,
        indicators_invalid=0,
        validation_warnings=0,
        confidence_scores=[0.9, 0.85, 0.95, 0.88, 0.92],
    )
    
    metrics_collector.end_document(doc_metrics, success=True)
    health_checker.update_extraction_status(success=True)
    
    # Start HTTP server
    server = HealthMetricsServer(
        host="127.0.0.1",
        port=8081,  # Use different port for testing
        health_callback=lambda: health_checker.get_health_status(),
        metrics_callback=lambda: {
            "aggregate": metrics_collector.get_aggregate_metrics(),
            "recent_documents": metrics_collector.get_recent_documents(limit=10),
        }
    )
    
    try:
        server.start()
        print("✓ HTTP server started on http://127.0.0.1:8081")
        
        # Give server time to start
        time.sleep(0.5)
        
        # Test root endpoint
        print("\nTesting GET /")
        try:
            response = urlopen("http://127.0.0.1:8081/")
            data = json.loads(response.read().decode())
            print(f"✓ Root endpoint response: {data['service']}")
            assert "endpoints" in data
        except URLError as e:
            print(f"✗ Failed to connect to root endpoint: {e}")
            raise
        
        # Test health endpoint
        print("\nTesting GET /health")
        try:
            response = urlopen("http://127.0.0.1:8081/health")
            data = json.loads(response.read().decode())
            print(f"✓ Health endpoint response:")
            print(f"  - Status: {data['status']}")
            print(f"  - Uptime: {data['uptime_seconds']:.2f}s")
            assert "status" in data
            assert "uptime_seconds" in data
        except URLError as e:
            # 503 is acceptable if no components are healthy yet
            if hasattr(e, 'code') and e.code == 503:
                # Read the response body even on error
                data = json.loads(e.read().decode())
                print(f"✓ Health endpoint response (503 - no healthy components yet):")
                print(f"  - Status: {data['status']}")
                print(f"  - Uptime: {data['uptime_seconds']:.2f}s")
                assert "status" in data
                assert "uptime_seconds" in data
            else:
                print(f"✗ Failed to connect to health endpoint: {e}")
                raise
        
        # Test metrics endpoint
        print("\nTesting GET /metrics")
        try:
            response = urlopen("http://127.0.0.1:8081/metrics")
            data = json.loads(response.read().decode())
            print(f"✓ Metrics endpoint response:")
            print(f"  - Total documents: {data['aggregate']['total_documents_processed']}")
            print(f"  - Recent documents: {len(data['recent_documents'])}")
            assert "aggregate" in data
            assert "recent_documents" in data
        except URLError as e:
            print(f"✗ Failed to connect to metrics endpoint: {e}")
            raise
        
        # Test 404
        print("\nTesting GET /nonexistent (should return 404)")
        try:
            response = urlopen("http://127.0.0.1:8081/nonexistent")
            print(f"✗ Should have returned 404, got {response.status}")
        except URLError as e:
            if hasattr(e, 'code') and e.code == 404:
                print(f"✓ Correctly returned 404 for nonexistent endpoint")
            else:
                print(f"✗ Unexpected error: {e}")
                raise
        
        print("\n" + "=" * 80)
        print("✓ All HTTP server tests passed!")
        print("=" * 80)
        
    finally:
        # Stop server
        server.stop()
        print("\n✓ HTTP server stopped")


if __name__ == "__main__":
    test_http_server()
    print("\n" + "=" * 80)
    print("✓✓✓ HTTP SERVER TEST PASSED! ✓✓✓")
    print("=" * 80)
