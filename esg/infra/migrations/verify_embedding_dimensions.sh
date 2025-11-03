#!/bin/bash

# Verification Script: Check document_embeddings dimensions
# This script verifies the current state of the document_embeddings table

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-moz}"
DB_USER="${POSTGRES_USER:-drfitz}"
DB_PASSWORD="${POSTGRES_PASSWORD:-h4i1hydr4}"

# Export password for psql
export PGPASSWORD="$DB_PASSWORD"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Embedding Dimensions Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check database connection
echo -e "${YELLOW}Checking database connection...${NC}"
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Failed to connect to database${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Checking document_embeddings table...${NC}"

# Check if table exists
TABLE_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'document_embeddings'
    );
" | tr -d ' ')

if [ "$TABLE_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓ Table exists${NC}"
else
    echo -e "${RED}✗ Table does not exist${NC}"
    exit 1
fi

# Get embedding dimensions
echo ""
echo -e "${YELLOW}Checking embedding dimensions...${NC}"
DIMENSIONS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT vector_dims(embedding) as dimensions
    FROM document_embeddings
    LIMIT 1;
" | tr -d ' ')

if [ -z "$DIMENSIONS" ]; then
    echo -e "${RED}✗ Could not determine dimensions${NC}"
    exit 1
elif [ "$DIMENSIONS" = "3072" ]; then
    echo -e "${GREEN}✓ Embedding dimensions: $DIMENSIONS (correct for gemini-embedding-001)${NC}"
else
    echo -e "${YELLOW}⚠ Embedding dimensions: $DIMENSIONS (expected 3072 for gemini-embedding-001)${NC}"
fi

# Count embeddings
echo ""
echo -e "${YELLOW}Counting embeddings...${NC}"
EMBEDDING_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*) FROM document_embeddings;
" | tr -d ' ')
echo -e "${GREEN}✓ Total embeddings: $EMBEDDING_COUNT${NC}"

# Check indexes
echo ""
echo -e "${YELLOW}Checking indexes...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT 
        indexname,
        indexdef
    FROM pg_indexes
    WHERE tablename = 'document_embeddings'
    ORDER BY indexname;
"

# Check for backup table
echo ""
echo -e "${YELLOW}Checking for backup table...${NC}"
BACKUP_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'document_embeddings_backup'
    );
" | tr -d ' ')

if [ "$BACKUP_EXISTS" = "t" ]; then
    BACKUP_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM document_embeddings_backup;
    " | tr -d ' ')
    echo -e "${GREEN}✓ Backup table exists with $BACKUP_COUNT embeddings${NC}"
else
    echo -e "${YELLOW}⚠ No backup table found${NC}"
fi

# Sample embedding check
if [ "$EMBEDDING_COUNT" -gt "0" ]; then
    echo ""
    echo -e "${YELLOW}Checking sample embedding...${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            id,
            object_key,
            company_name,
            report_year,
            chunk_index,
            vector_dims(embedding) as actual_dimensions,
            LEFT(chunk_text, 50) || '...' as chunk_preview,
            created_at
        FROM document_embeddings
        LIMIT 1;
    "
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Complete${NC}"
echo -e "${BLUE}========================================${NC}"

# Summary
echo ""
echo "Summary:"
echo "  - Table exists: Yes"
echo "  - Configured dimensions: $DIMENSIONS"
echo "  - Total embeddings: $EMBEDDING_COUNT"
echo "  - Backup exists: $([ "$BACKUP_EXISTS" = "t" ] && echo "Yes" || echo "No")"

if [ "$DIMENSIONS" = "3072" ]; then
    echo ""
    echo -e "${GREEN}✓ Schema is correctly configured for gemini-embedding-001 (3072 dimensions)${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠ Schema needs migration to 3072 dimensions${NC}"
    echo -e "${YELLOW}Run: ./migrate_embeddings_to_3072.sh${NC}"
    exit 1
fi

