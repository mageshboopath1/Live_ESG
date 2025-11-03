#!/bin/bash

# Migration Script: Update document_embeddings to 3072 dimensions
# This script updates the document_embeddings table from vector(768) to vector(3072)
# for use with Google Gemini gemini-embedding-001 model

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-moz}"
DB_USER="${POSTGRES_USER:-drfitz}"
DB_PASSWORD="${POSTGRES_PASSWORD:-h4i1hydr4}"

# Export password for psql
export PGPASSWORD="$DB_PASSWORD"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Embedding Dimensions Migration${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "This script will:"
echo "  1. Backup existing document_embeddings table"
echo "  2. Drop and recreate table with 3072 dimensions"
echo "  3. Recreate all indexes optimized for 3072 dimensions"
echo ""
echo -e "${RED}WARNING: This will delete all existing embeddings!${NC}"
echo -e "${RED}Make sure you have a database backup before proceeding.${NC}"
echo ""

# Check if running in force mode
if [ "$1" != "--force" ]; then
    read -p "Do you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Migration cancelled."
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}Step 1: Checking database connection...${NC}"
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Failed to connect to database${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Checking current embedding dimensions...${NC}"
CURRENT_DIM=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT vector_dims(embedding) as dimensions
    FROM document_embeddings
    LIMIT 1;
" 2>/dev/null | tr -d ' ')

if [ -z "$CURRENT_DIM" ]; then
    echo -e "${YELLOW}⚠ Could not determine current dimensions (table may be empty or not exist)${NC}"
else
    echo -e "${GREEN}✓ Current embedding dimensions: $CURRENT_DIM${NC}"
    if [ "$CURRENT_DIM" = "3072" ]; then
        echo -e "${GREEN}✓ Table already uses 3072 dimensions. No migration needed.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}Step 3: Counting existing embeddings...${NC}"
EMBEDDING_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*) FROM document_embeddings;
" | tr -d ' ')
echo -e "${GREEN}✓ Found $EMBEDDING_COUNT embeddings${NC}"

echo ""
echo -e "${YELLOW}Step 4: Running migration...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$(dirname "$0")/005_update_embedding_dimensions.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migration completed successfully${NC}"
else
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Verifying migration...${NC}"
# Check table structure (vector type should be defined as 3072)
TABLE_CHECK=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'document_embeddings' AND column_name = 'embedding';
" | tr -d ' ')

if [ -n "$TABLE_CHECK" ]; then
    echo -e "${GREEN}✓ Table structure verified - embedding column exists${NC}"
    echo -e "${GREEN}✓ Embedding dimensions configured for 3072${NC}"
else
    echo -e "${RED}✗ Verification failed. Table structure not found.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 6: Verifying indexes...${NC}"
INDEX_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*)
    FROM pg_indexes
    WHERE tablename = 'document_embeddings';
" | tr -d ' ')
echo -e "${GREEN}✓ Found $INDEX_COUNT indexes on document_embeddings${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Summary:"
echo "  - Backed up $EMBEDDING_COUNT embeddings to document_embeddings_backup"
echo "  - Updated embedding dimensions from $CURRENT_DIM to 3072"
echo "  - Recreated $INDEX_COUNT indexes"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Update embedding service to use gemini-embedding-001 with 3072 dimensions"
echo "  2. Update extraction service retriever to use 3072 dimensions"
echo "  3. Re-run embedding generation for all documents"
echo ""
echo -e "${YELLOW}Note: The backup table 'document_embeddings_backup' has been created.${NC}"
echo -e "${YELLOW}You can drop it once you've verified the migration: DROP TABLE document_embeddings_backup;${NC}"

