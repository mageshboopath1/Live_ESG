#!/bin/bash

# Migration Verification Script
# Verifies that all migrations have been applied correctly

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-esg_platform}"
DB_USER="${DB_USER:-esg_user}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Function to execute SQL query
execute_query() {
    local query=$1
    if [ -n "$DB_PASSWORD" ]; then
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$query" 2>/dev/null
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$query" 2>/dev/null
    fi
}

# Function to check if table exists
check_table() {
    local table_name=$1
    local result=$(execute_query "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$table_name');")
    echo "$result" | tr -d '[:space:]'
}

# Function to count rows
count_rows() {
    local table_name=$1
    local result=$(execute_query "SELECT COUNT(*) FROM $table_name;")
    echo "$result" | tr -d '[:space:]'
}

# Function to check if index exists
check_index() {
    local index_name=$1
    local result=$(execute_query "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = '$index_name');")
    echo "$result" | tr -d '[:space:]'
}

# Function to check if extension exists
check_extension() {
    local ext_name=$1
    local result=$(execute_query "SELECT EXISTS (SELECT FROM pg_extension WHERE extname = '$ext_name');")
    echo "$result" | tr -d '[:space:]'
}

echo "=========================================="
echo "Database Migration Verification"
echo "=========================================="
echo ""

# Check database connection
print_info "Checking database connection..."
if execute_query "SELECT 1;" > /dev/null 2>&1; then
    print_success "Connected to database: $DB_NAME"
else
    print_error "Failed to connect to database"
    exit 1
fi
echo ""

# Check pgvector extension
print_info "Checking pgvector extension..."
if [ "$(check_extension 'vector')" = "t" ]; then
    print_success "pgvector extension is installed"
else
    print_error "pgvector extension is NOT installed"
fi
echo ""

# Check Migration 001: Initial Schema
print_info "Verifying Migration 001: Initial Schema"
tables_001=("company_catalog" "ingestion_metadata" "document_embeddings")
for table in "${tables_001[@]}"; do
    if [ "$(check_table $table)" = "t" ]; then
        print_success "Table exists: $table"
    else
        print_error "Table missing: $table"
    fi
done
echo ""

# Check Migration 002: BRSR Indicators
print_info "Verifying Migration 002: BRSR Indicators"

if [ "$(check_table 'brsr_indicators')" = "t" ]; then
    print_success "Table exists: brsr_indicators"
    
    # Count indicators
    count=$(count_rows 'brsr_indicators')
    if [ "$count" -ge 60 ]; then
        print_success "BRSR indicators seeded: $count indicators"
    else
        print_error "BRSR indicators incomplete: only $count indicators (expected 60+)"
    fi
    
    # Check distribution by attribute
    print_info "Checking indicator distribution by attribute..."
    for attr in {1..9}; do
        count=$(execute_query "SELECT COUNT(*) FROM brsr_indicators WHERE attribute_number = $attr;" | tr -d '[:space:]')
        echo "  Attribute $attr: $count indicators"
    done
    
    # Check distribution by pillar
    print_info "Checking indicator distribution by pillar..."
    for pillar in E S G; do
        count=$(execute_query "SELECT COUNT(*) FROM brsr_indicators WHERE pillar = '$pillar';" | tr -d '[:space:]')
        echo "  Pillar $pillar: $count indicators"
    done
else
    print_error "Table missing: brsr_indicators"
fi

# Check critical indexes
print_info "Checking critical indexes..."
critical_indexes=(
    "idx_doc_emb_company_year"
    "idx_doc_emb_object_key"
    "idx_doc_emb_vector"
    "idx_brsr_attribute"
    "idx_brsr_pillar"
)
for index in "${critical_indexes[@]}"; do
    if [ "$(check_index $index)" = "t" ]; then
        print_success "Index exists: $index"
    else
        print_error "Index missing: $index"
    fi
done
echo ""

# Check Migration 003: Extraction Tables
print_info "Verifying Migration 003: Extraction Tables"
tables_003=("extracted_indicators" "esg_scores")
for table in "${tables_003[@]}"; do
    if [ "$(check_table $table)" = "t" ]; then
        print_success "Table exists: $table"
    else
        print_error "Table missing: $table"
    fi
done

# Check extraction indexes
print_info "Checking extraction indexes..."
extraction_indexes=(
    "idx_extracted_object_key"
    "idx_extracted_company_id"
    "idx_extracted_indicator_id"
    "idx_scores_company_id"
)
for index in "${extraction_indexes[@]}"; do
    if [ "$(check_index $index)" = "t" ]; then
        print_success "Index exists: $index"
    else
        print_error "Index missing: $index"
    fi
done
echo ""

# Check Migration 004: Auth Tables
print_info "Verifying Migration 004: Auth Tables"
tables_004=("users" "api_keys")
for table in "${tables_004[@]}"; do
    if [ "$(check_table $table)" = "t" ]; then
        print_success "Table exists: $table"
    else
        print_error "Table missing: $table"
    fi
done

# Check default users
if [ "$(check_table 'users')" = "t" ]; then
    user_count=$(count_rows 'users')
    if [ "$user_count" -ge 2 ]; then
        print_success "Default users created: $user_count users"
    else
        print_error "Default users missing: only $user_count users (expected 2)"
    fi
fi
echo ""

# Summary
print_info "Verification Summary"
total_tables=9
existing_tables=0
for table in company_catalog ingestion_metadata document_embeddings brsr_indicators extracted_indicators esg_scores users api_keys; do
    if [ "$(check_table $table)" = "t" ]; then
        ((existing_tables++))
    fi
done

echo "Tables: $existing_tables/$total_tables"

if [ "$existing_tables" -eq "$total_tables" ]; then
    print_success "All migrations verified successfully!"
    exit 0
else
    print_error "Some migrations are incomplete or missing"
    exit 1
fi
