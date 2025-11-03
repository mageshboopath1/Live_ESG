# Requirements Document

## Introduction

This document outlines the requirements for modernizing the ESG Intelligence Platform to follow best practices for Python development, Docker containerization, and Airflow-based orchestration. The modernization focuses on standardizing Python versions, adopting UV package manager consistently, implementing multi-stage Docker builds, and migrating all orchestration logic to Airflow.

## Glossary

- **Platform**: The ESG Intelligence Platform system
- **Service**: A microservice component (api-gateway, extraction, embeddings, ingestion, company-catalog)
- **UV**: A fast Python package installer and resolver
- **Multi-stage Build**: Docker build pattern that separates build dependencies from runtime dependencies
- **Airflow**: Apache Airflow workflow orchestration platform
- **DAG**: Directed Acyclic Graph - Airflow workflow definition
- **Legacy Script**: Python scripts in the scripts/ directory that duplicate Airflow functionality

## Requirements

### Requirement 1: Python Version Standardization

**User Story:** As a platform developer, I want all services to use Python 3.12 consistently, so that we have predictable behavior and simplified dependency management.

#### Acceptance Criteria

1. WHEN a developer inspects any service directory, THE Platform SHALL contain a .python-version file specifying "3.12"
2. WHEN a developer reviews any pyproject.toml file, THE Platform SHALL specify "requires-python = '>=3.12'" 
3. WHEN a developer examines any Dockerfile, THE Platform SHALL use "python:3.12-slim" or "ghcr.io/astral-sh/uv:python3.12-bookworm-slim" as base images
4. WHEN a developer checks the Airflow service, THE Platform SHALL use "apache/airflow:2.8.1-python3.12" as the base image
5. WHEN a developer runs any service, THE Platform SHALL execute using Python 3.12 runtime

### Requirement 2: UV Package Manager Adoption

**User Story:** As a platform developer, I want all services to use UV for dependency management, so that we have fast, reliable, and consistent package installations.

#### Acceptance Criteria

1. WHEN a developer builds any service, THE Platform SHALL use UV for installing dependencies
2. WHEN a developer examines any service directory, THE Platform SHALL contain pyproject.toml and uv.lock files
3. WHEN a developer reviews any Dockerfile, THE Platform SHALL install UV from the official source
4. WHEN a developer checks the Airflow service, THE Platform SHALL use UV instead of pip for Python dependencies
5. WHEN a developer adds a new dependency, THE Platform SHALL update the uv.lock file using UV commands

### Requirement 3: Multi-stage Docker Builds

**User Story:** As a DevOps engineer, I want all services to use multi-stage Docker builds, so that production images are minimal and secure.

#### Acceptance Criteria

1. WHEN a developer reviews any Dockerfile, THE Platform SHALL define a separate builder stage for dependency installation
2. WHEN a developer builds a service image, THE Platform SHALL copy only the virtual environment from builder to runtime stage
3. WHEN a developer inspects a production image, THE Platform SHALL exclude build tools and unnecessary dependencies
4. WHEN a developer measures image sizes, THE Platform SHALL produce runtime images smaller than single-stage equivalents
5. WHEN a developer examines the runtime stage, THE Platform SHALL include only application code and runtime dependencies

### Requirement 4: Consistent Dockerfile Structure

**User Story:** As a platform developer, I want all Dockerfiles to follow the same structure and patterns, so that they are easy to understand and maintain.

#### Acceptance Criteria

1. WHEN a developer reviews any Dockerfile, THE Platform SHALL use consistent stage naming (builder, runtime)
2. WHEN a developer examines any Dockerfile, THE Platform SHALL set PYTHONUNBUFFERED=1 and PYTHONDONTWRITEBYTECODE=1
3. WHEN a developer checks any service Dockerfile, THE Platform SHALL include appropriate health checks
4. WHEN a developer reviews the Dockerfile structure, THE Platform SHALL follow the order: base image, system deps, UV install, dependency copy, dependency install, code copy, environment setup, command
5. WHEN a developer compares Dockerfiles, THE Platform SHALL use consistent patterns for copying files and setting environment variables

### Requirement 5: Airflow-Based Orchestration

**User Story:** As a platform operator, I want all pipeline orchestration to use Airflow, so that we have a single, reliable workflow management system.

#### Acceptance Criteria

1. WHEN an operator triggers a pipeline, THE Platform SHALL execute the workflow through Airflow DAGs
2. WHEN a developer reviews the codebase, THE Platform SHALL contain all orchestration logic in services/airflow/dags/
3. WHEN an operator monitors pipeline execution, THE Platform SHALL provide visibility through the Airflow UI
4. WHEN a developer examines the Airflow DAG, THE Platform SHALL use DockerOperator for service execution
5. WHEN an operator schedules workflows, THE Platform SHALL configure scheduling through Airflow DAG definitions

### Requirement 6: Legacy Script Removal

**User Story:** As a platform maintainer, I want to remove or migrate legacy orchestration scripts, so that we eliminate duplicate functionality and reduce maintenance burden.

#### Acceptance Criteria

1. WHEN a developer reviews the scripts/ directory, THE Platform SHALL contain only utility scripts that do not duplicate Airflow functionality
2. WHEN a developer searches for pipeline orchestration code, THE Platform SHALL find it only in Airflow DAGs
3. WHEN a developer examines removed scripts, THE Platform SHALL have migrated their functionality to Airflow tasks
4. WHEN a developer checks the documentation, THE Platform SHALL reference Airflow for all orchestration workflows
5. WHEN a developer needs to trigger extraction, THE Platform SHALL use Airflow API or UI instead of standalone scripts

### Requirement 7: Service Airflow Compatibility

**User Story:** As a platform developer, I want all services to be compatible with Airflow execution, so that they can be orchestrated through DAGs.

#### Acceptance Criteria

1. WHEN Airflow executes a service, THE Platform SHALL accept configuration through environment variables
2. WHEN a service runs in Airflow, THE Platform SHALL log output to stdout/stderr for Airflow capture
3. WHEN a service completes, THE Platform SHALL exit with appropriate status codes (0 for success, non-zero for failure)
4. WHEN a service encounters an error, THE Platform SHALL provide clear error messages for Airflow logging
5. WHEN Airflow monitors a service, THE Platform SHALL expose health check endpoints where applicable

### Requirement 8: Project Structure Optimization

**User Story:** As a platform developer, I want a clean and logical project structure, so that I can easily navigate and understand the codebase.

#### Acceptance Criteria

1. WHEN a developer explores the repository, THE Platform SHALL organize services in the services/ directory
2. WHEN a developer looks for infrastructure code, THE Platform SHALL find it in the infra/ directory
3. WHEN a developer searches for tests, THE Platform SHALL find them in the tests/ directory or service-specific test directories
4. WHEN a developer checks for documentation, THE Platform SHALL find README files at appropriate levels
5. WHEN a developer reviews the root directory, THE Platform SHALL see minimal clutter with clear purpose for each file

### Requirement 9: Dependency Consistency

**User Story:** As a platform developer, I want consistent dependency versions across services, so that we avoid version conflicts and simplify updates.

#### Acceptance Criteria

1. WHEN a developer reviews shared dependencies, THE Platform SHALL use the same major versions across services
2. WHEN a developer checks database clients, THE Platform SHALL use psycopg2-binary with consistent versions
3. WHEN a developer examines message queue clients, THE Platform SHALL use pika with consistent versions
4. WHEN a developer reviews cloud storage clients, THE Platform SHALL use boto3 with consistent versions
5. WHEN a developer updates a shared dependency, THE Platform SHALL document the change and update all affected services

### Requirement 10: Build and Development Workflow

**User Story:** As a platform developer, I want streamlined build and development workflows, so that I can quickly iterate and test changes.

#### Acceptance Criteria

1. WHEN a developer builds services locally, THE Platform SHALL provide make targets or scripts for common operations
2. WHEN a developer runs services in development, THE Platform SHALL support docker-compose for local orchestration
3. WHEN a developer tests changes, THE Platform SHALL provide clear instructions for running tests
4. WHEN a developer builds Docker images, THE Platform SHALL use consistent naming conventions
5. WHEN a developer needs to rebuild, THE Platform SHALL leverage Docker layer caching effectively
