# Shared Dependency Version Reference

This document maintains the "blessed" versions of shared dependencies across all services in the ESG Intelligence Platform. Keeping these versions aligned reduces conflicts, simplifies updates, and ensures consistent behavior.

## Version Alignment Strategy

### Principles

1. **Consistency First**: Use the same major.minor version across all services
2. **Security Updates**: Promptly update for security patches
3. **Compatibility Testing**: Test updates in one service before rolling out to all
4. **Lock Files**: Always commit `uv.lock` files for reproducible builds
5. **Gradual Updates**: Update one service at a time, test thoroughly

### Update Process

1. Identify the dependency to update
2. Check compatibility with Python 3.12
3. Update in one service first (preferably company-catalog as it's simplest)
4. Run tests and verify functionality
5. Update remaining services
6. Update this document with new version
7. Commit all changes together

## Core Shared Dependencies

These dependencies are used across multiple services and should maintain version alignment.

### Database Clients

#### psycopg2-binary
- **Current Version**: `>=2.9.11`
- **Used By**: api-gateway, extraction, embeddings, ingestion
- **Purpose**: PostgreSQL database adapter
- **Notes**: 
  - Binary version includes compiled C extensions
  - Requires `libpq5` at runtime in Docker
  - Alternative: `psycopg[binary]>=3.2.10` (used by company-catalog, consider migrating)

#### psycopg (v3)
- **Current Version**: `>=3.2.10`
- **Used By**: company-catalog
- **Purpose**: Modern PostgreSQL adapter (psycopg3)
- **Notes**:
  - Newer API than psycopg2
  - Better async support
  - Consider migrating other services to psycopg3 in future

### Message Queue

#### pika
- **Current Version**: `>=1.3.2`
- **Used By**: extraction, embeddings, ingestion
- **Purpose**: RabbitMQ client library
- **Notes**:
  - Stable and well-maintained
  - Used for async task distribution
  - Critical for pipeline orchestration

### Cloud Storage

#### boto3
- **Current Version**: `>=1.40.43` (align to `>=1.40.60`)
- **Used By**: api-gateway, embeddings, ingestion
- **Purpose**: AWS SDK (used for MinIO S3-compatible storage)
- **Notes**:
  - Version variance: api-gateway uses 1.40.60, others use 1.40.43
  - **Action Required**: Align all services to `>=1.40.60`
  - Works with MinIO S3-compatible API

#### minio
- **Current Version**: `>=7.2.18`
- **Used By**: ingestion
- **Purpose**: Native MinIO client
- **Notes**:
  - Alternative to boto3 for MinIO
  - More MinIO-specific features
  - Consider standardizing on either boto3 or minio

### Data Validation

#### pydantic
- **Current Version**: `>=2.11.9` (align to `>=2.12.3`)
- **Used By**: All services
- **Purpose**: Data validation and settings management
- **Notes**:
  - Version variance: Some use 2.11.9, others use 2.12.3
  - **Action Required**: Align all services to `>=2.12.3`
  - Pydantic v2 has breaking changes from v1

#### pydantic-settings
- **Current Version**: `>=2.11.0`
- **Used By**: api-gateway, extraction
- **Purpose**: Settings management with Pydantic
- **Notes**:
  - Separated from main pydantic package in v2
  - Used for environment variable configuration

### Configuration

#### python-dotenv
- **Current Version**: `>=1.2.1`
- **Used By**: api-gateway, extraction
- **Purpose**: Load environment variables from .env files
- **Notes**:
  - Essential for local development
  - Not needed in production with proper env var injection

### Web Frameworks

#### fastapi
- **Current Version**: `>=0.116.1` (align to `>=0.120.0`)
- **Used By**: api-gateway, company-catalog
- **Purpose**: Modern async web framework
- **Notes**:
  - Version variance: api-gateway uses 0.120.0, company-catalog uses 0.116.1
  - **Action Required**: Align to `>=0.120.0`
  - Requires uvicorn for ASGI server

#### uvicorn
- **Current Version**: `>=0.35.0` (align to `>=0.38.0`)
- **Used By**: api-gateway, company-catalog
- **Purpose**: ASGI server for FastAPI
- **Notes**:
  - Version variance: api-gateway uses 0.38.0, company-catalog uses 0.35.0
  - **Action Required**: Align to `>=0.38.0`
  - Use `uvicorn[standard]` for full features

### Database ORM

#### sqlalchemy
- **Current Version**: `>=2.0.43` (align to `>=2.0.44`)
- **Used By**: api-gateway, company-catalog
- **Purpose**: SQL toolkit and ORM
- **Notes**:
  - Version variance: api-gateway uses 2.0.44, company-catalog uses 2.0.43
  - **Action Required**: Align to `>=2.0.44`
  - SQLAlchemy 2.0 has breaking changes from 1.x

## Service-Specific Dependencies

These dependencies are unique to specific services but documented here for reference.

### AI/ML Libraries

#### google-genai
- **Current Version**: `>=1.46.0` (align to `>=1.47.0`)
- **Used By**: extraction, embeddings
- **Purpose**: Google Generative AI SDK
- **Notes**:
  - Version variance: extraction uses 1.47.0, embeddings uses 1.46.0
  - **Action Required**: Align to `>=1.47.0`

#### langchain
- **Current Version**: `>=1.0.2`
- **Used By**: extraction
- **Purpose**: LLM application framework
- **Notes**: Core langchain library

#### langchain-google-genai
- **Current Version**: `>=3.0.0`
- **Used By**: extraction, embeddings
- **Purpose**: Google AI integration for LangChain
- **Notes**: Provides Gemini model support

#### langchain-text-splitters
- **Current Version**: `>=1.0.0`
- **Used By**: embeddings
- **Purpose**: Text chunking utilities
- **Notes**: Used for document processing

### PDF Processing

#### pdfplumber
- **Current Version**: `>=0.11.7`
- **Used By**: embeddings
- **Purpose**: PDF text extraction
- **Notes**: Good for structured PDF data

#### pymupdf
- **Current Version**: `>=1.26.5`
- **Used By**: embeddings
- **Purpose**: PDF rendering and extraction
- **Notes**: Also known as fitz, fast C-based library

### Web Scraping

#### selenium
- **Current Version**: `>=4.36.0`
- **Used By**: ingestion
- **Purpose**: Browser automation
- **Notes**: Used for downloading reports from websites

#### selenium-stealth
- **Current Version**: `>=1.0.6`
- **Used By**: ingestion
- **Purpose**: Avoid bot detection
- **Notes**: Makes Selenium less detectable

#### webdriver-manager
- **Current Version**: `>=4.0.2`
- **Used By**: ingestion
- **Purpose**: Automatic webdriver management
- **Notes**: Handles ChromeDriver installation

### Caching

#### redis
- **Current Version**: `>=7.0.1`
- **Used By**: api-gateway
- **Purpose**: Redis client for caching
- **Notes**: Used for API response caching

### Authentication

#### python-jose[cryptography]
- **Current Version**: `>=3.5.0`
- **Used By**: api-gateway
- **Purpose**: JWT token handling
- **Notes**: Includes cryptography extras for security

#### passlib
- **Current Version**: `>=1.7.4`
- **Used By**: api-gateway
- **Purpose**: Password hashing
- **Notes**: Used for secure password storage

### Utilities

#### requests
- **Current Version**: `>=2.32.5`
- **Used By**: ingestion, company-catalog
- **Purpose**: HTTP client library
- **Notes**: Standard Python HTTP library

#### tqdm
- **Current Version**: `>=4.67.1`
- **Used By**: embeddings, ingestion
- **Purpose**: Progress bars
- **Notes**: Useful for long-running operations

#### pandas
- **Current Version**: `>=2.3.2`
- **Used By**: company-catalog
- **Purpose**: Data manipulation
- **Notes**: Used for CSV/data processing

## Version Alignment Action Items

### High Priority (Breaking Changes or Security)

1. **Align boto3 versions**
   - Update embeddings and ingestion from `>=1.40.43` to `>=1.40.60`
   - Test MinIO connectivity after update

2. **Align pydantic versions**
   - Update company-catalog from `>=2.11.9` to `>=2.12.3`
   - Test data validation and settings

3. **Align FastAPI versions**
   - Update company-catalog from `>=0.116.1` to `>=0.120.0`
   - Test API endpoints

### Medium Priority (Minor Version Differences)

4. **Align uvicorn versions**
   - Update company-catalog from `>=0.35.0` to `>=0.38.0`
   - Test server startup

5. **Align SQLAlchemy versions**
   - Update company-catalog from `>=2.0.43` to `>=2.0.44`
   - Test database queries

6. **Align google-genai versions**
   - Update embeddings from `>=1.46.0` to `>=1.47.0`
   - Test embedding generation

### Low Priority (Patch Versions)

7. **Consider psycopg2 to psycopg3 migration**
   - Evaluate benefits of migrating to psycopg3
   - Plan migration strategy if beneficial
   - Update all services together

## Testing Strategy for Updates

When updating shared dependencies:

1. **Update pyproject.toml**: Change version constraint
2. **Regenerate lock file**: Run `uv sync` to update `uv.lock`
3. **Local testing**: Test service locally with new version
4. **Unit tests**: Run service-specific unit tests
5. **Integration tests**: Run integration tests with other services
6. **Docker build**: Build Docker image and test in container
7. **Smoke tests**: Verify basic functionality
8. **Commit**: Commit both `pyproject.toml` and `uv.lock`

## Monitoring for Updates

### Security Updates
- Monitor GitHub security advisories
- Subscribe to security mailing lists for critical dependencies
- Use tools like `pip-audit` or `safety` to scan for vulnerabilities

### Version Tracking
- Check for updates monthly
- Review changelogs before updating
- Test in development before production

### Deprecation Warnings
- Monitor logs for deprecation warnings
- Plan migrations before breaking changes
- Update documentation when APIs change

## Notes

- This document should be updated whenever shared dependencies are modified
- Version constraints use `>=` to allow patch updates while maintaining compatibility
- Lock files (`uv.lock`) ensure exact reproducible builds
- Always test updates thoroughly before deploying to production
- Consider creating a dependency update schedule (e.g., monthly review)

## Last Updated

- **Date**: 2025-11-01
- **Updated By**: Project Modernization Initiative
- **Next Review**: 2025-12-01
