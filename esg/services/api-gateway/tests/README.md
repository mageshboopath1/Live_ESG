# API Gateway Tests

This directory contains all test files for the API Gateway service.

## Test Files

### Authentication Tests
- `test_auth.py` - Authentication and authorization tests
- `test_public_endpoints.py` - Public endpoint access tests

### Endpoint Tests
- `test_companies_endpoints.py` - Company endpoints tests
- `test_indicators_endpoints.py` - BRSR indicators endpoints tests
- `test_reports_endpoints.py` - Reports endpoints tests
- `test_scores_endpoints.py` - ESG scores endpoints tests
- `test_citations_endpoints.py` - Citations endpoints tests

### Infrastructure Tests
- `test_cache.py` - Redis caching tests
- `test_db_setup.py` - Database setup and connection tests

## Running Tests

### Run all tests
```bash
uv run pytest tests/ -v
```

### Run specific test file
```bash
uv run pytest tests/test_auth.py -v
```

### Run specific test category
```bash
# Run only authentication tests
uv run pytest tests/test_auth.py tests/test_public_endpoints.py -v

# Run only endpoint tests
uv run pytest tests/test_*_endpoints.py -v
```

## Test Requirements

Tests require:
- PostgreSQL database
- Redis cache
- Test data seeded in database

See main [README.md](../README.md) for setup instructions.

## Test Configuration

Tests use environment variables from `.env` file:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`
- `SECRET_KEY` for JWT tokens

## Coverage

Generate coverage report:
```bash
uv run pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```
