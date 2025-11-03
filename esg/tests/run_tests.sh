#!/bin/bash
#
# Integration Test Runner
# Runs all integration tests using uv
#

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== ESG Platform Integration Tests ==="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv is not installed${NC}"
    echo "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo -e "${GREEN}✓ uv is installed${NC}"

# Check if services are running
echo ""
echo "Checking if services are running..."

# Check PostgreSQL
if docker ps | grep -q postgres; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL is not running${NC}"
    echo "Start services: cd infra && docker-compose up -d"
fi

# Check API Gateway
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Gateway is running${NC}"
else
    echo -e "${YELLOW}⚠ API Gateway is not running${NC}"
fi

echo ""
echo "Running integration tests..."
echo ""

# Run tests with uv
uv run pytest integration/ -v "$@"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

exit $exit_code
