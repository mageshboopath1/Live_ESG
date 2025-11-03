#!/bin/bash

set -e

echo "=== ESG Platform Integration Test Runner ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Check if services are running
echo -e "${BLUE}Checking if services are running...${NC}"
if docker ps | grep -q "esg-postgres"; then
    echo -e "${GREEN}✓ Services are running${NC}"
else
    echo -e "${YELLOW}⚠ Services not running. Starting services...${NC}"
    cd "$PROJECT_ROOT/infra"
    docker-compose up -d
    
    echo -e "${YELLOW}Waiting for services to be healthy (this may take 30-60 seconds)...${NC}"
    sleep 30
    
    # Wait for PostgreSQL to be ready
    echo -n "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker exec esg-postgres pg_isready -U drfitz -d moz > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for API Gateway to be ready
    echo -n "Waiting for API Gateway..."
    for i in {1..30}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${GREEN}✓ Services started${NC}"
fi

echo ""
echo "=== Running Health Check ==="
echo ""

# Run health check
if bash "$SCRIPT_DIR/health_check.sh"; then
    echo ""
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo ""
    echo -e "${RED}✗ Health check failed. Please fix service issues before running tests.${NC}"
    exit 1
fi

echo ""
echo "=== Running Integration Tests ==="
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠ pytest not found. Installing test dependencies...${NC}"
    cd "$SCRIPT_DIR"
    if [ -f "pyproject.toml" ]; then
        uv sync
    else
        echo -e "${RED}✗ pyproject.toml not found. Cannot install dependencies.${NC}"
        exit 1
    fi
fi

# Run integration tests
cd "$SCRIPT_DIR"
echo -e "${BLUE}Running integration tests with pytest...${NC}"
echo ""

# Run tests with verbose output and generate report
if pytest integration/ -v --tb=short --color=yes 2>&1 | tee test_results.log; then
    TEST_EXIT_CODE=0
else
    TEST_EXIT_CODE=$?
fi

echo ""
echo "=== Test Summary ==="
echo ""

# Parse test results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All integration tests passed${NC}"
    
    # Count passed tests
    PASSED_COUNT=$(grep -c "PASSED" test_results.log || echo "0")
    echo -e "${GREEN}  Passed: $PASSED_COUNT${NC}"
else
    echo -e "${RED}✗ Some integration tests failed${NC}"
    
    # Count passed and failed tests
    PASSED_COUNT=$(grep -c "PASSED" test_results.log || echo "0")
    FAILED_COUNT=$(grep -c "FAILED" test_results.log || echo "0")
    echo -e "${GREEN}  Passed: $PASSED_COUNT${NC}"
    echo -e "${RED}  Failed: $FAILED_COUNT${NC}"
fi

echo ""
echo "=== Test Report ==="
echo "Full test output saved to: $SCRIPT_DIR/test_results.log"
echo ""

# Exit with test exit code
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Integration test suite completed successfully${NC}"
    exit 0
else
    echo -e "${RED}✗ Integration test suite completed with failures${NC}"
    exit 1
fi
