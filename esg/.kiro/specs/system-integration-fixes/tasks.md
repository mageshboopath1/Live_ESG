# Implementation Plan

## Overview
This implementation plan addresses critical system integration issues in the ESG Intelligence Platform. The tasks focus on fixing BRSR indicator seeding, authentication configuration, and creating a comprehensive integration test suite that verifies real functionality.

## Tasks

- [x] 1. Update BRSR Indicators Seeding with Complete Annexure I Data
  - Update `infra/db-init/main.py` to include ALL parameters from Annexure I
  - Parse the complete BRSR Core framework (9 attributes, 60+ parameters)
  - Ensure all indicators have correct pillar assignments (E/S/G)
  - Add verification to confirm expected indicator count after seeding
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

- [x] 2. Fix API Gateway Authentication for Public Endpoints
  - [x] 2.1 Remove global authentication middleware from API Gateway
    - Modify `services/api-gateway/src/main.py` to not require auth globally
    - Apply authentication per-router instead of globally
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 2.2 Update routers to allow public GET requests
    - Modify companies router to allow GET without auth
    - Modify indicators router to allow GET without auth
    - Modify scores router to allow GET without auth
    - Modify reports router to allow GET without auth
    - Keep POST/PUT/DELETE requiring authentication
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Fix Frontend Authentication Integration
  - [x] 3.1 Update frontend API client to not send auth headers for GET requests
    - Modify API client in `services/frontend/src/api/` to conditionally include auth headers
    - Only send auth headers for POST/PUT/DELETE operations
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Update frontend components to handle unauthenticated access
    - Remove forced authentication checks for viewing data
    - Display login prompt only when attempting mutations
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] 4. Create Consolidated Integration Test Suite
  - [x] 4.1 Set up test directory structure
    - Create `tests/` directory at project root
    - Create `tests/integration/` subdirectory
    - Create `tests/fixtures/` for test data
    - Create `tests/utils/` for test utilities
    - Set up `conftest.py` with pytest fixtures
    - _Requirements: 5.1, 5.2_

  - [x] 4.2 Implement database integration tests
    - Create `tests/integration/test_database.py`
    - Test database connectivity
    - Test all required tables exist
    - Test BRSR indicators are seeded with correct count (60+)
    - Test pgvector extension is installed
    - Verify actual data in tables, not just schema
    - _Requirements: 4.1, 7.1, 7.2, 7.3, 7.4, 7.5, 13.1_

  - [x] 4.3 Implement service health integration tests
    - Create `tests/integration/test_services.py`
    - Test PostgreSQL health and connectivity
    - Test MinIO health and connectivity
    - Test RabbitMQ health and connectivity
    - Test Redis health and connectivity
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 4.4 Implement API Gateway integration tests
    - Create `tests/integration/test_api_gateway.py`
    - Test GET /api/companies returns actual data from database
    - Test GET /api/indicators/definitions returns real BRSR indicators
    - Test GET /api/companies/{id}/indicators returns actual indicators
    - Test POST endpoints require authentication
    - Verify responses contain real data, not mocks
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 13.2_

  - [x] 4.5 Implement end-to-end pipeline tests
    - Create `tests/integration/test_pipeline.py`
    - Test document upload to MinIO
    - Test embeddings generation and storage
    - Test extraction service processing
    - Test scores calculation
    - Verify data at each step by querying database
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 13.3, 13.4_

  - [x] 4.6 Implement frontend integration tests
    - Create `tests/integration/test_frontend.py`
    - Test frontend can fetch company data without auth
    - Test frontend can fetch indicator data without auth
    - Test frontend displays data correctly
    - Test frontend handles API errors
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 5. Create Test Utilities and Fixtures
  - [x] 5.1 Create database utilities
    - Create `tests/utils/db_utils.py`
    - Implement connection helpers
    - Implement query helpers
    - Implement data verification helpers
    - _Requirements: 5.4, 11.1, 11.2, 11.3, 11.4_

  - [x] 5.2 Create API client utilities
    - Create `tests/utils/api_utils.py`
    - Implement HTTP client helpers
    - Implement authentication helpers
    - Implement response validation helpers
    - _Requirements: 5.4_

  - [x] 5.3 Create test fixtures
    - Create `tests/fixtures/sample_data.py`
    - Create sample company data
    - Create sample indicator data
    - Create sample document data
    - Add sample PDF for testing
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 6. Create Health Check and Test Runner Scripts
  - [x] 6.1 Create health check script
    - Create `tests/health_check.sh`
    - Check all service health endpoints
    - Verify database tables have data
    - Verify API endpoints are accessible
    - Display color-coded status report
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 6.2 Create test runner script
    - Create `tests/run_integration_tests.sh`
    - Start services if not running
    - Wait for services to be healthy
    - Run health check
    - Run all integration tests
    - Generate test report
    - _Requirements: 5.2, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 7. Verify Complete System Integration
  - [x] 7.1 Run complete test suite
    - Execute `tests/run_integration_tests.sh`
    - Verify all tests pass
    - Verify no tests are using mocks
    - Verify all tests query actual database
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [x] 7.2 Verify BRSR indicators are complete
    - Query database for indicator count
    - Verify count matches Annexure I (60+)
    - Verify all 9 attributes are represented
    - Verify all pillars (E/S/G) are assigned
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_

  - [x] 7.3 Verify authentication works correctly
    - Test public GET endpoints work without auth
    - Test mutation endpoints require auth
    - Test frontend can view data without login
    - Test frontend shows login prompt for mutations
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 13.5_

  - [x] 7.4 Verify end-to-end pipeline
    - Upload a test document
    - Verify embeddings are generated
    - Verify extraction processes the document
    - Verify scores are calculated
    - Query database to confirm data at each step
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 13.6_

## Notes

- All integration tests MUST verify actual functionality by querying the database
- Tests MUST NOT use mocks or fake data
- Each test should verify real data exists, not just that endpoints return 200
- The test suite should be runnable with a single command
- Health checks should be run before tests to ensure services are ready
