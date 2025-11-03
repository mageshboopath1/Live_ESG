"""
API utility functions for integration tests
"""
import requests
from typing import Dict, Any, Optional
import os


def get_api_base_url() -> str:
    """Get the API base URL from environment or default"""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


def api_get(endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> requests.Response:
    """
    Make a GET request to the API.
    
    Args:
        endpoint: API endpoint (e.g., "/api/companies")
        params: Optional query parameters
        headers: Optional headers
        
    Returns:
        Response object
    """
    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"
    
    default_headers = {"Accept": "application/json"}
    if headers:
        default_headers.update(headers)
    
    return requests.get(url, params=params, headers=default_headers, timeout=10)


def api_post(endpoint: str, data: Dict[str, Any], headers: Optional[Dict] = None, auth_token: Optional[str] = None) -> requests.Response:
    """
    Make a POST request to the API.
    
    Args:
        endpoint: API endpoint (e.g., "/api/companies")
        data: Request body data
        headers: Optional headers
        auth_token: Optional authentication token
        
    Returns:
        Response object
    """
    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"
    
    default_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    if auth_token:
        default_headers["Authorization"] = f"Bearer {auth_token}"
    
    if headers:
        default_headers.update(headers)
    
    return requests.post(url, json=data, headers=default_headers, timeout=10)


def api_put(endpoint: str, data: Dict[str, Any], headers: Optional[Dict] = None, auth_token: Optional[str] = None) -> requests.Response:
    """
    Make a PUT request to the API.
    
    Args:
        endpoint: API endpoint (e.g., "/api/companies/1")
        data: Request body data
        headers: Optional headers
        auth_token: Optional authentication token
        
    Returns:
        Response object
    """
    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"
    
    default_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    if auth_token:
        default_headers["Authorization"] = f"Bearer {auth_token}"
    
    if headers:
        default_headers.update(headers)
    
    return requests.put(url, json=data, headers=default_headers, timeout=10)


def api_delete(endpoint: str, headers: Optional[Dict] = None, auth_token: Optional[str] = None) -> requests.Response:
    """
    Make a DELETE request to the API.
    
    Args:
        endpoint: API endpoint (e.g., "/api/companies/1")
        headers: Optional headers
        auth_token: Optional authentication token
        
    Returns:
        Response object
    """
    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"
    
    default_headers = {"Accept": "application/json"}
    
    if auth_token:
        default_headers["Authorization"] = f"Bearer {auth_token}"
    
    if headers:
        default_headers.update(headers)
    
    return requests.delete(url, headers=default_headers, timeout=10)


def check_api_health() -> bool:
    """
    Check if the API is healthy and responding.
    
    Returns:
        True if API is healthy, False otherwise
    """
    try:
        response = api_get("/health")
        return response.status_code == 200
    except:
        return False


def get_companies() -> list:
    """
    Get all companies from the API.
    
    Returns:
        List of company dictionaries
    """
    response = api_get("/api/companies")
    if response.status_code == 200:
        return response.json()
    return []


def get_company_by_id(company_id: int) -> Optional[Dict]:
    """
    Get a specific company by ID.
    
    Args:
        company_id: ID of the company
        
    Returns:
        Company dictionary or None if not found
    """
    response = api_get(f"/api/companies/{company_id}")
    if response.status_code == 200:
        return response.json()
    return None


def get_indicators() -> list:
    """
    Get all BRSR indicator definitions from the API.
    
    Returns:
        List of indicator dictionaries
    """
    response = api_get("/api/indicators/definitions")
    if response.status_code == 200:
        return response.json()
    return []


def get_company_indicators(company_id: int) -> list:
    """
    Get indicators for a specific company.
    
    Args:
        company_id: ID of the company
        
    Returns:
        List of indicator dictionaries
    """
    response = api_get(f"/api/companies/{company_id}/indicators")
    if response.status_code == 200:
        return response.json()
    return []


def get_company_scores(company_id: int) -> list:
    """
    Get ESG scores for a specific company.
    
    Args:
        company_id: ID of the company
        
    Returns:
        List of score dictionaries
    """
    response = api_get(f"/api/companies/{company_id}/scores")
    if response.status_code == 200:
        return response.json()
    return []


def verify_api_returns_real_data(endpoint: str, expected_count: Optional[int] = None) -> bool:
    """
    Verify that an API endpoint returns real data, not mocks.
    
    Args:
        endpoint: API endpoint to check
        expected_count: Optional expected minimum count
        
    Returns:
        True if endpoint returns real data, False otherwise
    """
    try:
        response = api_get(endpoint)
        if response.status_code != 200:
            return False
        
        data = response.json()
        
        if not isinstance(data, list):
            return False
        
        if expected_count is not None and len(data) < expected_count:
            return False
        
        # Check for mock data indicators
        if len(data) > 0:
            first_item = data[0]
            # Check for common mock data patterns
            mock_indicators = ["MOCK", "TEST", "FAKE", "DUMMY"]
            for value in first_item.values():
                if isinstance(value, str):
                    for indicator in mock_indicators:
                        if indicator in value.upper():
                            return False
        
        return True
    except:
        return False


def create_auth_token(username: str, password: str) -> Optional[str]:
    """
    Create an authentication token by logging in.
    
    Args:
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        JWT token string or None if authentication failed
    """
    try:
        response = api_post("/api/auth/login", {
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    except:
        return None


def verify_auth_required(endpoint: str, method: str = "POST") -> bool:
    """
    Verify that an endpoint requires authentication.
    
    Args:
        endpoint: API endpoint to check
        method: HTTP method (POST, PUT, DELETE)
        
    Returns:
        True if endpoint requires auth (returns 401), False otherwise
    """
    try:
        if method == "POST":
            response = api_post(endpoint, {})
        elif method == "PUT":
            response = api_put(endpoint, {})
        elif method == "DELETE":
            response = api_delete(endpoint)
        else:
            return False
        
        return response.status_code == 401
    except:
        return False


def verify_response_structure(response: requests.Response, expected_fields: list) -> bool:
    """
    Verify that a response has the expected structure.
    
    Args:
        response: Response object to check
        expected_fields: List of expected field names
        
    Returns:
        True if response has all expected fields, False otherwise
    """
    try:
        if response.status_code != 200:
            return False
        
        data = response.json()
        
        # Handle list responses
        if isinstance(data, list):
            if len(data) == 0:
                return True  # Empty list is valid
            data = data[0]  # Check first item
        
        # Check if all expected fields are present
        return all(field in data for field in expected_fields)
    except:
        return False


def get_reports(company_id: Optional[int] = None) -> list:
    """
    Get reports from the API.
    
    Args:
        company_id: Optional company ID to filter by
        
    Returns:
        List of report dictionaries
    """
    if company_id:
        response = api_get(f"/api/companies/{company_id}/reports")
    else:
        response = api_get("/api/reports")
    
    if response.status_code == 200:
        return response.json()
    return []


def upload_document(company_id: int, file_path: str, auth_token: str) -> Optional[Dict]:
    """
    Upload a document for a company.
    
    Args:
        company_id: ID of the company
        file_path: Path to the file to upload
        auth_token: Authentication token
        
    Returns:
        Response data or None if upload failed
    """
    try:
        base_url = get_api_base_url()
        url = f"{base_url}/api/companies/{company_id}/documents"
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            return response.json()
        return None
    except:
        return None


def wait_for_processing(company_id: int, timeout: int = 60) -> bool:
    """
    Wait for document processing to complete.
    
    Args:
        company_id: ID of the company
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if processing completed, False if timeout
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check if indicators have been extracted
        indicators = get_company_indicators(company_id)
        if len(indicators) > 0:
            return True
        
        time.sleep(2)
    
    return False


def validate_indicator_response(indicator: Dict) -> bool:
    """
    Validate that an indicator response has the correct structure.
    
    Args:
        indicator: Indicator dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "indicator_code",
        "parameter_name",
        "measurement_unit",
        "pillar"
    ]
    
    return all(field in indicator for field in required_fields)


def validate_score_response(score: Dict) -> bool:
    """
    Validate that a score response has the correct structure.
    
    Args:
        score: Score dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "score_type",
        "score_value",
        "fiscal_year"
    ]
    
    return all(field in score for field in required_fields)


def validate_company_response(company: Dict) -> bool:
    """
    Validate that a company response has the correct structure.
    
    Args:
        company: Company dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "id",
        "name"
    ]
    
    return all(field in company for field in required_fields)


def check_endpoint_accessibility(endpoint: str, expected_status: int = 200) -> bool:
    """
    Check if an endpoint is accessible and returns expected status.
    
    Args:
        endpoint: API endpoint to check
        expected_status: Expected HTTP status code
        
    Returns:
        True if endpoint returns expected status, False otherwise
    """
    try:
        response = api_get(endpoint)
        return response.status_code == expected_status
    except:
        return False


def get_error_message(response: requests.Response) -> Optional[str]:
    """
    Extract error message from a response.
    
    Args:
        response: Response object
        
    Returns:
        Error message string or None
    """
    try:
        if response.status_code >= 400:
            data = response.json()
            return data.get("detail") or data.get("message") or data.get("error")
        return None
    except:
        return None
