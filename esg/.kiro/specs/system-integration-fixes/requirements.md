# Requirements Document

## Introduction

The ESG Intelligence Platform has been deployed but has critical integration issues preventing it from functioning properly. The system requires fixes for database initialization, authentication configuration, service integration testing, and a consolidated testing framework. This spec addresses the gaps between individual service tests and actual end-to-end system functionality.

## Glossary

- **Platform**: The ESG Intelligence Platform system
- **BRSR Indicators**: Business Responsibility and Sustainability Report Core indicators that must be seeded in the database
- **API Gateway**: FastAPI service that provides REST endpoints and handles authentication
- **Frontend**: Vue 3 application that displays ESG data to users
- **Authentication Middleware**: JWT and API key-based authentication system
- **Integration Tests**: Tests that verify multiple services work together correctly
- **E2E Tests**: End-to-end tests that verify the complete user workflow
- **Database Seeding**: Process of populating initial data required for system operation
- **Health Checks**: Endpoints that verify service availability and readiness

## Requirements

### Requirement 1: BRSR Indicators Database Seeding

**User Story:** As a platform operator, I want all BRSR Core indicators from Annexure I to be automatically seeded during database initialization, so that the extraction service has the complete set of required indicator definitions.

#### Acceptance Criteria

1. WHEN the database is initialized, THE Platform SHALL seed all BRSR Core indicators from Annexure I into the brsr_indicators table
2. THE Platform SHALL include all 9 BRSR attributes with their complete set of parameters as defined in the official BRSR Core framework
3. THE Platform SHALL assign correct pillar values (E, S, G) to each indicator based on the attribute classification
4. THE Platform SHALL include measurement units, weights, data assurance approaches, and BRSR references for each indicator
5. WHEN the seeding script runs multiple times, THE Platform SHALL handle duplicate entries gracefully using INSERT ON CONFLICT
6. THE Platform SHALL verify that the seeded indicator count matches the expected count from the BRSR Core framework

### Requirement 2: Authentication Configuration for Public Endpoints

**User Story:** As a frontend developer, I want public API endpoints to be accessible without authentication, so that users can view company data and indicators without logging in.

#### Acceptance Criteria

1. THE API Gateway SHALL allow unauthenticated access to GET /api/companies endpoints
2. THE API Gateway SHALL allow unauthenticated access to GET /api/indicators endpoints
3. THE API Gateway SHALL allow unauthenticated access to GET /api/scores endpoints
4. THE API Gateway SHALL allow unauthenticated access to GET /api/reports endpoints
5. THE API Gateway SHALL require authentication only for POST, PUT, DELETE operations

### Requirement 3: Frontend Authentication Integration

**User Story:** As a frontend user, I want the application to work without requiring authentication for viewing data, so that I can explore ESG information freely.

#### Acceptance Criteria

1. THE Frontend SHALL not send authentication headers for GET requests to public endpoints
2. THE Frontend SHALL display company data without requiring user login
3. THE Frontend SHALL display indicator data without requiring user login
4. THE Frontend SHALL display score data without requiring user login
5. WHEN authentication is required, THE Frontend SHALL display a clear login prompt

### Requirement 4: Comprehensive Integration Testing

**User Story:** As a platform operator, I want a comprehensive test suite that verifies all services work together, so that I can validate the entire system is functioning correctly.

#### Acceptance Criteria

1. THE Platform SHALL provide integration tests that verify database connectivity from all services
2. THE Platform SHALL provide integration tests that verify RabbitMQ message flow between services
3. THE Platform SHALL provide integration tests that verify MinIO object storage operations
4. THE Platform SHALL provide integration tests that verify API Gateway endpoints return correct data
5. THE Platform SHALL provide integration tests that verify the complete ingestion-to-extraction pipeline

### Requirement 5: Consolidated Testing Framework

**User Story:** As a developer, I want all integration tests in a single location with a single command to run them, so that I can easily verify system health.

#### Acceptance Criteria

1. THE Platform SHALL provide a tests/ directory at the project root containing all integration tests
2. THE Platform SHALL provide a single command to run all integration tests
3. THE Platform SHALL provide test fixtures that set up required test data
4. THE Platform SHALL provide test utilities for common operations (database queries, API calls)
5. THE Platform SHALL generate a comprehensive test report showing pass/fail status for each component

### Requirement 6: Service Health Verification

**User Story:** As a platform operator, I want to verify all services are healthy and ready, so that I can confirm the system is operational.

#### Acceptance Criteria

1. THE Platform SHALL provide health check endpoints for all services
2. THE Platform SHALL verify database connectivity in health checks
3. THE Platform SHALL verify message queue connectivity in health checks
4. THE Platform SHALL verify object storage connectivity in health checks
5. THE Platform SHALL provide a script that checks health of all services and reports status

### Requirement 7: Database Migration Verification

**User Story:** As a platform operator, I want to verify all database migrations have been applied correctly, so that I can ensure schema integrity.

#### Acceptance Criteria

1. THE Platform SHALL verify all required tables exist
2. THE Platform SHALL verify all required indexes exist
3. THE Platform SHALL verify all required foreign key constraints exist
4. THE Platform SHALL verify pgvector extension is installed and configured
5. THE Platform SHALL verify BRSR indicators are seeded with expected count

### Requirement 8: End-to-End Workflow Testing

**User Story:** As a platform operator, I want to test the complete workflow from document ingestion to score calculation, so that I can verify the entire pipeline works.

#### Acceptance Criteria

1. THE Platform SHALL provide a test that uploads a sample PDF document
2. THE Platform SHALL verify the document is processed by the embeddings service
3. THE Platform SHALL verify embeddings are stored in the database
4. THE Platform SHALL verify the extraction service processes the document
5. THE Platform SHALL verify extracted indicators and scores are stored in the database

### Requirement 9: API Gateway Endpoint Testing

**User Story:** As a developer, I want to test all API Gateway endpoints with real data, so that I can verify they return correct responses.

#### Acceptance Criteria

1. THE Platform SHALL test GET /api/companies returns company list
2. THE Platform SHALL test GET /api/companies/{id}/indicators returns indicators for a company
3. THE Platform SHALL test GET /api/companies/{id}/scores returns scores for a company
4. THE Platform SHALL test GET /api/indicators/definitions returns BRSR indicator definitions
5. THE Platform SHALL test error handling for invalid requests

### Requirement 10: Frontend Integration Testing

**User Story:** As a frontend developer, I want to verify the frontend can communicate with the API Gateway, so that I can ensure the UI displays data correctly.

#### Acceptance Criteria

1. THE Platform SHALL verify the frontend can fetch company data from the API
2. THE Platform SHALL verify the frontend can fetch indicator data from the API
3. THE Platform SHALL verify the frontend can fetch score data from the API
4. THE Platform SHALL verify the frontend displays error messages for failed API calls
5. THE Platform SHALL verify the frontend handles loading states correctly

### Requirement 11: Test Data Management

**User Story:** As a developer, I want test data to be automatically created and cleaned up, so that tests are reproducible and don't interfere with each other.

#### Acceptance Criteria

1. THE Platform SHALL provide fixtures that create test companies
2. THE Platform SHALL provide fixtures that create test documents
3. THE Platform SHALL provide fixtures that create test embeddings
4. THE Platform SHALL provide fixtures that create test indicators
5. THE Platform SHALL clean up test data after tests complete

### Requirement 12: Continuous Integration Support

**User Story:** As a DevOps engineer, I want tests to run in CI/CD pipelines, so that I can catch integration issues before deployment.

#### Acceptance Criteria

1. THE Platform SHALL provide a script that starts all services for testing
2. THE Platform SHALL wait for all services to be healthy before running tests
3. THE Platform SHALL run all integration tests and report results
4. THE Platform SHALL stop all services after tests complete
5. THE Platform SHALL exit with appropriate status codes for CI/CD integration

### Requirement 13: Real Functionality Verification

**User Story:** As a platform operator, I want tests to verify actual system functionality rather than just passing superficially, so that I can trust the test results indicate real working features.

#### Acceptance Criteria

1. THE Platform SHALL verify database tables contain expected data after seeding operations
2. THE Platform SHALL verify API endpoints return actual data from the database, not mock responses
3. THE Platform SHALL verify message queue operations by confirming messages are consumed and processed
4. THE Platform SHALL verify file storage operations by confirming files are retrievable after upload
5. THE Platform SHALL verify authentication by testing both successful and failed authentication scenarios
6. THE Platform SHALL verify each service can perform its core function end-to-end without mocking dependencies
