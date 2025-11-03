"""Test script to verify public endpoints work without authentication."""

import sys
from fastapi.testclient import TestClient

# Import the app
from src.main import app

client = TestClient(app)

def test_public_get_endpoints():
    """Test that GET endpoints work without authentication."""
    
    print("Testing public GET endpoints...")
    
    # Test root endpoint
    response = client.get("/")
    print(f"GET / - Status: {response.status_code}")
    assert response.status_code == 200, "Root endpoint should be accessible"
    
    # Test health endpoint
    response = client.get("/health")
    print(f"GET /health - Status: {response.status_code}")
    # Health might fail if DB not connected, but should not be 401
    assert response.status_code != 401, "Health endpoint should not require auth"
    
    # Test companies endpoint (should work without auth)
    response = client.get("/api/companies")
    print(f"GET /api/companies - Status: {response.status_code}")
    assert response.status_code != 401, "Companies GET should not require auth"
    
    # Test indicators definitions endpoint (should work without auth)
    response = client.get("/api/indicators/definitions")
    print(f"GET /api/indicators/definitions - Status: {response.status_code}")
    assert response.status_code != 401, "Indicators definitions GET should not require auth"
    
    print("\n✓ All public GET endpoints are accessible without authentication")


def test_protected_post_endpoints():
    """Test that POST endpoints require authentication."""
    
    print("\nTesting protected POST endpoints...")
    
    # Test cache invalidation (should require auth)
    response = client.post("/api/cache/invalidate/indicators")
    print(f"POST /api/cache/invalidate/indicators - Status: {response.status_code}")
    assert response.status_code in [401, 403], f"Cache POST should require auth (got {response.status_code})"
    
    # Test trigger processing (should require auth)
    response = client.post(
        "/api/reports/trigger-processing",
        json={"object_key": "test.pdf", "force_reprocess": False}
    )
    print(f"POST /api/reports/trigger-processing - Status: {response.status_code}")
    assert response.status_code in [401, 403], f"Reports POST should require auth (got {response.status_code})"
    
    print("\n✓ All POST endpoints correctly require authentication")


if __name__ == "__main__":
    try:
        test_public_get_endpoints()
        test_protected_post_endpoints()
        print("\n" + "="*60)
        print("SUCCESS: All authentication tests passed!")
        print("="*60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
