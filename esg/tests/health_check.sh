#!/bin/bash

echo "=== ESG Platform Health Check ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall health
ALL_HEALTHY=true

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker exec esg-postgres pg_isready -U drfitz -d moz > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
    ALL_HEALTHY=false
fi

# Check MinIO
echo -n "MinIO: "
if curl -sf http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
    ALL_HEALTHY=false
fi

# Check RabbitMQ
echo -n "RabbitMQ: "
if docker exec esg-rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
    ALL_HEALTHY=false
fi

# Check Redis
echo -n "Redis: "
if docker exec esg-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
    ALL_HEALTHY=false
fi

# Check API Gateway
echo -n "API Gateway: "
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
    ALL_HEALTHY=false
fi

# Check Frontend
echo -n "Frontend: "
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
    ALL_HEALTHY=false
fi

echo ""
echo "=== Database Verification ==="

# Check BRSR indicators
BRSR_COUNT=$(docker exec esg-postgres psql -U drfitz -d moz -t -c "SELECT COUNT(*) FROM brsr_indicators" 2>/dev/null | tr -d ' ')
echo -n "BRSR Indicators: "
if [ -z "$BRSR_COUNT" ]; then
    echo -e "${RED}✗ Unable to query${NC}"
    ALL_HEALTHY=false
elif [ "$BRSR_COUNT" -gt 0 ]; then
    if [ "$BRSR_COUNT" -ge 60 ]; then
        echo -e "${GREEN}✓ $BRSR_COUNT indicators (complete)${NC}"
    else
        echo -e "${YELLOW}⚠ $BRSR_COUNT indicators (expected 60+)${NC}"
    fi
else
    echo -e "${RED}✗ Empty table${NC}"
    ALL_HEALTHY=false
fi

# Check companies
COMPANY_COUNT=$(docker exec esg-postgres psql -U drfitz -d moz -t -c "SELECT COUNT(*) FROM company_catalog" 2>/dev/null | tr -d ' ')
echo -n "Companies: "
if [ -z "$COMPANY_COUNT" ]; then
    echo -e "${RED}✗ Unable to query${NC}"
    ALL_HEALTHY=false
elif [ "$COMPANY_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ $COMPANY_COUNT companies${NC}"
else
    echo -e "${YELLOW}⚠ Empty table (no companies yet)${NC}"
fi

# Check embeddings
EMBEDDING_COUNT=$(docker exec esg-postgres psql -U drfitz -d moz -t -c "SELECT COUNT(*) FROM document_embeddings" 2>/dev/null | tr -d ' ')
echo -n "Document Embeddings: "
if [ -z "$EMBEDDING_COUNT" ]; then
    echo -e "${RED}✗ Unable to query${NC}"
    ALL_HEALTHY=false
elif [ "$EMBEDDING_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ $EMBEDDING_COUNT embeddings${NC}"
else
    echo -e "${YELLOW}⚠ Empty table (no documents processed yet)${NC}"
fi

# Check extracted indicators
EXTRACTED_COUNT=$(docker exec esg-postgres psql -U drfitz -d moz -t -c "SELECT COUNT(*) FROM extracted_indicators" 2>/dev/null | tr -d ' ')
echo -n "Extracted Indicators: "
if [ -z "$EXTRACTED_COUNT" ]; then
    echo -e "${RED}✗ Unable to query${NC}"
    ALL_HEALTHY=false
elif [ "$EXTRACTED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ $EXTRACTED_COUNT extracted${NC}"
else
    echo -e "${YELLOW}⚠ Empty table (no extractions yet)${NC}"
fi

# Check scores
SCORE_COUNT=$(docker exec esg-postgres psql -U drfitz -d moz -t -c "SELECT COUNT(*) FROM esg_scores" 2>/dev/null | tr -d ' ')
echo -n "ESG Scores: "
if [ -z "$SCORE_COUNT" ]; then
    echo -e "${RED}✗ Unable to query${NC}"
    ALL_HEALTHY=false
elif [ "$SCORE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ $SCORE_COUNT scores${NC}"
else
    echo -e "${YELLOW}⚠ Empty table (no scores calculated yet)${NC}"
fi

echo ""
echo "=== API Endpoint Tests ==="

# Load API key from file if it exists
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
API_KEY_FILE="$SCRIPT_DIR/.test_api_key"

if [ -f "$API_KEY_FILE" ]; then
    TEST_API_KEY=$(cat "$API_KEY_FILE")
    echo -e "${GREEN}✓ Using test API key${NC}"
else
    echo -e "${YELLOW}⚠ No test API key found. Run: uv run tests/utils/generate_test_api_key.py${NC}"
    TEST_API_KEY=""
fi

# Set up curl headers
if [ -n "$TEST_API_KEY" ]; then
    CURL_HEADERS="-H X-API-Key:$TEST_API_KEY"
else
    CURL_HEADERS=""
fi

# Test companies endpoint
echo -n "GET /api/companies: "
COMPANIES_RESPONSE=$(curl -sf $CURL_HEADERS http://localhost:8000/api/companies 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    ALL_HEALTHY=false
fi

# Test indicators endpoint
echo -n "GET /api/brsr/indicators: "
INDICATORS_RESPONSE=$(curl -sf $CURL_HEADERS http://localhost:8000/api/brsr/indicators 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    ALL_HEALTHY=false
fi

# Test scores endpoint (requires company_id, test with company 1)
echo -n "GET /api/companies/1/scores: "
SCORES_RESPONSE=$(curl -sf $CURL_HEADERS http://localhost:8000/api/companies/1/scores 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    ALL_HEALTHY=false
fi

# Test reports endpoint
echo -n "GET /api/reports: "
REPORTS_RESPONSE=$(curl -sf $CURL_HEADERS http://localhost:8000/api/reports 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    ALL_HEALTHY=false
fi

echo ""
echo "=== Summary ==="
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ All critical services are healthy${NC}"
    exit 0
else
    echo -e "${RED}✗ Some services are unhealthy${NC}"
    exit 1
fi
