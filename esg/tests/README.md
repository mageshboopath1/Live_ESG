# Integration Tests

This directory contains integration tests for the ESG Intelligence Platform. These tests verify that all services work together correctly and that the system functions end-to-end.

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and shared fixtures
├── requirements.txt            # Python dependencies for tests
├── integration/                # Integration test modules
│   ├── test_database.py        # Database connectivity and schema tests
│   ├── test_services.py        # Service health checks
│   ├── test_api_gateway.py     # API endpoint tests
│   ├── test_pipeline.py        # End-to-end pipeline tests
│   └── test_frontend.py        # Frontend integration tests
├── fixtures/                   # Test data and fixtures
└── utils/                      # Test utilities and helpers
```

## Prerequisites

1. **Services Running**: All services must be running before executing tests:
   ```bash
   cd infra
   docker-compose up -d
   ```

2. **Python Dependencies**: Install test dependencies using `uv`:
   ```bash
   cd tests
   uv sync
   ```

3. **Environment Variables**: Tests use the following defaults (can be overridden):
   - `DB_HOST=localhost`
   - `DB_PORT=5432`
   - `DB_NAME=moz`
   - `DB_USER=drfitz`
   - `DB_PASSWORD=h4i1hydr4`
   - `API_BASE_URL=http://localhost:8000`
   - `FRONTEND_BASE_URL=http://localhost:3000`
   - `MINIO_ENDPOINT=localhost:9000`
   - `RABBITMQ_HOST=localhost`
   - `REDIS_HOST=localhost`

## Running Tests

### Quick Start (Recommended)

**Option 1: Run Full Test Suite with Health Check**
```bash
cd tests
./run_integration_tests.sh
```

The test runner script will:
- Check if services are running (start them if not)
- Wait for services to be healthy
- Run health check to verify system readiness
- Run all integration tests
- Generate test report with pass/fail summary
- Display color-coded output

**Option 2: Run Health Check Only**
```bash
cd tests
./health_check.sh
```

The health check script will:
- Verify all services are running and healthy
- Check database tables have data
- Verify API endpoints are accessible
- Display color-coded status report
- Exit with status code 0 if healthy, 1 if unhealthy

**Option 3: Run Tests Manually**
```bash
cd tests
./run_tests.sh
```

The test runner script will:
- Check if uv is installed
- Check if services are running
- Run all integration tests
- Display colored output

### Run All Tests
```bash
cd tests
uv run pytest integration/ -v
```

### Run Specific Test Module
```bash
cd tests
uv run pytest integration/test_database.py -v
uv run pytest integration/test_services.py -v
uv run pytest integration/test_api_gateway.py -v
uv run pytest integration/test_pipeline.py -v
uv run pytest integration/test_frontend.py -v
```

### Run Specific Test
```bash
cd tests
uv run pytest integration/test_database.py::test_brsr_indicators_seeded -v
```

### Run with Output
```bash
cd tests
uv run pytest integration/ -v -s
```

### Run and Stop on First Failure
```bash
cd tests
uv run pytest integration/ -v -x
```

### Run from Project Root
```bash
uv run --directory tests pytest tests/integration/ -v
```

## Health Check

The `health_check.sh` script provides comprehensive system health verification:

### Service Health Checks
- PostgreSQL: Database connectivity
- MinIO: Object storage availability
- RabbitMQ: Message queue connectivity
- Redis: Cache availability
- API Gateway: REST API accessibility
- Frontend: Web application availability

### Database Verification
- BRSR Indicators: Verifies 60+ indicators are seeded
- Companies: Checks if company data exists
- Document Embeddings: Verifies embeddings table
- Extracted Indicators: Checks extraction results
- ESG Scores: Verifies score calculations

### API Endpoint Tests
- GET /api/companies: Public company endpoint
- GET /api/indicators/definitions: BRSR indicator definitions
- GET /api/scores: Score data endpoint
- GET /api/reports: Report data endpoint

### Usage
```bash
# Run health check
cd tests
./health_check.sh

# Use in scripts
if ./health_check.sh; then
    echo "System is healthy"
else
    echo "System has issues"
fi
```

### Output
- ✓ Green: Service/check is healthy
- ✗ Red: Service/check failed (critical)
- ⚠ Yellow: Warning (non-critical, e.g., empty tables)

## Test Categories

### Database Tests (`test_database.py`)
- Database connectivity
- Required tables exist
- BRSR indicators are properly seeded (60+ indicators)
- pgvector extension is installed
- Foreign key constraints exist
- Indexes are created

**Key Tests:**
- `test_brsr_indicators_seeded`: Verifies all BRSR indicators from Annexure I are seeded
- `test_brsr_indicators_all_attributes`: Verifies all 9 attributes are present
- `test_brsr_indicators_pillars_assigned`: Verifies E/S/G pillar assignments

### Service Health Tests (`test_services.py`)
- PostgreSQL health and connectivity
- MinIO health and connectivity
- RabbitMQ health and connectivity
- Redis health and connectivity
- Service-specific operations

**Key Tests:**
- `test_postgresql_health`: Database is accessible
- `test_minio_health`: Object storage is accessible
- `test_rabbitmq_health`: Message queue is accessible
- `test_redis_health`: Cache is accessible

### API Gateway Tests (`test_api_gateway.py`)
- API endpoints return actual data from database
- GET endpoints work without authentication
- POST endpoints require authentication
- Responses contain real data, not mocks
- Error handling

**Key Tests:**
- `test_get_companies_no_auth`: Public access to companies
- `test_get_indicators_returns_real_brsr_data`: Verifies real BRSR data, not mocks
- `test_post_requires_authentication`: Mutations require auth

### Pipeline Tests (`test_pipeline.py`)
- Document upload to MinIO
- Embeddings generation and storage
- Extraction service processing
- Scores calculation
- Data verification at each step

**Key Tests:**
- `test_minio_document_upload`: Document storage works
- `test_embeddings_storage_structure`: Embeddings table is ready
- `test_scores_calculation_readiness`: Score calculation is ready
- `test_full_pipeline_simulation`: All pipeline components are in place

### Frontend Tests (`test_frontend.py`)
- Frontend is accessible
- Frontend can fetch data without auth
- Frontend handles API errors
- CORS support
- Static assets are served

**Key Tests:**
- `test_frontend_can_fetch_companies`: Frontend can access company data
- `test_frontend_can_fetch_indicators`: Frontend can access indicator data
- `test_frontend_cors_support`: CORS is configured

## Test Principles

These integration tests follow strict principles:

1. **No Mocking**: Tests use real services and databases
2. **Data Verification**: Tests query the database to verify actual data exists
3. **Real Functionality**: Tests verify actual system behavior, not just HTTP 200 responses
4. **Idempotent**: Tests can be run multiple times without side effects
5. **Isolated**: Tests clean up after themselves where necessary

## Interpreting Results

### Success Indicators
- ✓ All tests pass
- ✓ BRSR indicators count >= 60
- ✓ All 9 attributes present
- ✓ All services healthy
- ✓ API returns real data from database

### Common Issues

**Database Connection Failed**
- Ensure PostgreSQL is running: `docker ps | grep postgres`
- Check connection parameters in environment variables

**BRSR Indicators Not Seeded**
- Run database initialization: `cd infra && docker-compose up -d`
- Check db-init logs: `docker logs esg-db-init`

**API Gateway Not Accessible**
- Ensure API Gateway is running: `docker ps | grep api-gateway`
- Check API Gateway logs: `docker logs esg-api-gateway`

**Frontend Not Accessible**
- Ensure Frontend is running: `docker ps | grep frontend`
- Check Frontend logs: `docker logs esg-frontend`

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```bash
# Start services
cd infra && docker-compose up -d

# Wait for services to be healthy
sleep 30

# Run tests
cd tests && uv run pytest integration/ -v --tb=short

# Stop services
cd infra && docker-compose down
```

## Adding New Tests

When adding new integration tests:

1. Place them in the appropriate test module
2. Use fixtures from `conftest.py`
3. Verify actual data, not just response codes
4. Add cleanup if the test modifies data
5. Document what the test verifies

Example:
```python
def test_new_feature(db_cursor, api_base_url):
    """Test new feature works end-to-end"""
    # 1. Setup (if needed)
    
    # 2. Execute action
    response = requests.get(f"{api_base_url}/api/new-endpoint")
    
    # 3. Verify response
    assert response.status_code == 200
    
    # 4. Verify data in database
    db_cursor.execute("SELECT COUNT(*) FROM new_table")
    count = db_cursor.fetchone()[0]
    assert count > 0, "Data not written to database"
    
    # 5. Cleanup (if needed)
```

## Troubleshooting

### Tests Hang
- Check if services are responding: `docker ps`
- Increase timeout values in test code
- Check for network issues

### Tests Fail Intermittently
- Services may not be fully ready - increase wait time
- Check for resource constraints (CPU, memory)
- Run tests sequentially: `pytest -n 1`

### Database Tests Fail
- Verify database schema is up to date
- Check if migrations have been applied
- Verify BRSR indicators are seeded

## Support

For issues or questions about integration tests:
1. Check service logs: `docker-compose logs [service-name]`
2. Verify all services are running: `docker-compose ps`
3. Review test output with `-v -s` flags for detailed information
