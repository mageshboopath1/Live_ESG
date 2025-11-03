# ESG Intelligence Platform - Infrastructure

This directory contains the Docker Compose configuration and infrastructure setup for the ESG Intelligence Platform.

## Overview

The platform consists of the following services:

### Core Services
- **PostgreSQL** - Database with pgvector extension for embeddings
- **MinIO** - S3-compatible object storage for PDF documents
- **RabbitMQ** - Message queue for asynchronous task processing
- **Redis** - Cache layer for API responses

### Application Services
- **Company Catalog** - Syncs NIFTY 50 company data
- **Ingestion** - Downloads and processes PDF reports
- **Embeddings** - Generates vector embeddings using Google GenAI
- **Extraction** - Extracts BRSR indicators using LangChain
- **API Gateway** - FastAPI REST API for frontend
- **Frontend** - Vue 3 web application

### Management Tools
- **PgAdmin** - Database management interface

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available for Docker
- Google API key for GenAI services

### Initial Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your configuration:
   - Set your Google API key (`GOOGLE_API_KEY`)
   - Update passwords for production use
   - Configure other settings as needed

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Check service health**:
   ```bash
   docker-compose ps
   ```

5. **View logs**:
   ```bash
   docker-compose logs -f
   ```

## Development Mode

For development with hot-reloading and volume mounts:

```bash
# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or run in background
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### Development Features

- **Hot-reload**: Code changes are automatically reflected
- **Volume mounts**: Source code is mounted from host
- **Debug logging**: All services run with DEBUG log level
- **Exposed ports**: All service ports are accessible from host

## Service Access

### Web Interfaces

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PgAdmin**: http://localhost:8080
- **MinIO Console**: http://localhost:9001
- **RabbitMQ Management**: http://localhost:15672

### Default Credentials

**PgAdmin**:
- Email: `admin@admin.com`
- Password: `admin`

**MinIO Console**:
- Username: `esg_minio`
- Password: `esg_secret`

**RabbitMQ Management**:
- Username: `esg_rabbitmq`
- Password: `esg_secret`

**PostgreSQL**:
- Host: `localhost:5432`
- Database: `moz`
- Username: `drfitz`
- Password: `h4i1hydr4`

> ⚠️ **Security Warning**: Change all default passwords before deploying to production!

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart api-gateway

# View service logs
docker-compose logs -f extraction

# View logs for specific service (last 100 lines)
docker-compose logs --tail=100 embeddings

# Rebuild a service
docker-compose build extraction

# Rebuild and restart a service
docker-compose up -d --build extraction
```

### Database Operations

```bash
# Access PostgreSQL CLI
docker-compose exec postgres psql -U drfitz -d moz

# Run SQL file
docker-compose exec postgres psql -U drfitz -d moz -f /docker-entrypoint-initdb.d/migration.sql

# Backup database
docker-compose exec postgres pg_dump -U drfitz moz > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres psql -U drfitz -d moz < backup.sql
```

### Service Shell Access

```bash
# Access service shell
docker-compose exec extraction /bin/bash

# Run Python commands
docker-compose exec extraction uv run python -c "import sys; print(sys.version)"

# Check installed packages
docker-compose exec extraction uv pip list
```

### Monitoring

```bash
# View resource usage
docker stats

# View service health
docker-compose ps

# Check specific service health
docker-compose exec api-gateway curl -f http://localhost:8000/health
```

## Troubleshooting

### Services Won't Start

1. **Check Docker resources**:
   - Ensure Docker has enough memory (8GB+ recommended)
   - Check disk space

2. **Check port conflicts**:
   ```bash
   # Check if ports are already in use
   lsof -i :5432  # PostgreSQL
   lsof -i :8000  # API Gateway
   lsof -i :3000  # Frontend
   ```

3. **View service logs**:
   ```bash
   docker-compose logs postgres
   docker-compose logs api-gateway
   ```

### Database Connection Issues

1. **Wait for health checks**:
   ```bash
   docker-compose ps
   # Ensure postgres shows "healthy" status
   ```

2. **Check database logs**:
   ```bash
   docker-compose logs postgres
   ```

3. **Test connection**:
   ```bash
   docker-compose exec postgres pg_isready -U drfitz
   ```

### Service Crashes or Restarts

1. **Check logs for errors**:
   ```bash
   docker-compose logs --tail=100 <service-name>
   ```

2. **Check resource usage**:
   ```bash
   docker stats
   ```

3. **Restart service**:
   ```bash
   docker-compose restart <service-name>
   ```

### Hot-Reload Not Working

1. **Ensure using dev compose file**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. **Check volume mounts**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml config
   ```

3. **Rebuild service**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build <service-name>
   ```

## Data Persistence

All data is stored in Docker volumes:

- `postgres_data` - Database data
- `pgadmin_data` - PgAdmin configuration
- `minio_data` - Object storage data
- `rabbitmq_data` - Message queue data
- `redis_data` - Cache data

### Backup Volumes

```bash
# Backup all volumes
docker run --rm -v esg-platform_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v esg-platform_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes (⚠️ deletes all data)
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all
```

## Network Architecture

The platform uses two Docker networks:

- **backend** - Internal network for backend services
- **frontend** - Network for frontend and API gateway

This isolation ensures:
- Frontend can only access API Gateway
- Backend services are not directly accessible from outside
- Services can communicate using service names as hostnames

## Health Checks

All services implement health checks:

- **PostgreSQL**: `pg_isready` command
- **MinIO**: HTTP health endpoint
- **RabbitMQ**: `rabbitmq-diagnostics ping`
- **Redis**: `redis-cli ping`
- **API Gateway**: HTTP `/health` endpoint
- **Extraction**: HTTP `/health` endpoint
- **Frontend**: HTTP root endpoint

Services wait for dependencies to be healthy before starting.

## Performance Tuning

### PostgreSQL

Edit `docker-compose.yml` to add performance settings:

```yaml
postgres:
  command:
    - postgres
    - -c
    - shared_buffers=256MB
    - -c
    - max_connections=200
    - -c
    - work_mem=16MB
```

### Redis

Adjust memory limits:

```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## Production Deployment

For production deployment:

1. **Update all passwords** in `.env`
2. **Generate strong SECRET_KEY**:
   ```bash
   openssl rand -hex 32
   ```
3. **Enable SSL/TLS** for all services
4. **Configure firewall rules**
5. **Set up monitoring and alerting**
6. **Configure backup automation**
7. **Use secrets management** (AWS Secrets Manager, Vault)
8. **Consider Kubernetes** for orchestration instead of Docker Compose

## Testing

### Quick Health Check

Run a quick health check of all services:

```bash
./quick-health-check.sh
```

This checks:
- ✓ All services are running
- ✓ Health checks are passing
- ✓ Endpoints are accessible

### Comprehensive Testing

Run the full test suite:

```bash
./test-docker-setup.sh
```

This performs comprehensive testing including service startup, health checks, communication, environment variables, volume persistence, and network connectivity.

### Using Makefile

```bash
make test          # Run all tests
make test-quick    # Quick health check
```

For detailed testing documentation, see [TESTING.md](TESTING.md).

## Support

For issues or questions:
- Check service logs: `docker-compose logs <service-name>`
- Review environment variables in `.env`
- Ensure all prerequisites are met
- Check Docker resources and disk space
- Run testing scripts to diagnose issues
- Consult [TESTING.md](TESTING.md) for troubleshooting

## License

[Your License Here]
