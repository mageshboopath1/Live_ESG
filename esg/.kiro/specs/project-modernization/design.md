# Design Document

## Overview

This design document outlines the comprehensive modernization of the ESG Intelligence Platform to adopt industry best practices for Python development, containerization, and workflow orchestration. The modernization will standardize on Python 3.12, UV package manager, multi-stage Docker builds, and Airflow-based orchestration while removing legacy scripts and improving project structure.

### Goals

1. **Consistency**: Standardize Python versions, dependency management, and Docker patterns across all services
2. **Performance**: Reduce Docker image sizes and build times through multi-stage builds
3. **Maintainability**: Simplify the codebase by removing duplicate orchestration logic
4. **Reliability**: Centralize workflow orchestration in Airflow for better monitoring and error handling
5. **Developer Experience**: Provide clear patterns and tooling for local development

### Non-Goals

- Changing the core functionality of any service
- Modifying database schemas or API contracts
- Rewriting application logic
- Changing the overall architecture

## Architecture

### Current State

The platform currently has:
- Mixed Python versions (3.10, 3.11, 3.12, 3.14)
- Inconsistent use of UV vs pip
- Mix of single-stage and multi-stage Docker builds
- Duplicate orchestration logic in scripts/ and Airflow
- Inconsistent Dockerfile patterns

### Target State

The modernized platform will have:
- Python 3.12 everywhere
- UV for all dependency management
- Multi-stage Docker builds for all services
- Single source of truth for orchestration (Airflow)
- Consistent Dockerfile patterns and structure
- Clean separation of concerns

### Service Architecture

```
ESG Intelligence Platform
├── Infrastructure Layer
│   ├── PostgreSQL (database)
│   ├── MinIO (object storage)
│   ├── RabbitMQ (message queue)
│   └── Redis (cache)
├── Application Services
│   ├── api-gateway (FastAPI, Python 3.12, UV)
│   ├── extraction (LangChain, Python 3.12, UV)
│   ├── embeddings (GenAI, Python 3.12, UV)
│   ├── ingestion (Selenium, Python 3.12, UV)
│   └── company-catalog (FastAPI, Python 3.12, UV)
├── Orchestration Layer
│   └── Airflow (Python 3.12, UV)
└── Frontend
    └── Vue.js application
```

## Components and Interfaces

### 1. Standardized Dockerfile Template

All services will follow this multi-stage pattern:

```dockerfile
# Stage 1: Builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    <system-deps> && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install runtime system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    <runtime-deps> && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY main.py ./  # if applicable

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose ports (if applicable)
EXPOSE <port>

# Health check (if applicable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD <health-check-command>

# Run command
CMD ["<command>"]
```

### 2. Service-Specific Configurations

#### API Gateway
- Base: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- Runtime deps: None
- Port: 8000
- Health check: `curl -f http://localhost:8000/health`
- Command: `uvicorn src.main:app --host 0.0.0.0 --port 8000`

#### Extraction Service
- Base: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- Runtime deps: `curl`
- Port: 8080 (health check)
- Health check: `curl -f http://localhost:8080/health`
- Command: `python main.py`

#### Embeddings Service
- Base: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- Build deps: `libxml2-dev libxslt-dev build-essential`
- Runtime deps: `libxml2 libxslt1.1`
- Command: `python src/worker.py`

#### Ingestion Service
- Base: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- Runtime deps: `aria2`
- Command: `python src/main.py`

#### Company Catalog Service
- Base: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- Runtime deps: None
- Command: `python src/main.py`

#### Airflow Service
- Base: `apache/airflow:2.8.1-python3.12`
- Special: Install UV in builder stage, use for Python deps
- Ports: 8080 (webserver), 8974 (scheduler health)

### 3. Python Version Files

Each service directory will contain:

```
.python-version
```

Content: `3.12`

### 4. pyproject.toml Standardization

All services will use:

```toml
[project]
name = "<service-name>"
version = "0.1.0"
description = "<description>"
requires-python = ">=3.12"
dependencies = [
    # ... dependencies
]

[dependency-groups]
dev = [
    # ... dev dependencies
]
```

### 5. Airflow DAG Structure

The Airflow DAG will be enhanced to:

1. **Use DockerOperator** for all service execution
2. **Accept parameters** for flexible pipeline execution
3. **Implement proper error handling** and retries
4. **Provide visibility** through logging and monitoring
5. **Support batch processing** for scalability

Key improvements:
- Remove Python callable functions that duplicate service logic
- Use environment variables for service configuration
- Implement proper task dependencies
- Add validation and verification steps
- Generate execution reports

### 6. Legacy Script Migration

Scripts to be removed or migrated:

| Script | Action | Airflow Equivalent |
|--------|--------|-------------------|
| `pipeline_orchestrator.py` | Remove | Main DAG handles orchestration |
| `publish_extraction_tasks.py` | Remove | Extraction task in DAG |
| `trigger_extraction.py` | Remove | Airflow API/UI trigger |
| `test_pipeline_e2e.py` | Keep | Integration test (not orchestration) |
| `cleanup_pipeline_data.py` | Migrate | New Airflow DAG for cleanup |
| `cleanup_sample_data.py` | Keep | Utility script |
| `verify_extraction_service.sh` | Keep | Health check utility |

## Data Models

### Airflow Variables

Airflow will use these variables (set via UI or environment):

```python
{
    "db_name": "esg_platform",
    "db_user": "postgres",
    "db_password": "<secret>",
    "minio_access_key": "<secret>",
    "minio_secret_key": "<secret>",
    "google_api_key": "<secret>"
}
```

### DAG Parameters

The main pipeline DAG will accept:

```python
{
    "companies": [],  # List of company symbols, empty = all
    "report_year": None,  # Specific year or None for latest
    "skip_company_sync": True,  # Skip company catalog sync
    "batch_size": 5  # Process N companies at a time
}
```

### Service Environment Variables

All services will receive configuration via environment variables:

```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=${POSTGRES_DB}
DB_USER=${POSTGRES_USER}
DB_PASSWORD=${POSTGRES_PASSWORD}

# Storage
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}

# Message Queue
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=${RABBITMQ_DEFAULT_USER}
RABBITMQ_PASS=${RABBITMQ_DEFAULT_PASS}

# API Keys
GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

## Error Handling

### Docker Build Errors

1. **UV sync failures**: Ensure uv.lock is committed and up-to-date
2. **System dependency errors**: Document required packages in Dockerfile comments
3. **Layer caching issues**: Order Dockerfile commands from least to most frequently changing

### Airflow Execution Errors

1. **Service failures**: Airflow will retry tasks based on retry configuration
2. **Docker connectivity**: Ensure Docker socket is mounted and accessible
3. **Network issues**: Use proper Docker network configuration
4. **Resource constraints**: Configure appropriate resource limits

### Migration Errors

1. **Version conflicts**: Update all services simultaneously
2. **Missing dependencies**: Run `uv sync` after updating pyproject.toml
3. **Docker build context**: Ensure all required files are in build context

## Testing Strategy

### Phase 1: Individual Service Testing

For each service:
1. Update .python-version to 3.12
2. Update pyproject.toml requires-python to >=3.12
3. Update Dockerfile to use multi-stage build with Python 3.12
4. Build Docker image locally
5. Run service in docker-compose
6. Verify functionality

### Phase 2: Integration Testing

1. Build all services with new Dockerfiles
2. Start infrastructure services (postgres, minio, rabbitmq, redis)
3. Start application services
4. Run integration tests from tests/ directory
5. Verify end-to-end functionality

### Phase 3: Airflow Testing

1. Update Airflow Dockerfile to Python 3.12
2. Build Airflow image
3. Start Airflow services
4. Trigger test DAG run
5. Verify all tasks execute successfully
6. Check logs and monitoring

### Phase 4: Legacy Script Removal

1. Verify Airflow DAG covers all orchestration use cases
2. Document migration path for any custom scripts
3. Remove deprecated scripts
4. Update documentation

### Test Checklist

- [ ] All services build successfully
- [ ] All services start without errors
- [ ] Database connections work
- [ ] MinIO storage operations work
- [ ] RabbitMQ message passing works
- [ ] Redis caching works
- [ ] API Gateway endpoints respond
- [ ] Extraction service processes documents
- [ ] Embeddings service generates vectors
- [ ] Ingestion service downloads PDFs
- [ ] Airflow DAG executes successfully
- [ ] Airflow UI is accessible
- [ ] Docker images are smaller than before
- [ ] Build times are acceptable
- [ ] No Python version warnings

## Implementation Approach

### Rollout Strategy

**Option 1: Service-by-Service (Recommended)**
- Update one service at a time
- Test thoroughly before moving to next
- Lower risk, easier to debug
- Longer overall timeline

**Option 2: Big Bang**
- Update all services simultaneously
- Faster overall completion
- Higher risk of issues
- Requires comprehensive testing

**Recommendation**: Use Option 1 (service-by-service) to minimize risk and ensure stability.

### Service Update Order

1. **company-catalog** (simplest, no complex dependencies)
2. **ingestion** (depends on company-catalog)
3. **embeddings** (depends on ingestion)
4. **extraction** (depends on embeddings)
5. **api-gateway** (depends on all data services)
6. **airflow** (orchestrates all services)
7. **db-init** (infrastructure component)

### Dependency Version Strategy

Maintain a "blessed" version list for shared dependencies:

```toml
# Shared dependencies - keep versions aligned
psycopg2-binary = ">=2.9.11"
pika = ">=1.3.2"
boto3 = ">=1.40.60"
pydantic = ">=2.12.3"
pydantic-settings = ">=2.11.0"
python-dotenv = ">=1.2.1"
```

### Build Optimization

1. **Layer caching**: Order Dockerfile commands appropriately
2. **Multi-stage builds**: Separate build and runtime dependencies
3. **Minimal base images**: Use slim variants
4. **Dependency locking**: Use uv.lock for reproducible builds
5. **Build arguments**: Parameterize where appropriate

### Documentation Updates

Update these files:
- `README.md` - Main project documentation
- `services/*/README.md` - Service-specific documentation
- `infra/README.md` - Infrastructure documentation
- `AIRFLOW_QUICKSTART.md` - Airflow usage guide
- Create `MIGRATION_GUIDE.md` - Document the changes

## Monitoring and Observability

### Build Metrics

Track:
- Docker image sizes (before/after)
- Build times (before/after)
- Layer cache hit rates

### Runtime Metrics

Monitor:
- Service startup times
- Memory usage
- CPU usage
- Error rates

### Airflow Metrics

Track:
- DAG run duration
- Task success/failure rates
- Retry counts
- Queue depths

## Rollback Plan

If issues arise:

1. **Individual service rollback**: Revert Dockerfile and rebuild
2. **Full rollback**: Use git to revert all changes
3. **Partial rollback**: Keep Python 3.12 but revert other changes
4. **Emergency**: Use previous Docker images (tag them before migration)

## Security Considerations

1. **Base images**: Use official images from trusted sources
2. **Secrets management**: Never hardcode secrets in Dockerfiles
3. **User permissions**: Run containers as non-root where possible
4. **Network isolation**: Use Docker networks appropriately
5. **Dependency scanning**: Regularly update dependencies for security patches

## Performance Considerations

### Expected Improvements

1. **Docker image sizes**: 20-40% reduction from multi-stage builds
2. **Build times**: 10-30% improvement from UV speed
3. **Dependency resolution**: Faster with UV vs pip
4. **Layer caching**: Better with optimized Dockerfile order

### Potential Concerns

1. **Initial build time**: First build will be slower (no cache)
2. **UV learning curve**: Team needs to learn UV commands
3. **Migration downtime**: Services need to be rebuilt and restarted

## Future Enhancements

1. **BuildKit**: Use Docker BuildKit for parallel builds
2. **Registry caching**: Use Docker registry for layer caching
3. **Distroless images**: Consider distroless base images for even smaller sizes
4. **Kubernetes**: Prepare for potential K8s deployment
5. **CI/CD integration**: Automate builds and deployments
