#!/bin/bash

# ============================================================================
# ESG Intelligence Platform - Docker Compose Setup Test Script
# ============================================================================
# This script tests the Docker Compose setup according to task 46 requirements:
# - Test docker-compose up starts all services successfully
# - Verify health checks pass for all services
# - Test service-to-service communication
# - Test volume persistence
# - Test development mode with hot-reload
# - Verify environment variables are correctly passed
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    print_header "Checking Environment Configuration"
    
    print_test "Checking if .env file exists"
    if [ -f ".env" ]; then
        print_success ".env file found"
    else
        print_error ".env file not found"
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_info "Please edit .env with your actual values, especially GOOGLE_API_KEY"
        exit 1
    fi
    
    print_test "Checking required environment variables"
    required_vars=(
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "POSTGRES_DB"
        "MINIO_ROOT_USER"
        "MINIO_ROOT_PASSWORD"
        "RABBITMQ_DEFAULT_USER"
        "RABBITMQ_DEFAULT_PASS"
    )
    
    source .env
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_success "All required environment variables are set"
    else
        print_error "Missing environment variables: ${missing_vars[*]}"
        exit 1
    fi
}

# Test 1: Start all services
test_docker_compose_up() {
    print_header "Test 1: Starting All Services"
    
    print_test "Starting services with docker-compose up"
    print_info "This may take several minutes on first run..."
    
    # Start services in detached mode
    if docker-compose up -d; then
        print_success "docker-compose up completed successfully"
    else
        print_error "docker-compose up failed"
        return 1
    fi
    
    print_info "Waiting 30 seconds for services to initialize..."
    sleep 30
}

# Test 2: Verify health checks
test_health_checks() {
    print_header "Test 2: Verifying Health Checks"
    
    services=(
        "postgres"
        "minio"
        "rabbitmq"
        "redis"
        "extraction"
        "api-gateway"
        "frontend"
    )
    
    for service in "${services[@]}"; do
        print_test "Checking health status of $service"
        
        # Get health status
        health_status=$(docker-compose ps --format json | jq -r ".[] | select(.Service == \"$service\") | .Health" 2>/dev/null || echo "unknown")
        
        if [ "$health_status" = "healthy" ]; then
            print_success "$service is healthy"
        elif [ "$health_status" = "unknown" ]; then
            # Some services might not have health checks
            state=$(docker-compose ps --format json | jq -r ".[] | select(.Service == \"$service\") | .State" 2>/dev/null || echo "unknown")
            if [ "$state" = "running" ]; then
                print_success "$service is running (no health check configured)"
            else
                print_error "$service is not running (state: $state)"
            fi
        else
            print_error "$service health check failed (status: $health_status)"
        fi
    done
}

# Test 3: Service-to-service communication
test_service_communication() {
    print_header "Test 3: Testing Service-to-Service Communication"
    
    # Test API Gateway to PostgreSQL
    print_test "Testing API Gateway connection to PostgreSQL"
    if docker-compose exec -T api-gateway curl -f http://localhost:8000/health 2>/dev/null; then
        print_success "API Gateway health endpoint accessible"
    else
        print_error "API Gateway health endpoint not accessible"
    fi
    
    # Test PostgreSQL connectivity
    print_test "Testing PostgreSQL connectivity"
    if docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER:-esg_user} -d ${POSTGRES_DB:-esg_platform} > /dev/null 2>&1; then
        print_success "PostgreSQL is accepting connections"
    else
        print_error "PostgreSQL is not accepting connections"
    fi
    
    # Test RabbitMQ management API
    print_test "Testing RabbitMQ management API"
    if curl -f -u ${RABBITMQ_DEFAULT_USER:-esg_rabbitmq}:${RABBITMQ_DEFAULT_PASS:-change_this_pass} \
        http://localhost:15672/api/overview > /dev/null 2>&1; then
        print_success "RabbitMQ management API accessible"
    else
        print_error "RabbitMQ management API not accessible"
    fi
    
    # Test MinIO API
    print_test "Testing MinIO API"
    if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        print_success "MinIO API accessible"
    else
        print_error "MinIO API not accessible"
    fi
    
    # Test Redis connectivity
    print_test "Testing Redis connectivity"
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is responding to PING"
    else
        print_error "Redis is not responding"
    fi
}

# Test 4: Environment variables
test_environment_variables() {
    print_header "Test 4: Verifying Environment Variables"
    
    # Test API Gateway environment variables
    print_test "Checking API Gateway environment variables"
    db_host=$(docker-compose exec -T api-gateway printenv DB_HOST 2>/dev/null || echo "")
    if [ "$db_host" = "postgres" ]; then
        print_success "DB_HOST correctly set to 'postgres'"
    else
        print_error "DB_HOST not correctly set (got: $db_host)"
    fi
    
    # Test Extraction service environment variables
    print_test "Checking Extraction service environment variables"
    rabbitmq_host=$(docker-compose exec -T extraction printenv RABBITMQ_HOST 2>/dev/null || echo "")
    if [ "$rabbitmq_host" = "rabbitmq" ]; then
        print_success "RABBITMQ_HOST correctly set to 'rabbitmq'"
    else
        print_error "RABBITMQ_HOST not correctly set (got: $rabbitmq_host)"
    fi
    
    # Test Embeddings service environment variables
    print_test "Checking Embeddings service environment variables"
    minio_endpoint=$(docker-compose exec -T embeddings printenv MINIO_ENDPOINT 2>/dev/null || echo "")
    if [ -n "$minio_endpoint" ]; then
        print_success "MINIO_ENDPOINT is set"
    else
        print_error "MINIO_ENDPOINT is not set"
    fi
}

# Test 5: Volume persistence
test_volume_persistence() {
    print_header "Test 5: Testing Volume Persistence"
    
    print_test "Creating test data in PostgreSQL"
    docker-compose exec -T postgres psql -U ${POSTGRES_USER:-esg_user} -d ${POSTGRES_DB:-esg_platform} \
        -c "CREATE TABLE IF NOT EXISTS test_persistence (id SERIAL PRIMARY KEY, data TEXT);" > /dev/null 2>&1
    docker-compose exec -T postgres psql -U ${POSTGRES_USER:-esg_user} -d ${POSTGRES_DB:-esg_platform} \
        -c "INSERT INTO test_persistence (data) VALUES ('test_data_$(date +%s)');" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Test data created in PostgreSQL"
    else
        print_error "Failed to create test data"
        return 1
    fi
    
    print_test "Stopping services"
    docker-compose stop > /dev/null 2>&1
    print_success "Services stopped"
    
    print_info "Waiting 5 seconds..."
    sleep 5
    
    print_test "Restarting services"
    docker-compose start > /dev/null 2>&1
    print_success "Services restarted"
    
    print_info "Waiting 20 seconds for services to be ready..."
    sleep 20
    
    print_test "Verifying test data persisted"
    count=$(docker-compose exec -T postgres psql -U ${POSTGRES_USER:-esg_user} -d ${POSTGRES_DB:-esg_platform} \
        -t -c "SELECT COUNT(*) FROM test_persistence;" 2>/dev/null | tr -d ' ')
    
    if [ "$count" -gt 0 ]; then
        print_success "Data persisted after restart (found $count rows)"
    else
        print_error "Data did not persist after restart"
    fi
    
    # Cleanup
    docker-compose exec -T postgres psql -U ${POSTGRES_USER:-esg_user} -d ${POSTGRES_DB:-esg_platform} \
        -c "DROP TABLE IF EXISTS test_persistence;" > /dev/null 2>&1
}

# Test 6: Development mode
test_development_mode() {
    print_header "Test 6: Testing Development Mode"
    
    print_test "Checking if docker-compose.dev.yml exists"
    if [ -f "docker-compose.dev.yml" ]; then
        print_success "docker-compose.dev.yml found"
    else
        print_error "docker-compose.dev.yml not found"
        return 1
    fi
    
    print_test "Validating development compose configuration"
    if docker-compose -f docker-compose.yml -f docker-compose.dev.yml config > /dev/null 2>&1; then
        print_success "Development compose configuration is valid"
    else
        print_error "Development compose configuration is invalid"
        return 1
    fi
    
    print_info "Note: Full hot-reload testing requires manual verification"
    print_info "To test hot-reload: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up"
}

# Test 7: Network connectivity
test_network_connectivity() {
    print_header "Test 7: Testing Network Connectivity"
    
    print_test "Checking backend network exists"
    if docker network inspect esg-backend > /dev/null 2>&1; then
        print_success "Backend network exists"
    else
        print_error "Backend network does not exist"
    fi
    
    print_test "Checking frontend network exists"
    if docker network inspect esg-frontend > /dev/null 2>&1; then
        print_success "Frontend network exists"
    else
        print_error "Frontend network does not exist"
    fi
    
    print_test "Testing API Gateway can reach PostgreSQL"
    if docker-compose exec -T api-gateway ping -c 1 postgres > /dev/null 2>&1; then
        print_success "API Gateway can reach PostgreSQL"
    else
        print_error "API Gateway cannot reach PostgreSQL"
    fi
}

# Test 8: Port accessibility
test_port_accessibility() {
    print_header "Test 8: Testing Port Accessibility"
    
    ports=(
        "5432:PostgreSQL"
        "8000:API Gateway"
        "3000:Frontend"
        "9000:MinIO API"
        "9001:MinIO Console"
        "15672:RabbitMQ Management"
        "8080:PgAdmin"
        "6379:Redis"
    )
    
    for port_info in "${ports[@]}"; do
        port="${port_info%%:*}"
        service="${port_info##*:}"
        
        print_test "Checking if port $port ($service) is accessible"
        if nc -z localhost $port 2>/dev/null; then
            print_success "Port $port ($service) is accessible"
        else
            print_error "Port $port ($service) is not accessible"
        fi
    done
}

# Test 9: Container logs
test_container_logs() {
    print_header "Test 9: Checking Container Logs for Errors"
    
    services=("postgres" "minio" "rabbitmq" "redis" "api-gateway" "extraction" "embeddings")
    
    for service in "${services[@]}"; do
        print_test "Checking $service logs for critical errors"
        
        # Get last 50 lines of logs and check for common error patterns
        error_count=$(docker-compose logs --tail=50 $service 2>/dev/null | grep -iE "error|exception|fatal|failed" | grep -v "ERROR_HANDLING" | wc -l)
        
        if [ "$error_count" -eq 0 ]; then
            print_success "$service logs show no critical errors"
        else
            print_error "$service logs contain $error_count potential error messages"
            print_info "Run 'docker-compose logs $service' to investigate"
        fi
    done
}

# Cleanup function
cleanup() {
    print_header "Cleanup"
    
    print_info "Test run completed. Services are still running."
    print_info "To stop services: docker-compose down"
    print_info "To stop and remove volumes: docker-compose down -v"
}

# Print summary
print_summary() {
    print_header "Test Summary"
    
    echo -e "Total Tests: ${TESTS_TOTAL}"
    echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
    echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed!${NC}"
        echo -e "\n${BLUE}Your Docker Compose setup is working correctly.${NC}"
        echo -e "${BLUE}Services are running and ready for development.${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some tests failed.${NC}"
        echo -e "\n${YELLOW}Please review the errors above and:${NC}"
        echo -e "  1. Check service logs: docker-compose logs <service-name>"
        echo -e "  2. Verify .env configuration"
        echo -e "  3. Ensure all required ports are available"
        echo -e "  4. Check Docker resources (memory, disk space)"
        return 1
    fi
}

# Main execution
main() {
    print_header "ESG Intelligence Platform - Docker Compose Setup Test"
    
    # Change to infra directory
    cd "$(dirname "$0")"
    
    # Run tests
    check_env_file
    test_docker_compose_up
    test_health_checks
    test_service_communication
    test_environment_variables
    test_volume_persistence
    test_development_mode
    test_network_connectivity
    test_port_accessibility
    test_container_logs
    
    # Print summary
    print_summary
    exit_code=$?
    
    # Cleanup
    cleanup
    
    exit $exit_code
}

# Run main function
main
