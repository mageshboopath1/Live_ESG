# Test Utilities

This directory contains utility functions for integration tests.

## Files

### db_utils.py
Database utility functions for testing:

**Connection Management:**
- `get_db_connection()`: Create a database connection
- `execute_query()`: Execute a query and return results as tuples
- `execute_query_dict()`: Execute a query and return results as dictionaries

**Schema Verification:**
- `table_exists()`: Check if a table exists
- `get_table_columns()`: Get column names for a table
- `verify_foreign_key()`: Verify a foreign key constraint exists
- `verify_index_exists()`: Verify an index exists
- `verify_extension_installed()`: Verify a PostgreSQL extension is installed

**Data Verification:**
- `get_table_count()`: Get row count for a table
- `verify_data_exists()`: Check if data exists matching a condition
- `get_record_by_id()`: Get a record by ID
- `verify_pipeline_data()`: Verify pipeline data exists for a company

**BRSR Specific:**
- `get_brsr_indicator_count()`: Get count of BRSR indicators
- `get_brsr_indicators_by_pillar()`: Get indicator counts by pillar (E/S/G)
- `get_brsr_attributes()`: Get list of attribute numbers
- `verify_brsr_completeness()`: Comprehensive BRSR verification

**Company Data:**
- `get_company_count()`: Get count of companies
- `get_company_by_ticker()`: Get company by ticker symbol
- `get_indicators_for_company()`: Get extracted indicators for a company
- `get_scores_for_company()`: Get ESG scores for a company

**Test Data Management:**
- `insert_test_data()`: Insert test data and return ID
- `update_test_data()`: Update test data
- `cleanup_test_data()`: Clean up test data

### api_utils.py
API client utility functions for testing:

**HTTP Methods:**
- `api_get()`: Make a GET request
- `api_post()`: Make a POST request
- `api_put()`: Make a PUT request
- `api_delete()`: Make a DELETE request

**Health Checks:**
- `check_api_health()`: Check if API is healthy
- `check_endpoint_accessibility()`: Check if endpoint is accessible

**Data Retrieval:**
- `get_companies()`: Get all companies
- `get_company_by_id()`: Get specific company
- `get_indicators()`: Get BRSR indicator definitions
- `get_company_indicators()`: Get indicators for a company
- `get_company_scores()`: Get scores for a company
- `get_reports()`: Get reports

**Authentication:**
- `create_auth_token()`: Create authentication token
- `verify_auth_required()`: Verify endpoint requires authentication

**Validation:**
- `verify_api_returns_real_data()`: Verify endpoint returns real data, not mocks
- `verify_response_structure()`: Verify response has expected fields
- `validate_indicator_response()`: Validate indicator response structure
- `validate_score_response()`: Validate score response structure
- `validate_company_response()`: Validate company response structure

**Document Processing:**
- `upload_document()`: Upload a document
- `wait_for_processing()`: Wait for document processing to complete

**Error Handling:**
- `get_error_message()`: Extract error message from response

## Usage Examples

### Database Utilities

```python
from tests.utils.db_utils import (
    get_brsr_indicator_count,
    verify_brsr_completeness,
    get_company_by_ticker,
    verify_pipeline_data
)

# Check BRSR indicators
count = get_brsr_indicator_count()
assert count >= 60, f"Expected at least 60 indicators, found {count}"

# Verify BRSR completeness
verification = verify_brsr_completeness()
assert verification["has_all_attributes"], "Missing BRSR attributes"
assert verification["has_all_pillars"], "Missing E/S/G pillars"

# Get company by ticker
company = get_company_by_ticker("RELIANCE")
if company:
    # Verify pipeline data
    pipeline_status = verify_pipeline_data(company["id"])
    assert pipeline_status["has_company"], "Company not found"
```

### API Utilities

```python
from tests.utils.api_utils import (
    check_api_health,
    get_indicators,
    verify_api_returns_real_data,
    verify_auth_required
)

# Check API health
assert check_api_health(), "API is not healthy"

# Get indicators and verify real data
indicators = get_indicators()
assert len(indicators) >= 60, "Not enough indicators"

# Verify endpoint returns real data
assert verify_api_returns_real_data("/api/indicators/definitions", expected_count=60)

# Verify authentication is required for mutations
assert verify_auth_required("/api/companies", method="POST")
```

## Best Practices

1. **Use Real Data**: Integration tests should verify actual functionality, not mocks
2. **Clean Up**: Always clean up test data after tests complete
3. **Verify Results**: Query database to confirm operations succeeded
4. **Handle Errors**: Use try/except blocks and provide meaningful error messages
5. **Timeouts**: Use timeouts for API calls to prevent hanging tests
6. **Idempotent**: Tests should be repeatable without side effects

## Notes

- All utilities are designed to work with the actual database and API
- No mocking is used in integration tests
- Utilities handle connection management and cleanup automatically
- Error handling is built-in to prevent test failures from connection issues
