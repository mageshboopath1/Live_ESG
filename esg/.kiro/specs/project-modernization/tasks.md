# Implementation Plan

- [x] 1. Prepare foundation and tooling
  - Update project-wide configuration files
  - Create standardized templates
  - Document migration procedures
  - _Requirements: 1.1, 2.1, 4.1, 10.1_

- [x] 1.1 Create Dockerfile template and documentation
  - Create a reference Dockerfile template in `.kiro/templates/Dockerfile.template`
  - Document the multi-stage build pattern with inline comments
  - Create a migration checklist document
  - _Requirements: 3.1, 3.2, 4.1, 4.4_

- [x] 1.2 Create shared dependency version reference
  - Create `.kiro/docs/DEPENDENCY_VERSIONS.md` documenting blessed versions
  - List all shared dependencies (psycopg2-binary, pika, boto3, pydantic, etc.)
  - Document version alignment strategy
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 1.3 Update root .gitignore for consistency
  - Ensure .python-version files are tracked
  - Ensure uv.lock files are tracked
  - Ensure .venv directories are ignored
  - _Requirements: 2.2, 8.1_

- [x] 2. Modernize company-catalog service
  - Update to Python 3.12
  - Implement multi-stage Docker build with UV
  - Test service functionality
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 7.1_

- [x] 2.1 Update company-catalog Python version and dependencies
  - Update `.python-version` to `3.12`
  - Update `pyproject.toml` requires-python to `>=3.12`
  - Run `uv sync` to update uv.lock
  - Verify no dependency conflicts
  - _Requirements: 1.1, 1.2, 2.2, 2.5_

- [x] 2.2 Create multi-stage Dockerfile for company-catalog
  - Replace existing `dockerfile` with multi-stage build
  - Use `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` as builder
  - Use `python:3.12-slim` as runtime
  - Copy only .venv and source code to runtime
  - Set PYTHONUNBUFFERED=1 and PYTHONDONTWRITEBYTECODE=1
  - _Requirements: 1.3, 2.1, 3.1, 3.2, 3.3, 4.2, 4.4_

- [x] 2.3 Build and test company-catalog service
  - Build Docker image: `docker build -t esg-company-catalog:latest services/company-catalog`
  - Test service in docker-compose: `docker-compose up company-catalog`
  - Verify database connectivity and functionality
  - Compare image size with previous version
  - _Requirements: 3.4, 7.1, 7.2, 7.3, 10.3_

- [x] 3. Modernize ingestion service
  - Update to Python 3.12
  - Implement multi-stage Docker build with UV
  - Test service functionality
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 7.1_

- [x] 3.1 Update ingestion Python version and dependencies
  - Update `.python-version` to `3.12`
  - Update `pyproject.toml` requires-python to `>=3.12`
  - Run `uv sync` to update uv.lock
  - Verify selenium and aria2 compatibility
  - _Requirements: 1.1, 1.2, 2.2, 2.5_

- [x] 3.2 Create multi-stage Dockerfile for ingestion
  - Replace existing `dockerfile` with multi-stage build
  - Use `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` as builder
  - Use `python:3.12-slim` as runtime
  - Install aria2 in runtime stage
  - Set environment variables properly
  - _Requirements: 1.3, 2.1, 3.1, 3.2, 3.3, 4.2, 4.4_

- [x] 3.3 Build and test ingestion service
  - Build Docker image: `docker build -t esg-ingestion:latest services/ingestion`
  - Test service in docker-compose
  - Verify PDF download functionality
  - Verify MinIO integration
  - _Requirements: 3.4, 7.1, 7.2, 7.3, 10.3_

- [x] 4. Modernize embeddings service
  - Update to Python 3.12
  - Implement multi-stage Docker build with UV
  - Handle XML dependencies properly
  - Test service functionality
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 7.1_

- [x] 4.1 Update embeddings Python version and dependencies
  - Update `.python-version` to `3.12`
  - Update `pyproject.toml` requires-python to `>=3.12`
  - Run `uv sync` to update uv.lock
  - Verify pdfplumber and pymupdf compatibility
  - _Requirements: 1.1, 1.2, 2.2, 2.5_

- [x] 4.2 Create multi-stage Dockerfile for embeddings
  - Update existing `dockerfile` to ensure proper multi-stage pattern
  - Use `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` as builder
  - Install libxml2-dev, libxslt-dev, build-essential in builder
  - Use `python:3.12-slim` as runtime
  - Install libxml2, libxslt1.1 in runtime
  - _Requirements: 1.3, 2.1, 3.1, 3.2, 3.3, 4.2, 4.4_

- [x] 4.3 Build and test embeddings service
  - Build Docker image: `docker build -t esg-embeddings:latest services/embeddings`
  - Test service in docker-compose
  - Verify embedding generation
  - Verify vector storage in PostgreSQL
  - _Requirements: 3.4, 7.1, 7.2, 7.3, 10.3_

- [x] 5. Modernize extraction service
  - Update to Python 3.12
  - Ensure multi-stage Docker build uses UV
  - Test service functionality
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 7.1_

- [x] 5.1 Update extraction Python version and dependencies
  - Update `.python-version` to `3.12`
  - Update `pyproject.toml` requires-python to `>=3.12`
  - Run `uv sync` to update uv.lock
  - Verify LangChain and GenAI compatibility
  - _Requirements: 1.1, 1.2, 2.2, 2.5_

- [x] 5.2 Verify extraction Dockerfile follows standards
  - Review existing Dockerfile (already multi-stage)
  - Ensure Python 3.12 base images
  - Ensure UV is used for dependency installation
  - Verify health check is properly configured
  - _Requirements: 1.3, 2.1, 3.1, 3.2, 4.2, 4.3, 4.4_

- [x] 5.3 Build and test extraction service
  - Build Docker image: `docker build -t esg-extraction:latest services/extraction`
  - Test service in docker-compose
  - Verify indicator extraction
  - Verify health check endpoint
  - _Requirements: 3.4, 7.1, 7.2, 7.3, 7.4, 10.3_

- [x] 6. Modernize api-gateway service
  - Update to Python 3.12
  - Ensure multi-stage Docker build uses UV
  - Test all endpoints
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 7.1_

- [x] 6.1 Update api-gateway Python version and dependencies
  - Update `.python-version` to `3.12`
  - Update `pyproject.toml` requires-python from `>=3.11` to `>=3.12`
  - Run `uv sync` to update uv.lock
  - Verify FastAPI and all dependencies work with Python 3.12
  - _Requirements: 1.1, 1.2, 2.2, 2.5_

- [x] 6.2 Verify api-gateway Dockerfile follows standards
  - Review existing Dockerfile (already multi-stage)
  - Ensure Python 3.12 base images
  - Ensure UV is used for dependency installation
  - Verify health check is properly configured
  - _Requirements: 1.3, 2.1, 3.1, 3.2, 4.2, 4.3, 4.4_

- [x] 6.3 Build and test api-gateway service
  - Build Docker image: `docker build -t esg-api-gateway:latest services/api-gateway`
  - Test service in docker-compose
  - Verify all API endpoints respond correctly
  - Verify authentication works
  - Verify Redis caching works
  - _Requirements: 3.4, 7.1, 7.2, 7.3, 10.3_

- [x] 6.4 Run api-gateway integration tests
  - Run pytest tests in tests/integration/test_api_gateway.py
  - Verify all endpoints pass tests
  - Check test coverage
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 7. Modernize airflow service
  - Update to Python 3.12
  - Implement UV for dependency management
  - Update DAG for DockerOperator usage
  - Test DAG execution
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 5.1, 5.2, 5.3_

- [x] 7.1 Update Airflow to Python 3.12
  - Update Dockerfile to use `apache/airflow:2.8.1-python3.12` base image
  - Update requirements.txt dependencies if needed
  - Verify Airflow providers are compatible
  - _Requirements: 1.1, 1.4, 2.1_

- [x] 7.2 Implement UV in Airflow Dockerfile
  - Add UV installation in Dockerfile
  - Convert requirements.txt to pyproject.toml
  - Use UV to install Python dependencies
  - Maintain compatibility with Airflow's pip-based system
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 7.3 Enhance Airflow DAG for production use
  - Review and update services/airflow/dags/esg_pipeline_dag.py
  - Ensure all services use DockerOperator
  - Remove Python callables that duplicate service logic
  - Add proper error handling and retries
  - Configure task dependencies correctly
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.3, 7.4_

- [x] 7.4 Build and test Airflow service
  - Build Docker image: `docker build -t esg-airflow:latest services/airflow`
  - Start Airflow with docker-compose
  - Access Airflow UI at http://localhost:8081
  - Trigger test DAG run
  - Verify all tasks execute successfully
  - _Requirements: 5.1, 5.2, 5.3, 10.3_

- [ ] 8. Modernize infrastructure components
  - Update db-init to Python 3.12
  - Implement UV in dockerfile with multistage build
  - Ensure consistent patterns
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 8.1 Update db-init Python version and dependencies
  - Update `infra/db-init/.python-version` to `3.12`
  - Update `infra/db-init/pyproject.toml` requires-python from `>=3.11` to `>=3.12`
  - Run `uv sync` in db-init directory
  - _Requirements: 1.1, 1.2, 2.2, 2.5_

- [x] 8.2 Verify db-init Dockerfile
  - Review infra/db-init/Dockerfile
  - Ensure it uses Python 3.12
  - Ensure UV is used for dependencies
  - _Requirements: 1.3, 2.1, 3.1_

- [x] 8.3 Test db-init functionality
  - Build db-init image
  - Test database initialization
  - Verify BRSR indicators are seeded correctly
  - _Requirements: 7.1, 7.2, 10.3_

- [ ] 9. Remove and migrate legacy scripts
  - Identify scripts to remove
  - Migrate functionality to Airflow
  - Update documentation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 9.1 Audit scripts directory
  - Review all scripts in scripts/ directory
  - Categorize as: remove, migrate, or keep
  - Document decision for each script
  - _Requirements: 6.1, 6.2_

- [ ] 9.2 Remove duplicate orchestration scripts
  - Delete `scripts/pipeline_orchestrator.py`
  - Delete `scripts/publish_extraction_tasks.py`
  - Delete `scripts/trigger_extraction.py`
  - Update any documentation referencing these scripts
  - _Requirements: 6.1, 6.2, 6.5_

- [ ] 9.3 Create Airflow DAG for cleanup operations
  - Create `services/airflow/dags/cleanup_dag.py`
  - Migrate functionality from `scripts/cleanup_pipeline_data.py`
  - Implement as Airflow tasks
  - Test cleanup DAG
  - _Requirements: 5.1, 6.3, 6.4_

- [ ] 9.4 Update scripts README
  - Update `scripts/README.md` to reflect removed scripts
  - Document which scripts remain and their purpose
  - Add references to Airflow for orchestration
  - _Requirements: 6.4, 6.5_

- [ ] 10. Update docker-compose configurations
  - Update service references
  - Ensure network configurations are correct
  - Test full stack startup
  - _Requirements: 7.1, 7.2, 10.2, 10.3_

- [ ] 10.1 Update docker-compose.yml
  - Verify all service image names are correct
  - Ensure all services use updated Dockerfiles
  - Verify environment variable passing
  - Check network configurations
  - _Requirements: 7.1, 7.2, 10.2_

- [ ] 10.2 Update docker-compose.airflow.yml
  - Update Airflow image reference
  - Verify Airflow environment variables
  - Ensure Docker socket is mounted for DockerOperator
  - Check Airflow service dependencies
  - _Requirements: 5.1, 7.1, 7.2, 10.2_

- [ ] 10.3 Test full stack with docker-compose
  - Stop all running containers
  - Build all images: `docker-compose build`
  - Start infrastructure: `docker-compose up -d postgres minio rabbitmq redis`
  - Wait for health checks to pass
  - Start application services: `docker-compose up -d`
  - Verify all services are running
  - _Requirements: 10.2, 10.3, 10.4_

- [ ] 11. Run integration tests
  - Execute full test suite
  - Verify all services work together
  - Document any issues
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 10.3_

- [ ] 11.1 Run infrastructure tests
  - Run `tests/integration/test_database.py`
  - Verify database connectivity and schema
  - Check MinIO bucket access
  - Verify RabbitMQ queues
  - _Requirements: 7.1, 7.2, 10.3_

- [ ] 11.2 Run service integration tests
  - Run `tests/integration/test_services.py`
  - Verify service-to-service communication
  - Check message queue integration
  - Verify data flow through pipeline
  - _Requirements: 7.1, 7.2, 7.3, 10.3_

- [ ] 11.3 Run API integration tests
  - Run `tests/integration/test_api_gateway.py`
  - Verify all API endpoints
  - Check authentication and authorization
  - Verify caching behavior
  - _Requirements: 7.1, 7.2, 7.3, 10.3_

- [ ] 11.4 Run end-to-end pipeline test
  - Run `tests/integration/test_pipeline.py`
  - Verify complete data flow from ingestion to extraction
  - Check data quality and completeness
  - Verify ESG scores are calculated
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 10.3_

- [ ] 12. Update documentation
  - Update README files
  - Create migration guide
  - Document new workflows
  - _Requirements: 6.4, 6.5, 10.1, 10.3_

- [ ] 12.1 Update root README.md
  - Update Python version requirements to 3.12
  - Update setup instructions for UV
  - Update Docker build instructions
  - Add link to migration guide
  - _Requirements: 1.1, 2.1, 10.1_

- [ ] 12.2 Create MIGRATION_GUIDE.md
  - Document all changes made
  - Explain Python 3.12 migration
  - Explain UV adoption
  - Document Dockerfile changes
  - Explain Airflow migration
  - List removed scripts and alternatives
  - _Requirements: 1.1, 2.1, 3.1, 5.1, 6.1, 6.5_

- [ ] 12.3 Update service README files
  - Update services/api-gateway/README.md
  - Update services/extraction/README.md
  - Update services/embeddings/README.md
  - Update services/ingestion/README.md
  - Update services/company-catalog/README.md
  - Document Python 3.12 and UV usage
  - _Requirements: 1.1, 2.1, 10.1_

- [ ] 12.4 Update Airflow documentation
  - Update services/airflow/README.md
  - Update AIRFLOW_QUICKSTART.md
  - Document new DAG structure
  - Explain how to trigger pipelines via Airflow
  - Document removed scripts and Airflow alternatives
  - _Requirements: 5.1, 5.2, 6.4, 6.5, 10.1_

- [ ] 12.5 Update infrastructure documentation
  - Update infra/README.md
  - Document docker-compose changes
  - Update quick start guide
  - Document Python 3.12 requirement
  - _Requirements: 1.1, 10.1, 10.2_

- [ ] 13. Performance validation
  - Measure Docker image sizes
  - Measure build times
  - Compare with baseline
  - Document improvements
  - _Requirements: 3.4, 10.3, 10.4_

- [ ] 13.1 Measure and document image sizes
  - Run `docker images` and record sizes for all services
  - Compare with previous image sizes (if available)
  - Document size reductions in a summary file
  - Target: 20-40% reduction from multi-stage builds
  - _Requirements: 3.4_

- [ ] 13.2 Measure and document build times
  - Time Docker builds for each service
  - Test with and without cache
  - Document build time improvements
  - Target: 10-30% improvement with UV
  - _Requirements: 10.4_

- [ ] 13.3 Create performance summary report
  - Create `.kiro/specs/project-modernization/PERFORMANCE_REPORT.md`
  - Document image size comparisons
  - Document build time comparisons
  - Document any performance issues found
  - List recommendations for further optimization
  - _Requirements: 3.4, 10.3, 10.4_
