# ESG Intelligence Platform - Documentation Index

This document provides a comprehensive guide to all documentation in the repository.

## Quick Start

1. [Main README](README.md) - Project overview and quick start
2. [Infrastructure Setup](infra/README.md) - Docker Compose setup
3. [Testing Guide](tests/README.md) - Integration tests

## Core Documentation

### Project Overview
- **[README.md](README.md)** - Main project documentation
  - Architecture overview
  - Quick start guide
  - Technology stack
  - Common commands

### Infrastructure

- **[infra/README.md](infra/README.md)** - Infrastructure setup and management
  - Docker Compose configuration
  - Service management
  - Database operations
  - Troubleshooting
  
- **[infra/TESTING.md](infra/TESTING.md)** - Infrastructure testing
  - Testing requirements
  - Manual testing procedures
  - CI/CD integration

- **[infra/QUICK_REFERENCE.md](infra/QUICK_REFERENCE.md)** - Quick command reference
  - Common commands
  - Service URLs
  - Troubleshooting tips

### Testing

- **[tests/README.md](tests/README.md)** - Integration testing
  - Test structure
  - Running tests
  - Health checks
  - Test categories

### Scripts

- **[scripts/README.md](scripts/README.md)** - Pipeline scripts overview
  - E2E testing
  - Data cleanup
  - Pipeline orchestration

- **[scripts/E2E_TEST_README.md](scripts/E2E_TEST_README.md)** - End-to-end testing
  - Test scenarios
  - Usage examples
  - Test reports
  - Troubleshooting

- **[scripts/CLEANUP_README.md](scripts/CLEANUP_README.md)** - Data cleanup
  - Cleanup operations
  - Safety features
  - Usage examples

## Service Documentation

### API Gateway
- **[services/api-gateway/README.md](services/api-gateway/README.md)** - REST API documentation
  - Endpoints
  - Authentication
  - Error handling

### Frontend
- **[services/frontend/README.md](services/frontend/README.md)** - Frontend application
  - Development setup
  - Build process
  - Component structure

### Extraction Service
- **[services/extraction/README.md](services/extraction/README.md)** - BRSR extraction
  - Extraction logic
  - LangChain integration
  - Configuration

### Other Services
- Company Catalog: [services/company-catalog/README.md](services/company-catalog/README.md)
- Ingestion: [services/ingestion/README.md](services/ingestion/README.md)
- Embeddings: [services/embeddings/README.md](services/embeddings/README.md)

## Specifications

Located in `.kiro/specs/`:
- Feature specifications
- Design documents
- Requirements
- Implementation tasks

## Configuration Files

### Environment Configuration
- `.env.example` - Root environment template
- `infra/.env` - Infrastructure configuration
- `scripts/.env.example` - Scripts configuration
- Service-specific `.env.example` files in each service directory

### Docker Configuration
- `docker-compose.yml` - Production configuration
- `docker-compose.dev.yml` - Development overrides
- Service Dockerfiles in each service directory

### Build Configuration
- `pyproject.toml` - Python project configuration (scripts, tests)
- `package.json` - Node.js configuration (frontend)
- `Makefile` - Build automation (infra)

## Common Workflows

### Initial Setup
1. Read [README.md](README.md) for overview
2. Follow [infra/README.md](infra/README.md) for setup
3. Run tests per [tests/README.md](tests/README.md)

### Development
1. Start services: `cd infra && make dev`
2. Run tests: `cd tests && ./run_integration_tests.sh`
3. Check health: `cd tests && ./health_check.sh`

### Testing
1. Infrastructure: `cd infra && make test`
2. Integration: `cd tests && ./run_integration_tests.sh`
3. E2E Pipeline: `cd scripts && python test_pipeline_e2e.py`

### Troubleshooting
1. Check [infra/QUICK_REFERENCE.md](infra/QUICK_REFERENCE.md)
2. Review service logs: `docker-compose logs <service>`
3. Run health checks: `./health_check.sh`

## Documentation by Role

### Developers
- [README.md](README.md) - Project overview
- [infra/README.md](infra/README.md) - Local development setup
- [tests/README.md](tests/README.md) - Running tests
- Service-specific READMEs

### DevOps/SRE
- [infra/README.md](infra/README.md) - Infrastructure management
- [infra/TESTING.md](infra/TESTING.md) - Testing procedures
- [infra/QUICK_REFERENCE.md](infra/QUICK_REFERENCE.md) - Command reference

### QA/Testers
- [tests/README.md](tests/README.md) - Integration testing
- [scripts/E2E_TEST_README.md](scripts/E2E_TEST_README.md) - E2E testing
- [infra/TESTING.md](infra/TESTING.md) - Infrastructure testing

### Project Managers
- [README.md](README.md) - Project overview
- `.kiro/specs/` - Feature specifications
- Test reports in `scripts/test_reports/`

## Getting Help

1. **Quick Reference**: [infra/QUICK_REFERENCE.md](infra/QUICK_REFERENCE.md)
2. **Troubleshooting**: Check service-specific README files
3. **Health Check**: Run `cd tests && ./health_check.sh`
4. **Logs**: `docker-compose logs <service-name>`

## Contributing

When adding new documentation:
1. Place it in the appropriate directory
2. Update this index
3. Link from related documents
4. Follow existing formatting conventions

## Documentation Standards

- Use Markdown format
- Include code examples
- Provide troubleshooting sections
- Keep examples up-to-date
- Link to related documentation
