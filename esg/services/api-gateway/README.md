# API Gateway Service

FastAPI-based API Gateway for the ESG Intelligence Platform. Provides REST API endpoints for accessing company data, extracted indicators, ESG scores, and source citations.

## Features

- RESTful API with FastAPI
- CORS middleware for frontend integration
- JWT-based authentication
- Database connection pooling with SQLAlchemy
- Redis caching layer for improved performance
- Health check endpoints
- OpenAPI/Swagger documentation

## Technology Stack

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **UV**: Fast Python package installer and resolver
- **Docker**: Containerization

## Development Setup

### Prerequisites

- Python 3.12+
- UV package manager
- PostgreSQL database (or use Docker Compose)
- Redis (optional, for caching - or use Docker Compose)

### Installation

1. Install dependencies using UV:

```bash
uv sync
```

2. Create a `.env` file from the example:

```bash
cp .env.example .env
```

3. Edit `.env` with your configuration.

### Running Locally

Run the service using UV:

```bash
uv run python -m src.main
```

Or use uvicorn directly:

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker Deployment

### Build the Docker image:

```bash
docker build -t api-gateway .
```

### Run the container:

```bash
docker run -p 8000:8000 --env-file .env api-gateway
```

### Using Docker Compose:

The service is included in the main `docker-compose.yml` at the project root.

```bash
docker-compose up api-gateway
```

## API Endpoints

### Health & Status

- `GET /` - Root endpoint with service info
- `GET /health` - Health check endpoint

### Companies (To be implemented)

- `GET /api/companies` - List all companies
- `GET /api/companies/{company_id}` - Get company details
- `GET /api/companies/search?q={query}` - Search companies

### Reports (To be implemented)

- `GET /api/companies/{company_id}/reports` - List company reports
- `GET /api/reports/{object_key}` - Get report details
- `POST /api/reports/trigger-processing` - Trigger report processing

### Indicators (To be implemented)

- `GET /api/companies/{company_id}/indicators?year={year}` - List indicators
- `GET /api/indicators/{indicator_id}` - Get indicator details
- `GET /api/indicators/compare` - Compare indicators across companies

### Scores (To be implemented)

- `GET /api/companies/{company_id}/scores?year={year}` - Get ESG scores
- `GET /api/scores/breakdown/{company_id}/{year}` - Get score breakdown

### Citations (To be implemented)

- `GET /api/citations/{extracted_indicator_id}` - Get citations
- `GET /api/documents/{object_key}/page/{page_number}` - Get PDF page

### Cache Management

- `GET /api/cache/status` - Get cache status
- `POST /api/cache/invalidate/company/{company_id}` - Invalidate company cache
- `POST /api/cache/invalidate/indicators` - Invalidate indicator definitions cache
- `POST /api/cache/invalidate/scores/{company_id}` - Invalidate scores cache
- `POST /api/cache/clear` - Clear all cache entries

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

Key settings:

- `POSTGRES_*`: Database connection settings
- `CORS_ORIGINS`: Allowed origins for CORS
- `SECRET_KEY`: JWT secret key (change in production!)
- `MINIO_*`: Object storage settings
- `REDIS_*`: Redis cache settings
- `CACHE_TTL_*`: Cache time-to-live settings

See [CACHING.md](./CACHING.md) for detailed caching documentation.

## Development

### Adding Dependencies

Use UV to add new dependencies:

```bash
uv add <package-name>
```

For development dependencies:

```bash
uv add --dev <package-name>
```

### Code Structure

```
services/api-gateway/
├── src/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   └── config.py        # Configuration management
├── Dockerfile           # Multi-stage Docker build
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock             # Locked dependencies
└── README.md           # This file
```

## Caching

The API Gateway includes a Redis caching layer for improved performance:

- **Company data**: Cached for 1 hour
- **BRSR indicator definitions**: Cached for 24 hours
- **ESG scores**: Cached for 1 hour

The caching layer is resilient and the service continues to work if Redis is unavailable.

For detailed information, see [CACHING.md](./CACHING.md).

## License

Part of the ESG Intelligence Platform project.
