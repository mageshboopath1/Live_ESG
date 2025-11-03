# ESG Intelligence Platform

An automated system for ingesting, processing, and analyzing company sustainability disclosures (BRSR reports, annual reports) to extract standardized ESG indicators, generate insights, and support scoring and benchmarking capabilities.

## Overview

The ESG Intelligence Platform uses AI-powered extraction with Google GenAI and LangChain to automatically identify and extract BRSR Core indicators from company reports, providing transparent, traceable ESG analysis with full source citations.

### Key Features

- **Automated Document Ingestion**: Fetches and processes PDF reports from company sources
- **AI-Powered Extraction**: Uses LangChain and Google GenAI to extract BRSR Core indicators
- **Semantic Search**: PostgreSQL with pgvector for intelligent document retrieval
- **Transparent Analysis**: Every data point traceable to source with PDF citations
- **Interactive Dashboard**: Vue 3 frontend with score breakdowns and source navigation
- **Scalable Architecture**: Microservices with asynchronous processing via RabbitMQ

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                         │
│                    Company Dashboards & Visualizations           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│              Authentication, Routing, Aggregation                │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│   Company    │    │    Ingestion     │    │  Extraction  │
│   Catalog    │    │    Service       │    │   Service    │
└──────────────┘    └──────────────────┘    └──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Embeddings     │
                    │    Service       │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL + pgvector │ RabbitMQ │ MinIO │ Redis              │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available for Docker
- Google API key for GenAI services ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd esg-intelligence-platform
   ```

2. **Configure environment**:
   ```bash
   cp .env.example infra/.env
   # Edit infra/.env with your Google API key and other settings
   ```

3. **Start all services**:
   ```bash
   cd infra
   make start
   # Or: ./start.sh start
   # Or: docker-compose up -d
   ```

4. **Access the platform**:
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - PgAdmin: http://localhost:8080
   - MinIO Console: http://localhost:9001
   - RabbitMQ Management: http://localhost:15672

### Development Mode

For development with hot-reloading:

```bash
cd infra
make dev
# Or: ./start.sh dev
# Or: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Services

### Core Services

- **PostgreSQL** - Database with pgvector extension for embeddings
- **MinIO** - S3-compatible object storage for PDF documents
- **RabbitMQ** - Message queue for asynchronous task processing
- **Redis** - Cache layer for API responses

### Application Services

- **Company Catalog** - Syncs NIFTY 50 company data from NSE
- **Ingestion** - Downloads and processes PDF reports
- **Embeddings** - Generates vector embeddings using Google GenAI
- **Extraction** - Extracts BRSR indicators using LangChain
- **API Gateway** - FastAPI REST API for frontend
- **Frontend** - Vue 3 web application with TypeScript

## Technology Stack

### Backend
- **Python 3.11+** with UV for dependency management
- **FastAPI** for REST API
- **LangChain** for LLM orchestration
- **Google GenAI** (Gemini) for embeddings and extraction
- **PostgreSQL** with pgvector for vector search
- **SQLAlchemy** for ORM
- **Pydantic** for data validation

### Frontend
- **Vue 3** with Composition API
- **TypeScript** for type safety
- **Bun** for package management and building
- **Vite** for development and bundling
- **Pinia** for state management
- **Tailwind CSS** for styling

### Infrastructure
- **Docker** for containerization
- **Docker Compose** for orchestration
- **RabbitMQ** for message queuing
- **Redis** for caching
- **MinIO** for object storage

## Common Commands

### Using Make (Recommended)

```bash
cd infra

# Start services
make start          # Production mode
make dev            # Development mode with hot-reload

# View logs
make logs           # All services
make logs-api-gateway  # Specific service

# Service management
make restart        # Restart all
make restart-extraction  # Restart specific service
make rebuild-frontend    # Rebuild specific service

# Status and monitoring
make status         # Show service status
make health         # Check health

# Database operations
make db-shell       # Open PostgreSQL shell
make db-backup      # Backup database
make db-restore     # Restore from backup

# Cleanup
make clean          # Remove containers
make clean-all      # Remove containers and volumes

# Open web interfaces
make open-frontend
make open-api
make open-pgadmin
```

### Using Docker Compose Directly

```bash
cd infra

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f api-gateway

# Stop services
docker-compose down

# Rebuild service
docker-compose build extraction
docker-compose up -d extraction
```

## Development

### Project Structure

```
esg-intelligence-platform/
├── infra/                      # Infrastructure configuration
│   ├── docker-compose.yml      # Production compose file
│   ├── docker-compose.dev.yml  # Development compose file
│   ├── db-init/                # Database initialization scripts
│   ├── Makefile                # Convenient commands
│   └── start.sh                # Start script
├── services/
│   ├── api-gateway/            # FastAPI REST API
│   ├── company-catalog/        # Company data sync service
│   ├── embeddings/             # Vector embedding generation
│   ├── extraction/             # BRSR indicator extraction
│   ├── frontend/               # Vue 3 web application
│   └── ingestion/              # Document ingestion service
├── .kiro/specs/                # Feature specifications
└── .env.example                # Environment template
```

### Adding a New Service

1. Create service directory in `services/`
2. Add Dockerfile with UV for Python or Bun for Node.js
3. Add service to `docker-compose.yml`
4. Configure environment variables in `.env`
5. Add health check endpoint
6. Update documentation

### Working on Python Services

```bash
cd services/<service-name>

# Install dependencies
uv sync

# Run locally (connects to Docker services)
uv run python main.py

# Run tests
uv run pytest

# Add dependency
uv add <package-name>
```

### Working on Frontend

```bash
cd services/frontend

# Install dependencies
bun install

# Run dev server
bun run dev

# Run tests
bun test

# Build for production
bun run build
```

## Configuration

All configuration is managed through environment variables in `infra/.env`. See `.env.example` for all available options.

### Key Configuration

- **GOOGLE_API_KEY**: Required for embeddings and extraction
- **POSTGRES_***: Database connection settings
- **MINIO_***: Object storage settings
- **RABBITMQ_***: Message queue settings
- **SECRET_KEY**: JWT signing key (generate with `openssl rand -hex 32`)

## Monitoring

### Service Health

```bash
# Check all services
make status

# Check specific service health
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8082/health  # Extraction Service
```

### Logs

```bash
# View all logs
make logs

# View specific service
make logs-extraction

# View last 100 lines
docker-compose logs --tail=100 embeddings
```

### Resource Usage

```bash
# View resource usage
docker stats

# Or using make
make status
```

## Troubleshooting

### Services Won't Start

1. Check Docker resources (8GB+ RAM recommended)
2. Check port conflicts: `lsof -i :5432` (PostgreSQL), `lsof -i :8000` (API)
3. View logs: `make logs`

### Database Connection Issues

1. Wait for health checks: `make status`
2. Check logs: `make logs-postgres`
3. Test connection: `make db-shell`

### Hot-Reload Not Working

1. Ensure using dev mode: `make dev`
2. Check volume mounts: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml config`
3. Rebuild service: `make rebuild-<service>`

## Production Deployment

For production deployment:

1. **Update all passwords** in `.env`
2. **Generate strong SECRET_KEY**: `openssl rand -hex 32`
3. **Enable SSL/TLS** for all services
4. **Configure firewall rules**
5. **Set up monitoring and alerting**
6. **Configure backup automation**
7. **Use secrets management** (AWS Secrets Manager, Vault)
8. **Consider Kubernetes** for orchestration

See `infra/README.md` for detailed production deployment guide.

## Documentation

For a complete documentation index, see [DOCUMENTATION.md](DOCUMENTATION.md).

### Quick Links
- [Infrastructure Setup](infra/README.md) - Docker Compose and service management
- [Testing Guide](tests/README.md) - Integration tests and health checks
- [Scripts Documentation](scripts/README.md) - Pipeline testing and orchestration
- [Quick Reference](infra/QUICK_REFERENCE.md) - Common commands and URLs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions:
- Check service logs: `make logs`
- Review documentation in `docs/`
- Open an issue on GitHub

## Acknowledgments

- Google GenAI for embeddings and extraction
- LangChain for LLM orchestration
- pgvector for vector similarity search
- BRSR Core framework for ESG indicators
