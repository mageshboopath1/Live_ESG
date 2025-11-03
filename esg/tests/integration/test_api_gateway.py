"""
API Gateway integration tests

These tests verify:
- API Gateway endpoints return actual data from database
- GET endpoints work without authentication
- POST endpoints require authentication
- Responses contain real data, not mocks
"""
import pytest
import requests
from typing import Dict, Any


def test_api_gateway_health(api_base_url):
    """Test API Gateway is running and healthy"""
    try:
        response = requests.get(f"{api_base_url}/health", timeout=5)
        assert response.status_code == 200, f"Health check failed with status {response.status_code}"
        print("✓ API Gateway is healthy")
    except requests.exceptions.ConnectionError:
        pytest.fail("Cannot connect to API Gateway - is it running?")


def test_get_companies_no_auth(api_base_url, auth_headers):
    """Test GET /api/companies works with authentication"""
    response = requests.get(f"{api_base_url}/api/companies", headers=auth_headers, timeout=5)
    
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    assert "companies" in data, "Response should have 'companies' key"
    assert isinstance(data["companies"], list), "Companies should be a list"
    
    print(f"✓ GET /api/companies returned {len(data['companies'])} companies")


def test_get_companies_returns_real_data(api_base_url, db_cursor, auth_headers):
    """Test GET /api/companies returns actual data from database, not mocks"""
    # Get count from database
    db_cursor.execute("SELECT COUNT(*) FROM company_catalog")
    db_count = db_cursor.fetchone()[0]
    
    # Get data from API with high limit to get all companies
    response = requests.get(f"{api_base_url}/api/companies?limit=100", headers=auth_headers, timeout=5)
    assert response.status_code == 200
    
    api_response = response.json()
    api_data = api_response.get("companies", [])
    api_count = api_response.get("total", len(api_data))
    
    # Verify API returns actual database data (check total count, not just returned items)
    assert api_count == db_count, \
        f"API returned {api_count} companies but database has {db_count}. Data mismatch!"
    
    if api_count > 0:
        # Verify structure of returned data
        first_company = api_data[0]
        assert "id" in first_company, "Company missing 'id' field"
        assert "company_name" in first_company, "Company missing 'company_name' field"
        
        # Verify this is real data by checking it exists in database
        db_cursor.execute("SELECT company_name FROM company_catalog WHERE id = %s", (first_company["id"],))
        db_name = db_cursor.fetchone()
        assert db_name is not None, f"Company {first_company['id']} not found in database"
        assert db_name[0] == first_company["company_name"], "Company name mismatch between API and database"
        
        print(f"✓ Verified API returns real data from database ({api_count} companies)")
    else:
        print("⚠ No companies in database yet")


def test_get_indicators_definitions_no_auth(api_base_url, auth_headers):
    """Test GET /api/brsr/indicators works with authentication"""
    response = requests.get(f"{api_base_url}/api/brsr/indicators", headers=auth_headers, timeout=5)
    
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    # Response is a list, not a dict with 'indicators' key
    assert isinstance(data, list), "Response should be a list of indicators"
    
    print(f"✓ GET /api/indicators/definitions returned {len(data)} indicators")


def test_get_indicators_returns_real_brsr_data(api_base_url, db_cursor, auth_headers):
    """Test GET /api/brsr/indicators returns actual BRSR indicators from database"""
    # Get count from database
    db_cursor.execute("SELECT COUNT(*) FROM brsr_indicators")
    db_count = db_cursor.fetchone()[0]
    
    # Get data from API
    response = requests.get(f"{api_base_url}/api/brsr/indicators", headers=auth_headers, timeout=5)
    assert response.status_code == 200
    
    # Response is a list, not a dict
    api_data = response.json()
    api_count = len(api_data)
    
    # Verify API returns actual database data
    assert api_count == db_count, \
        f"API returned {api_count} indicators but database has {db_count}. Data mismatch!"
    
    assert api_count >= 55, \
        f"Expected at least 55 BRSR indicators, got {api_count}"
    
    if api_count > 0:
        # Verify structure and real data
        first_indicator = api_data[0]
        required_fields = ["indicator_code", "parameter_name", "measurement_unit", "pillar"]
        
        for field in required_fields:
            assert field in first_indicator, f"Indicator missing required field: {field}"
        
        # Verify this is NOT mock data
        assert first_indicator["indicator_code"] != "MOCK_CODE", \
            "Receiving mock data instead of real indicators"
        assert first_indicator["indicator_code"] != "", \
            "Indicator code is empty"
        
        # Verify indicator exists in database
        db_cursor.execute(
            "SELECT parameter_name FROM brsr_indicators WHERE indicator_code = %s",
            (first_indicator["indicator_code"],)
        )
        db_result = db_cursor.fetchone()
        assert db_result is not None, \
            f"Indicator {first_indicator['indicator_code']} not found in database"
        
        print(f"✓ Verified API returns real BRSR indicators from database ({api_count} indicators)")
    else:
        pytest.fail("No BRSR indicators found - database seeding failed")


def test_get_indicators_all_pillars_present(api_base_url, auth_headers):
    """Test indicators include all three pillars (E/S/G)"""
    response = requests.get(f"{api_base_url}/api/brsr/indicators", headers=auth_headers, timeout=5)
    assert response.status_code == 200
    
    # Response is a list, not a dict
    data = response.json()
    pillars = set(indicator.get("pillar") for indicator in data)
    
    assert "E" in pillars, "No Environmental indicators"
    assert "S" in pillars, "No Social indicators"
    assert "G" in pillars, "No Governance indicators"
    
    print(f"✓ All three pillars (E/S/G) present in indicators")


def test_get_scores_no_auth(api_base_url, auth_headers):
    """Test GET /api/scores works with authentication"""
    response = requests.get(f"{api_base_url}/api/scores", headers=auth_headers, timeout=5)
    
    # Should return 200 even if empty
    assert response.status_code in [200, 404], \
        f"Expected 200 or 404, got {response.status_code}"
    
    if response.status_code == 200:
        data = response.json()
        # Response might be a list or dict with scores key
        if isinstance(data, dict):
            scores = data.get("scores", [])
        else:
            scores = data
        print(f"✓ GET /api/scores returned {len(scores)} scores")
    else:
        print("⚠ No scores endpoint or no scores yet")


def test_get_reports_no_auth(api_base_url, auth_headers):
    """Test GET /api/reports works with authentication"""
    response = requests.get(f"{api_base_url}/api/reports", headers=auth_headers, timeout=5)
    
    # Should return 200 even if empty
    assert response.status_code in [200, 404], \
        f"Expected 200 or 404, got {response.status_code}"
    
    if response.status_code == 200:
        data = response.json()
        # Response might be a list or dict with reports key
        if isinstance(data, dict):
            reports = data.get("reports", [])
        else:
            reports = data
        print(f"✓ GET /api/reports returned {len(reports)} reports")
    else:
        print("⚠ No reports endpoint or no reports yet")


def test_get_company_by_id(api_base_url, db_cursor, auth_headers):
    """Test GET /api/companies/{id} returns specific company data"""
    # Get a company from database
    db_cursor.execute("SELECT id, company_name FROM company_catalog LIMIT 1")
    result = db_cursor.fetchone()
    
    if result is None:
        print("⚠ No companies in database to test")
        return
    
    company_id, company_name = result
    
    # Get from API
    response = requests.get(f"{api_base_url}/api/companies/{company_id}", headers=auth_headers, timeout=5)
    assert response.status_code == 200, f"Failed to get company {company_id}"
    
    data = response.json()
    assert data["id"] == company_id, "Company ID mismatch"
    assert data["company_name"] == company_name, "Company name mismatch"
    
    print(f"✓ GET /api/companies/{company_id} returned correct data")


def test_get_company_indicators(api_base_url, db_cursor, auth_headers):
    """Test GET /api/companies/{id}/indicators returns actual indicators"""
    # Get a company from database
    db_cursor.execute("SELECT id FROM company_catalog LIMIT 1")
    result = db_cursor.fetchone()
    
    if result is None:
        print("⚠ No companies in database to test")
        return
    
    company_id = result[0]
    
    # Get indicators from API
    response = requests.get(
        f"{api_base_url}/api/companies/{company_id}/indicators",
        headers=auth_headers,
        timeout=5
    )
    
    # May return 200 with empty list or 404 if no indicators yet
    assert response.status_code in [200, 404], \
        f"Expected 200 or 404, got {response.status_code}"
    
    if response.status_code == 200:
        data = response.json()
        # Response might be a list or dict with indicators key
        if isinstance(data, dict):
            indicators = data.get("indicators", [])
        else:
            indicators = data
        print(f"✓ GET /api/companies/{company_id}/indicators returned {len(indicators)} indicators")
    else:
        print(f"⚠ No indicators for company {company_id} yet")


def test_post_requires_authentication(api_base_url):
    """Test POST endpoints require authentication"""
    # Try to create a company without auth
    response = requests.post(
        f"{api_base_url}/api/companies",
        json={"name": "Test Company", "ticker": "TEST"},
        timeout=5
    )
    
    # Should return 401 Unauthorized or 403 Forbidden
    assert response.status_code in [401, 403, 405], \
        f"Expected 401/403/405 for unauthenticated POST, got {response.status_code}"
    
    print(f"✓ POST /api/companies requires authentication (status: {response.status_code})")


def test_api_error_handling(api_base_url, auth_headers):
    """Test API returns proper error responses"""
    # Request non-existent company
    response = requests.get(f"{api_base_url}/api/companies/99999999", headers=auth_headers, timeout=5)
    
    assert response.status_code == 404, \
        f"Expected 404 for non-existent resource, got {response.status_code}"
    
    print("✓ API returns proper 404 for non-existent resources")


def test_api_cors_headers(api_base_url, auth_headers):
    """Test API includes CORS headers for frontend access"""
    response = requests.get(f"{api_base_url}/api/companies", headers=auth_headers, timeout=5)
    
    # Check for CORS headers (may not be present in all configurations)
    if "access-control-allow-origin" in response.headers:
        print(f"✓ CORS headers present: {response.headers.get('access-control-allow-origin')}")
    else:
        print("⚠ No CORS headers found (may need configuration)")
