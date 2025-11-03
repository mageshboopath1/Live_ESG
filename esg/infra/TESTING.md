# Docker Compose Setup Testing Guide

This guide explains how to test the ESG Intelligence Platform Docker Compose setup according to task 46 requirements.

## Prerequisites

Before running tests, ensure you have:

1. **Docker and Docker Compose installed**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Environment configuration**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and set your values, especially:
   # - GOOGLE_API_KEY (required for embeddings and extraction)
   # - Strong passwords for all services
   nano .env
   ```

3. **Required tools** (for comprehensive testing)
   ```bash
   # Install jq for JSON parsing
   sudo apt-get install jq netcat-openbsd curl
   ```

## Quick Health Check

For a quick status check of all services:

```bash
cd infra
./quick-health-check.sh
```

This script checks:
- ✓ All services are running
- ✓ Health checks are passing
- ✓ Endpoints are accessible

## Comprehensive Testing

For full Docker Compose setup testing:

```bash
cd infra
./test-docker-setup.sh
```

This script performs the following tests:

### Test 1: Service Startup
- Starts all services with `docker-compose up -d`
- Verifies all containers start successfully
- Waits for initialization

### Test 2: Health Checks
- Verifies health checks for:
  - PostgreSQL
  - MinIO
  - RabbitMQ
  - Redis
  - Extraction Service
  - API Gateway
  - Frontend

### Test 3: Service-to-Service Communication
- Tests API Gateway → PostgreSQL connection
- Tests RabbitMQ management API
- Tests MinIO API
- Tests Redis connectivity
- Verifies internal Docker networking

### Test 4: Environment Variables
- Verifies environment variables are correctly passed to:
  - API Gateway (DB_HOST, etc.)
  - Extraction Service (RABBITMQ_HOST, etc.)
  - Embeddings Service (MINIO_ENDPOINT, etc.)

### Test 5: Volume Persistence
- Creates test data in PostgreSQL
- Stops all services
- Restarts services
- Verifies data persisted across restart

### Test 6: Development Mode
- Validates `docker-compose.dev.yml` configuration
- Checks volume mounts for hot-reload
- Verifies development-specific settings

### Test 7: Network Connectivity
- Checks backend network exists
- Checks frontend network exists
- Tests inter-service connectivity

### Test 8: Port Accessibility
- Verifies all exposed ports are accessible:
  - 5432: PostgreSQL
  - 8000: API Gateway
  - 3000: Frontend
  - 9000: MinIO API
  - 9001: MinIO Console
  - 15672: RabbitMQ Management
  - 8080: PgAdmin
  - 6379: Redis

### Test 9: Container Logs
- Checks logs for critical errors
- Identifies potential issues

## Manual Testing

### Testing Development Mode with Hot-Reload

1. **Start in development mode:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. **Test hot-reload for API Gateway:**
   ```bash
   # In another terminal, edit a file
   echo "# Test change" >> ../services/api-gateway/src/main.py
   
   # Watch logs for reload message
   docker-compose logs -f api-gateway
   ```

3. **Test hot-reload for Frontend:**
   ```bash
   # Edit a Vue component
   echo "<!-- Test change -->" >> ../services/frontend/src/App.vue
   
   # Watch logs for HMR (Hot Module Replacement)
   docker-compose logs -f frontend
   ```

### Testing Service Communication

1. **Test API Gateway endpoints:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # API documentation
   curl http://localhost:8000/docs
   
   # Companies endpoint
   curl http://localhost:8000/api/companies
   ```

2. **Test RabbitMQ queues:**
   ```bash
   # Access management UI
   open http://localhost:15672
   # Login: esg_rabbitmq / change_this_pass (from .env)
   
   # Check queues via API
   curl -u esg_rabbitmq:change_this_pass http://localhost:15672/api/queues
   ```

3. **Test MinIO storage:**
   ```bash
   # Access console
   open http://localhost:9001
   # Login: esg_minio_admin / change_this_secret (from .env)
   
   # List buckets via API
   docker-compose exec minio mc ls local/
   ```

4. **Test PostgreSQL:**
   ```bash
   # Connect via psql
   docker-compose exec postgres psql -U esg_user -d esg_platform
   
   # Or use PgAdmin
   open http://localhost:8080
   # Login: admin@admin.com / admin (from .env)
   ```

### Testing Volume Persistence

1. **Create test data:**
   ```bash
   docker-compose exec postgres psql -U esg_user -d esg_platform \
     -c "CREATE TABLE test_data (id SERIAL, value TEXT);"
   
   docker-compose exec postgres psql -U esg_user -d esg_platform \
     -c "INSERT INTO test_data (value) VALUES ('test');"
   ```

2. **Stop and restart:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Verify data persisted:**
   ```bash
   docker-compose exec postgres psql -U esg_user -d esg_platform \
     -c "SELECT * FROM test_data;"
   ```

4. **Cleanup:**
   ```bash
   docker-compose exec postgres psql -U esg_user -d esg_platform \
     -c "DROP TABLE test_data;"
   ```

## Troubleshooting

### Services Not Starting

```bash
# Check service logs
docker-compose logs <service-name>

# Check all logs
docker-compose logs

# Check specific service status
docker-compose ps <service-name>
```

### Health Checks Failing

```bash
# Check health status
docker-compose ps

# Inspect container
docker inspect esg-<service-name>

# Check health check logs
docker-compose logs <service-name> | grep health
```

### Port Conflicts

```bash
# Check if ports are already in use
netstat -tuln | grep -E '5432|8000|3000|9000|15672'

# Stop conflicting services or change ports in .env
```

### Environment Variables Not Set

```bash
# Verify .env file
cat .env

# Check if variables are passed to container
docker-compose exec <service-name> printenv | grep DB_HOST
```

### Volume Permission Issues

```bash
# Check volume permissions
docker volume inspect esg-platform_postgres_data

# Fix permissions (if needed)
docker-compose down
sudo chown -R $USER:$USER volumes/
docker-compose up -d
```

### Network Issues

```bash
# Check networks
docker network ls | grep esg

# Inspect network
docker network inspect esg-backend

# Recreate networks
docker-compose down
docker network prune
docker-compose up -d
```

## Cleanup

### Stop Services (Keep Data)

```bash
docker-compose down
```

### Stop Services and Remove Volumes

```bash
docker-compose down -v
```

### Complete Cleanup

```bash
# Stop and remove everything
docker-compose down -v --remove-orphans

# Remove images
docker-compose down --rmi all

# Prune unused resources
docker system prune -a --volumes
```

## Test Results Interpretation

### All Tests Passed ✓

Your Docker Compose setup is working correctly. All services are:
- Starting successfully
- Passing health checks
- Communicating properly
- Persisting data
- Configured correctly

You can proceed with development.

### Some Tests Failed ✗

Review the specific failures:

1. **Service startup failures**: Check logs and resource availability
2. **Health check failures**: Verify service configuration and dependencies
3. **Communication failures**: Check network configuration and firewall
4. **Environment variable issues**: Verify .env file and docker-compose.yml
5. **Persistence failures**: Check volume configuration and permissions

## Continuous Testing

### Pre-commit Testing

Add to your workflow:

```bash
# Before committing changes to docker-compose files
cd infra
./test-docker-setup.sh
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Docker Compose Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Create .env
        run: cp .env.example .env
      - name: Run tests
        run: |
          cd infra
          ./test-docker-setup.sh
```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Docker Networking](https://docs.docker.com/network/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)

## Support

If you encounter issues not covered in this guide:

1. Check service-specific README files
2. Review Docker Compose logs
3. Consult the main project documentation
4. Open an issue with test output and logs
