# Database Migrations - Quick Start Guide

## Overview

The ESG Intelligence Platform uses numbered SQL migration scripts to manage database schema changes. Each migration has a forward script (applies changes) and a rollback script (reverts changes).

## Quick Commands

### Using Docker Compose (Recommended)

Migrations run automatically when PostgreSQL starts:

```bash
# Start all services (migrations run automatically)
docker-compose up -d

# Check if migrations ran successfully
docker-compose logs postgres | grep -i migration
```

### Using the Migration Script

```bash
# Navigate to migrations directory
cd infra/migrations

# Check migration status
./migrate.sh status

# Apply all pending migrations
./migrate.sh up

# Apply migrations up to a specific number
./migrate.sh up 3

# Rollback last migration
./migrate.sh down

# Rollback a specific migration
./migrate.sh down 3
```

### Manual Migration

```bash
# Connect to database
docker-compose exec postgres psql -U esg_user -d esg_platform

# Run a migration
\i /docker-entrypoint-initdb.d/001_initial_schema.sql

# Run a rollback
\i /docker-entrypoint-initdb.d/001_initial_schema_rollback.sql
```

## Migration Files

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | Base tables (company_catalog, ingestion_metadata, document_embeddings) |
| `002_brsr_indicators.sql` | BRSR indicators table + 60+ indicator definitions + indexes |
| `003_extraction_tables.sql` | Extraction results (extracted_indicators, esg_scores) |
| `004_auth_tables.sql` | Authentication (users, api_keys) |

## What Gets Created

### After Migration 001
- ✅ `company_catalog` table
- ✅ `ingestion_metadata` table
- ✅ `document_embeddings` table with pgvector support

### After Migration 002
- ✅ `brsr_indicators` table with 60+ seeded indicators
- ✅ Critical indexes for filtered vector retrieval
- ✅ HNSW vector index for similarity search

### After Migration 003
- ✅ `extracted_indicators` table for LLM extraction results
- ✅ `esg_scores` table for calculated scores
- ✅ Indexes for efficient querying

### After Migration 004
- ✅ `users` table for authentication
- ✅ `api_keys` table for API access
- ✅ Default admin user (username: `admin`, password: `admin123`)

## Verifying Migrations

```bash
# Check tables exist
docker-compose exec postgres psql -U esg_user -d esg_platform -c "\dt"

# Check BRSR indicators were seeded
docker-compose exec postgres psql -U esg_user -d esg_platform -c "SELECT COUNT(*) FROM brsr_indicators;"

# Check indexes
docker-compose exec postgres psql -U esg_user -d esg_platform -c "\di"

# Check vector extension
docker-compose exec postgres psql -U esg_user -d esg_platform -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

## Troubleshooting

### Migrations didn't run automatically

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Manually run migrations
docker-compose exec postgres psql -U esg_user -d esg_platform -f /docker-entrypoint-initdb.d/001_initial_schema.sql
```

### Need to reset database

```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm infra_postgres_data

# Start services (migrations will run fresh)
docker-compose up -d
```

### Migration failed halfway

```bash
# Check what's in the database
docker-compose exec postgres psql -U esg_user -d esg_platform -c "\dt"

# Rollback if needed
cd infra/migrations
./migrate.sh down

# Try again
./migrate.sh up
```

## Environment Variables

Set these before running migrations:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=esg_platform
export DB_USER=esg_user
export DB_PASSWORD=your_password
```

Or use Docker Compose (recommended) which handles this automatically.

## Next Steps

After migrations complete:

1. ✅ Verify all tables exist
2. ✅ Check BRSR indicators are seeded (should be 60+)
3. ✅ Test vector similarity search
4. ✅ Start extraction service
5. ✅ Start API gateway

## Support

For detailed documentation, see [README.md](./README.md)

For issues:
1. Check PostgreSQL logs: `docker-compose logs postgres`
2. Verify database connection: `docker-compose exec postgres psql -U esg_user -d esg_platform -c "SELECT version();"`
3. Check migration status: `./migrate.sh status`
