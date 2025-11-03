# Docker Compose Quick Reference

## Quick Start

```bash
cd infra
cp .env.example .env
# Edit .env with your values
docker-compose up -d
./quick-health-check.sh
```

## Testing Commands

| Command | Description | Duration |
|---------|-------------|----------|
| `./quick-health-check.sh` | Quick health check | ~5 sec |
| `./test-docker-setup.sh` | Comprehensive tests | ~3-5 min |
| `make test-quick` | Quick health check via Makefile | ~5 sec |
| `make test` | Comprehensive tests via Makefile | ~3-5 min |
| `make test-services` | Test service communication | ~10 sec |
| `make test-persistence` | Test volume persistence | ~30 sec |
| `make test-env` | Test environment variables | ~5 sec |

## Service Management

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start all services |
| `docker-compose down` | Stop all services |
| `docker-compose restart` | Restart all services |
| `docker-compose ps` | Show service status |
| `docker-compose logs -f` | View all logs |
| `docker-compose logs -f <service>` | View specific service logs |

## Makefile Shortcuts

| Command | Description |
|---------|-------------|
| `make start` | Start services (production) |
| `make dev` | Start services (development) |
| `make stop` | Stop services |
| `make restart` | Restart services |
| `make status` | Show service status |
| `make logs` | View all logs |
| `make logs-<service>` | View specific service logs |
| `make health` | Check service health |
| `make clean` | Remove containers |
| `make clean-all` | Remove containers and volumes |

## Access Points

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Frontend | http://localhost:3000 | N/A |
| API Gateway | http://localhost:8000 | N/A |
| API Docs | http://localhost:8000/docs | N/A |
| PgAdmin | http://localhost:8080 | admin@admin.com / admin |
| MinIO Console | http://localhost:9001 | esg_minio_admin / (from .env) |
| RabbitMQ Mgmt | http://localhost:15672 | esg_rabbitmq / (from .env) |
| PostgreSQL | localhost:5432 | esg_user / (from .env) |
| Redis | localhost:6379 | (from .env) |

## Development Mode

```bash
# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Or use Makefile
make dev
```

## Common Tasks

### Check Service Health
```bash
./quick-health-check.sh
# or
make test-quick
```

### View Service Logs
```bash
docker-compose logs -f api-gateway
# or
make logs-api-gateway
```

### Restart a Service
```bash
docker-compose restart extraction
# or
make restart-extraction
```

### Access Database
```bash
docker-compose exec postgres psql -U esg_user -d esg_platform
# or
make db-shell
```

### Rebuild a Service
```bash
docker-compose build extraction
docker-compose up -d extraction
# or
make rebuild-extraction
```

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs

# Check resources
docker stats

# Check ports
netstat -tuln | grep -E '5432|8000|3000'
```

### Health Checks Failing
```bash
# Check specific service
docker-compose logs <service-name>

# Check health status
docker-compose ps

# Restart service
docker-compose restart <service-name>
```

### Database Connection Issues
```bash
# Test connection
docker-compose exec postgres pg_isready -U esg_user

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Volume Issues
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect esg-platform_postgres_data

# Remove volumes (⚠️ deletes data)
docker-compose down -v
```

## Testing Workflow

1. **Initial Setup**
   ```bash
   cd infra
   cp .env.example .env
   # Edit .env
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Quick Check**
   ```bash
   ./quick-health-check.sh
   ```

4. **Comprehensive Test**
   ```bash
   ./test-docker-setup.sh
   ```

5. **Manual Verification**
   - Open http://localhost:3000
   - Open http://localhost:8000/docs
   - Check other web interfaces

## Documentation

| Document | Description |
|----------|-------------|
| `README.md` | Main infrastructure documentation |
| `TESTING.md` | Comprehensive testing guide |
| `TEST_REQUIREMENTS.md` | Requirements mapping |
| `TESTING_CHECKLIST.md` | Testing checklist |
| `TASK_46_SUMMARY.md` | Implementation summary |
| `QUICK_REFERENCE.md` | This document |

## Environment Variables

Key variables in `.env`:

```bash
# Database
POSTGRES_USER=esg_user
POSTGRES_PASSWORD=<your-password>
POSTGRES_DB=esg_platform

# MinIO
MINIO_ROOT_USER=esg_minio_admin
MINIO_ROOT_PASSWORD=<your-password>

# RabbitMQ
RABBITMQ_DEFAULT_USER=esg_rabbitmq
RABBITMQ_DEFAULT_PASS=<your-password>

# Google AI
GOOGLE_API_KEY=<your-api-key>

# API Gateway
SECRET_KEY=<random-64-char-string>
```

## Service Dependencies

```
Frontend → API Gateway → PostgreSQL
                      → Redis
                      
Extraction → PostgreSQL
          → RabbitMQ
          → Google AI

Embeddings → PostgreSQL
          → MinIO
          → RabbitMQ
          → Google AI

Ingestion → PostgreSQL
         → MinIO
         → RabbitMQ
```

## Health Check Endpoints

| Service | Endpoint | Method |
|---------|----------|--------|
| API Gateway | http://localhost:8000/health | GET |
| Extraction | http://localhost:8082/health | GET |
| MinIO | http://localhost:9000/minio/health/live | GET |
| RabbitMQ | http://localhost:15672 | GET |
| PostgreSQL | `pg_isready` command | CLI |
| Redis | `redis-cli ping` | CLI |

## Cleanup

```bash
# Stop services (keep data)
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Complete cleanup
docker-compose down -v --rmi all
docker system prune -a --volumes
```

## Getting Help

1. Check service logs: `docker-compose logs <service>`
2. Review documentation in `TESTING.md`
3. Run comprehensive tests: `./test-docker-setup.sh`
4. Check troubleshooting section in `README.md`
5. Verify environment variables in `.env`

## CI/CD Integration

Example GitHub Actions:
```yaml
- name: Test Docker Compose
  run: |
    cd infra
    cp .env.example .env
    ./test-docker-setup.sh
```

See `.github-workflows-example.yml` for complete example.

---

**Last Updated**: Task 46 Implementation  
**Version**: 1.0  
**Status**: Production Ready
