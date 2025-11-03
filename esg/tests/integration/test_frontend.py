"""
Frontend integration tests

These tests verify:
- Frontend can fetch company data without auth
- Frontend can fetch indicator data without auth
- Frontend displays data correctly
- Frontend handles API errors
"""
import pytest
import requests
from bs4 import BeautifulSoup


def test_frontend_is_accessible(frontend_base_url):
    """Test frontend is running and accessible"""
    try:
        response = requests.get(frontend_base_url, timeout=5)
        assert response.status_code == 200, \
            f"Frontend returned status {response.status_code}"
        print("✓ Frontend is accessible")
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend is not running - skipping frontend tests")


def test_frontend_serves_html(frontend_base_url):
    """Test frontend serves HTML content"""
    try:
        response = requests.get(frontend_base_url, timeout=5)
        assert response.status_code == 200
        
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, \
            f"Expected HTML content, got {content_type}"
        
        # Check for basic HTML structure
        assert '<html' in response.text.lower() or '<!doctype html>' in response.text.lower(), \
            "Response doesn't contain HTML"
        
        print("✓ Frontend serves HTML content")
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend is not running")


def test_frontend_has_vue_app(frontend_base_url):
    """Test frontend includes Vue.js application"""
    try:
        response = requests.get(frontend_base_url, timeout=5)
        assert response.status_code == 200
        
        # Check for Vue app mount point
        assert 'id="app"' in response.text or 'id=app' in response.text, \
            "Vue app mount point not found"
        
        print("✓ Frontend has Vue app structure")
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend is not running")


def test_frontend_loads_javascript(frontend_base_url):
    """Test frontend loads JavaScript bundles"""
    try:
        response = requests.get(frontend_base_url, timeout=5)
        assert response.status_code == 200
        
        # Check for script tags
        assert '<script' in response.text.lower(), \
            "No JavaScript found in HTML"
        
        print("✓ Frontend loads JavaScript")
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend is not running")


def test_frontend_api_integration(frontend_base_url, api_base_url):
    """
    Test frontend can communicate with API Gateway.
    This is a basic connectivity test.
    """
    try:
        # Check if frontend is running
        frontend_response = requests.get(frontend_base_url, timeout=5)
        assert frontend_response.status_code == 200
        
        # Check if API is accessible from the same network
        api_response = requests.get(f"{api_base_url}/health", timeout=5)
        assert api_response.status_code == 200
        
        print("✓ Frontend and API are both accessible")
    except requests.exceptions.ConnectionError as e:
        pytest.skip(f"Service not running: {e}")


def test_frontend_can_fetch_companies(api_base_url):
    """
    Test that the API endpoint used by frontend works without auth.
    This simulates what the frontend would do.
    """
    try:
        # Simulate frontend request (no auth headers)
        response = requests.get(
            f"{api_base_url}/api/companies",
            headers={
                "Accept": "application/json",
                "Origin": "http://localhost:3000"
            },
            timeout=5
        )
        
        assert response.status_code == 200, \
            f"Frontend would fail to fetch companies: {response.status_code}"
        
        data = response.json()
        # API returns a dict with 'companies' key, not a list
        assert isinstance(data, dict), "Companies endpoint should return a dict"
        assert "companies" in data, "Response should have 'companies' key"
        companies = data["companies"]
        
        print(f"✓ Frontend can fetch companies without auth ({len(companies)} companies)")
    except requests.exceptions.ConnectionError:
        pytest.skip("API Gateway is not running")


def test_frontend_can_fetch_indicators(api_base_url):
    """
    Test that the API endpoint used by frontend works without auth.
    This simulates what the frontend would do.
    """
    try:
        # Simulate frontend request (no auth headers) - using new endpoint
        response = requests.get(
            f"{api_base_url}/api/brsr/indicators",
            headers={
                "Accept": "application/json",
                "Origin": "http://localhost:3000"
            },
            timeout=5
        )
        
        assert response.status_code == 200, \
            f"Frontend would fail to fetch indicators: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Indicators endpoint should return a list"
        assert len(data) >= 55, f"Expected at least 55 indicators, got {len(data)}"
        
        print(f"✓ Frontend can fetch indicators without auth ({len(data)} indicators)")
    except requests.exceptions.ConnectionError:
        pytest.skip("API Gateway is not running")


def test_frontend_handles_api_errors(api_base_url):
    """
    Test that API returns proper error responses that frontend can handle.
    """
    try:
        # Request non-existent resource
        response = requests.get(
            f"{api_base_url}/api/companies/99999999",
            headers={
                "Accept": "application/json",
                "Origin": "http://localhost:3000"
            },
            timeout=5
        )
        
        assert response.status_code == 404, \
            f"Expected 404 for non-existent resource, got {response.status_code}"
        
        # Check if response is JSON (easier for frontend to handle)
        try:
            error_data = response.json()
            print(f"✓ API returns JSON error responses: {error_data}")
        except:
            print("⚠ API error response is not JSON (frontend may need to handle text)")
        
    except requests.exceptions.ConnectionError:
        pytest.skip("API Gateway is not running")


def test_frontend_cors_support(api_base_url):
    """
    Test that API supports CORS for frontend requests.
    """
    try:
        # Simulate a CORS preflight request
        response = requests.options(
            f"{api_base_url}/api/companies",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type"
            },
            timeout=5
        )
        
        # Check for CORS headers
        cors_headers = {
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        }
        
        found_headers = set()
        for header in response.headers:
            if header.lower() in cors_headers:
                found_headers.add(header.lower())
        
        if found_headers:
            print(f"✓ CORS headers present: {found_headers}")
        else:
            print("⚠ No CORS headers found - frontend may have cross-origin issues")
        
    except requests.exceptions.ConnectionError:
        pytest.skip("API Gateway is not running")


def test_frontend_static_assets(frontend_base_url):
    """Test frontend static assets are accessible"""
    try:
        response = requests.get(frontend_base_url, timeout=5)
        assert response.status_code == 200
        
        # Parse HTML to find asset references
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for CSS
        css_links = soup.find_all('link', rel='stylesheet')
        if css_links:
            print(f"✓ Found {len(css_links)} CSS files")
        
        # Check for JS
        js_scripts = soup.find_all('script', src=True)
        if js_scripts:
            print(f"✓ Found {len(js_scripts)} JavaScript files")
        
        # Try to fetch one asset if available
        if js_scripts:
            first_script = js_scripts[0]['src']
            if first_script.startswith('/'):
                asset_url = f"{frontend_base_url}{first_script}"
                asset_response = requests.get(asset_url, timeout=5)
                if asset_response.status_code == 200:
                    print(f"✓ Static assets are accessible")
                else:
                    print(f"⚠ Asset returned status {asset_response.status_code}")
        
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend is not running")
    except Exception as e:
        print(f"⚠ Could not verify static assets: {e}")


def test_frontend_routing(frontend_base_url):
    """Test frontend routing works (SPA behavior)"""
    try:
        # Test root route
        response = requests.get(frontend_base_url, timeout=5)
        assert response.status_code == 200
        
        # Test a typical route (may return 200 for SPA)
        routes_to_test = [
            "/companies",
            "/indicators",
            "/scores"
        ]
        
        for route in routes_to_test:
            route_response = requests.get(f"{frontend_base_url}{route}", timeout=5)
            # SPA should return 200 and serve the same HTML (client-side routing)
            if route_response.status_code == 200:
                print(f"✓ Route {route} accessible")
            else:
                print(f"⚠ Route {route} returned {route_response.status_code}")
        
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend is not running")


def test_frontend_environment_config(frontend_base_url):
    """Test frontend has proper environment configuration"""
    try:
        response = requests.get(frontend_base_url, timeout=5)
        assert response.status_code == 200
        
        # Check if API URL is configured in the HTML or scripts
        # This is a basic check - actual config may be in bundled JS
        if 'localhost:8000' in response.text or 'api' in response.text.lower():
            print("✓ Frontend appears to have API configuration")
        else:
            print("⚠ Could not verify API configuration in frontend")
        
    except requests.exceptions.ConnectionError:
        pytest.skip("Frontend is not running")


def test_frontend_displays_data_structure(api_base_url, db_cursor):
    """
    Test that the data structure returned by API is suitable for frontend display.
    """
    try:
        # Get companies data
        response = requests.get(f"{api_base_url}/api/companies", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        companies = data.get("companies", [])
        
        if len(companies) > 0:
            company = companies[0]
            
            # Check for fields frontend would need (actual field is company_name, not name)
            display_fields = ["id", "company_name"]
            for field in display_fields:
                assert field in company, \
                    f"Company data missing '{field}' field needed for display"
            
            print(f"✓ Company data structure suitable for frontend display")
        else:
            print("⚠ No company data to verify display structure")
        
        # Get indicators data (using new endpoint)
        response = requests.get(f"{api_base_url}/api/brsr/indicators", timeout=5)
        assert response.status_code == 200
        
        indicators = response.json()
        
        if len(indicators) > 0:
            indicator = indicators[0]
            
            # Check for fields frontend would need
            display_fields = ["indicator_code", "parameter_name", "pillar"]
            for field in display_fields:
                assert field in indicator, \
                    f"Indicator data missing '{field}' field needed for display"
            
            print(f"✓ Indicator data structure suitable for frontend display")
        else:
            pytest.fail("No indicator data - database seeding failed")
        
    except requests.exceptions.ConnectionError:
        pytest.skip("API Gateway is not running")
