#!/bin/bash

# ============================================================================
# ESG Intelligence Platform - Setup Verification Script
# ============================================================================
# This script verifies that the Docker Compose setup is correctly configured
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to print colored messages
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header "ESG Intelligence Platform - Setup Verification"

# Check 1: Docker installed
print_info "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker is installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed"
fi

# Check 2: Docker Compose installed
print_info "Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose is installed: $COMPOSE_VERSION"
else
    print_error "Docker Compose is not installed"
fi

# Check 3: Docker daemon running
print_info "Checking Docker daemon..."
if docker info &> /dev/null; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon is not running"
fi

# Check 4: Configuration files exist
print_info "Checking configuration files..."
if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
    print_success "docker-compose.yml exists"
else
    print_error "docker-compose.yml not found"
fi

if [ -f "$SCRIPT_DIR/docker-compose.dev.yml" ]; then
    print_success "docker-compose.dev.yml exists"
else
    print_error "docker-compose.dev.yml not found"
fi

if [ -f "$SCRIPT_DIR/.env" ]; then
    print_success ".env file exists"
else
    print_warning ".env file not found (will use defaults)"
fi

# Check 5: Validate docker-compose.yml
print_info "Validating docker-compose.yml..."
if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" config --quiet 2>/dev/null; then
    print_success "docker-compose.yml is valid"
else
    print_error "docker-compose.yml has errors"
fi

# Check 6: Validate docker-compose.dev.yml
print_info "Validating docker-compose.dev.yml..."
if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" -f "$SCRIPT_DIR/docker-compose.dev.yml" config --quiet 2>/dev/null; then
    print_success "docker-compose.dev.yml is valid"
else
    print_error "docker-compose.dev.yml has errors"
fi

# Check 7: Count services
print_info "Counting configured services..."
SERVICE_COUNT=$(docker-compose -f "$SCRIPT_DIR/docker-compose.yml" config --services | wc -l)
if [ "$SERVICE_COUNT" -eq 12 ]; then
    print_success "All 12 services are configured"
else
    print_warning "Expected 12 services, found $SERVICE_COUNT"
fi

# Check 8: List services
print_info "Configured services:"
docker-compose -f "$SCRIPT_DIR/docker-compose.yml" config --services | while read service; do
    echo "  - $service"
done

# Check 9: Check for required environment variables
print_info "Checking environment variables..."
if [ -f "$SCRIPT_DIR/.env" ]; then
    if grep -q "GOOGLE_API_KEY" "$SCRIPT_DIR/.env"; then
        print_success "GOOGLE_API_KEY is configured"
    else
        print_warning "GOOGLE_API_KEY not found in .env"
    fi
    
    if grep -q "POSTGRES_PASSWORD" "$SCRIPT_DIR/.env"; then
        print_success "POSTGRES_PASSWORD is configured"
    else
        print_warning "POSTGRES_PASSWORD not found in .env"
    fi
    
    if grep -q "SECRET_KEY" "$SCRIPT_DIR/.env"; then
        print_success "SECRET_KEY is configured"
    else
        print_warning "SECRET_KEY not found in .env"
    fi
fi

# Check 10: Check port availability
print_info "Checking port availability..."
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port ($service) is already in use"
    else
        print_success "Port $port ($service) is available"
    fi
}

check_port 5432 "PostgreSQL"
check_port 8000 "API Gateway"
check_port 3000 "Frontend"
check_port 8080 "PgAdmin"
check_port 9000 "MinIO API"
check_port 9001 "MinIO Console"
check_port 15672 "RabbitMQ Management"
check_port 6379 "Redis"

# Check 11: Check Dockerfiles exist
print_info "Checking Dockerfiles..."
check_dockerfile() {
    local path=$1
    local service=$2
    if [ -f "$path" ]; then
        print_success "$service Dockerfile exists"
    else
        print_warning "$service Dockerfile not found at $path"
    fi
}

check_dockerfile "$SCRIPT_DIR/../services/api-gateway/Dockerfile" "API Gateway"
check_dockerfile "$SCRIPT_DIR/../services/extraction/Dockerfile" "Extraction"
check_dockerfile "$SCRIPT_DIR/../services/frontend/Dockerfile" "Frontend"
check_dockerfile "$SCRIPT_DIR/../services/frontend/Dockerfile.dev" "Frontend Dev"
check_dockerfile "$SCRIPT_DIR/../services/embeddings/dockerfile" "Embeddings"
check_dockerfile "$SCRIPT_DIR/../services/ingestion/dockerfile" "Ingestion"
check_dockerfile "$SCRIPT_DIR/../services/company-catalog/dockerfile" "Company Catalog"

# Check 12: Check helper scripts
print_info "Checking helper scripts..."
if [ -f "$SCRIPT_DIR/start.sh" ] && [ -x "$SCRIPT_DIR/start.sh" ]; then
    print_success "start.sh exists and is executable"
else
    print_warning "start.sh not found or not executable"
fi

if [ -f "$SCRIPT_DIR/Makefile" ]; then
    print_success "Makefile exists"
else
    print_warning "Makefile not found"
fi

# Summary
print_header "Verification Summary"
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${RED}Failed:${NC}   $FAILED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ Setup verification completed successfully!${NC}"
    echo -e "\nYou can now start the services with:"
    echo -e "  ${BLUE}cd infra && make start${NC}"
    echo -e "  ${BLUE}cd infra && ./start.sh start${NC}"
    echo -e "  ${BLUE}cd infra && docker-compose up -d${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Setup verification found errors. Please fix them before starting services.${NC}"
    exit 1
fi
