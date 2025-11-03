#!/bin/bash

# ============================================================================
# ESG Intelligence Platform - Quick Health Check Script
# ============================================================================
# Quick script to check if all services are running and healthy
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}ESG Intelligence Platform - Quick Health Check${NC}\n"

# Change to infra directory
cd "$(dirname "$0")"

# Check if services are running
echo "Checking service status..."
echo ""

services=(
    "postgres:PostgreSQL Database"
    "minio:MinIO Object Storage"
    "rabbitmq:RabbitMQ Message Queue"
    "redis:Redis Cache"
    "api-gateway:API Gateway"
    "extraction:Extraction Service"
    "embeddings:Embeddings Service"
    "frontend:Frontend Application"
)

all_healthy=true

for service_info in "${services[@]}"; do
    service="${service_info%%:*}"
    name="${service_info##*:}"
    
    # Check if container is running
    if docker-compose ps --format json | jq -e ".[] | select(.Service == \"$service\" and .State == \"running\")" > /dev/null 2>&1; then
        # Check health status
        health=$(docker-compose ps --format json | jq -r ".[] | select(.Service == \"$service\") | .Health" 2>/dev/null || echo "unknown")
        
        if [ "$health" = "healthy" ]; then
            echo -e "${GREEN}✓${NC} $name: Running & Healthy"
        elif [ "$health" = "unknown" ]; then
            echo -e "${GREEN}✓${NC} $name: Running"
        else
            echo -e "${RED}✗${NC} $name: Running but unhealthy ($health)"
            all_healthy=false
        fi
    else
        echo -e "${RED}✗${NC} $name: Not running"
        all_healthy=false
    fi
done

echo ""

# Check accessible endpoints
echo "Checking accessible endpoints..."
echo ""

endpoints=(
    "http://localhost:8000/health:API Gateway"
    "http://localhost:9000/minio/health/live:MinIO"
    "http://localhost:15672:RabbitMQ Management"
    "http://localhost:3000:Frontend"
)

for endpoint_info in "${endpoints[@]}"; do
    endpoint="${endpoint_info%%:*}"
    name="${endpoint_info##*:}"
    
    if curl -f -s "$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name: Accessible at $endpoint"
    else
        echo -e "${RED}✗${NC} $name: Not accessible at $endpoint"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}All services are healthy!${NC}"
    echo ""
    echo "Access points:"
    echo "  - API Gateway: http://localhost:8000"
    echo "  - Frontend: http://localhost:3000"
    echo "  - MinIO Console: http://localhost:9001"
    echo "  - RabbitMQ Management: http://localhost:15672"
    echo "  - PgAdmin: http://localhost:8080"
    exit 0
else
    echo -e "${RED}Some services are not healthy.${NC}"
    echo ""
    echo "Run 'docker-compose logs <service-name>' to investigate."
    echo "Run './test-docker-setup.sh' for detailed testing."
    exit 1
fi
