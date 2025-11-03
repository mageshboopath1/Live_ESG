# Database Migrations

This directory contains numbered SQL migration scripts for the ESG Intelligence Platform database schema.

## Migration Structure

Each migration consists of two files:
- `XXX_migration_name.sql` - Forward migration (applies changes)
- `XXX_migration_name_rollback.sql` - Rollback migration (reverts changes)

## Migration List

### 001_initial_schema
**Description**: Creates base tables for company catalog, ingestion metadata, and document embeddings with pgvector extension.

**Tables Created**:
- `company_catalog` - Stores NIFTY 50 company information
- `ingestion_metadata` - Tracks document ingestion status
- `document_embeddings` - Stores text chunks with vector embeddings

**Dependencies**: None

---

### 002_brsr_indicators
**Description**: Creates BRSR Core indicators table with all 9 attributes and seeds ~60 indicator definitions.

**Tables Created**:
- `brsr_indicators` - BRSR Core indicator definitions

**Indexes Created**:
- Indexes on `brsr_indicators` for efficient filtering
- Critical composite index on `document_embeddings(company_name, report_year)` for filtered vector retrieval
- HNSW vector index on `document_embeddings.embedding` for similarity search

**Data Seeded**:
- 60+ BRSR Core indicators across 9 attributes:
  1. GHG Footprint (4 indicators)
  2. Water Footprint (7 indicators)
  3. Energy Footprint (4 indicators)
  4. Waste Management (16 indicators)
  5. Employee Wellbeing and Safety (4 indicators)
  6. Gender Diversity (4 indicators)
  7. Inclusive Development (3 indicators)
  8. Customer and Supplier Fairness (2 indicators)
  9. Business Openness (10 indicators)

**Dependencies**: 001_initial_schema

---

### 003_extraction_tables
**Description**: Creates tables for storing extracted indicators and calculated ESG scores.

**Tables Created**:
- `extracted_indicators` - Stores LLM-extracted indicator values with confidence scores and source citations
- `esg_scores` - Stores calculated ESG scores with transparent methodology

**Indexes Created**:
- Multiple indexes on `extracted_indicators` for efficient querying by company, year, indicator, and validation status
- Indexes on `esg_scores` for score retrieval and filtering

**Dependencies**: 001_initial_schema, 002_brsr_indicators

---

### 004_auth_tables
**Description**: Creates user authentication and API key management tables.

**Tables Created**:
- `users` - User accounts for authentication
- `api_keys` - API keys for programmatic access

**Functions Created**:
- `update_updated_at_column()` - Trigger function to auto-update timestamps

**Triggers Created**:
- Auto-update triggers for `users` and `api_keys` tables

**Data Seeded**:
- Default admin user (username: `admin`, password: `admin123`)
- Default test user (username: `testuser`, password: `user123`)

**⚠️ WARNING**: Change default passwords in production!

**Dependencies**: None

---

## Running Migrations

### Using Docker Compose (Automatic)

Migrations are automatically applied when the PostgreSQL container starts:

```bash
# Start all services (migrations run automatically)
docker-compose up -d

# Check migration logs
docker-compose logs postgres
```

The migrations are mounted to `/docker-entrypoint-initdb.d/` in the PostgreSQL container and run in alphabetical order.

### Manual Migration

To run migrations manually:

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U esg_user -d esg_platform

# Run a specific migration
\i /docker-entrypoint-initdb.d/001_initial_schema.sql
```

### Rollback Migrations

To rollback a migration:

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U esg_user -d esg_platform

# Run the rollback script
\i /docker-entrypoint-initdb.d/004_auth_tables_rollback.sql
```

**⚠️ WARNING**: Rollbacks will delete data! Always backup before rolling back.

---

## Migration Best Practices

### Creating New Migrations

1. **Naming Convention**: Use format `XXX_descriptive_name.sql` where XXX is the next sequential number
2. **Rollback Script**: Always create a corresponding `XXX_descriptive_name_rollback.sql`
3. **Idempotency**: Use `IF NOT EXISTS` and `IF EXISTS` to make migrations idempotent
4. **Comments**: Add clear comments explaining what the migration does
5. **Dependencies**: Document which migrations must run before this one
6. **Testing**: Test both forward and rollback migrations before committing

### Migration Template

```sql
-- Migration XXX: Migration Name
-- Description: Brief description of what this migration does
-- Date: YYYY-MM-DD
-- Author: Your Name

-- Create tables
CREATE TABLE IF NOT EXISTS table_name (
    id SERIAL PRIMARY KEY,
    -- columns
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_name ON table_name(column);

-- Add comments
COMMENT ON TABLE table_name IS 'Description';
```

### Rollback Template

```sql
-- Rollback Migration XXX: Migration Name
-- Description: Reverts changes from migration XXX
-- Date: YYYY-MM-DD
-- Author: Your Name

-- Drop indexes
DROP INDEX IF EXISTS idx_name;

-- Drop tables (in reverse order)
DROP TABLE IF EXISTS table_name CASCADE;
```

---

## Migration Order

Migrations must be run in numerical order:

1. `001_initial_schema.sql` - Base tables
2. `002_brsr_indicators.sql` - BRSR indicators and indexes
3. `003_extraction_tables.sql` - Extraction and scoring tables
4. `004_auth_tables.sql` - Authentication tables

---

## Troubleshooting

### Migration Failed

If a migration fails:

1. Check the PostgreSQL logs: `docker-compose logs postgres`
2. Connect to the database and check the error
3. Fix the migration script
4. Rollback if necessary
5. Restart the PostgreSQL container: `docker-compose restart postgres`

### Duplicate Key Errors

If you see duplicate key errors when re-running migrations:

- Migrations use `IF NOT EXISTS` and `ON CONFLICT DO NOTHING` to be idempotent
- If you still see errors, the migration may have partially completed
- Consider rolling back and re-running

### Index Creation Timeout

If vector index creation times out:

- The HNSW index on embeddings can take time with large datasets
- Consider creating the index `CONCURRENTLY` in production
- Monitor index creation progress: `SELECT * FROM pg_stat_progress_create_index;`

---

## Database Schema Diagram

```
company_catalog
    ├── ingestion_metadata (FK: company_id)
    └── extracted_indicators (FK: company_id)
        └── esg_scores (FK: company_id)

brsr_indicators
    └── extracted_indicators (FK: indicator_id)

document_embeddings (standalone, referenced by object_key)

users
    └── api_keys (FK: user_id)
```

---

## Performance Considerations

### Critical Indexes

1. **Filtered Vector Retrieval**: `idx_doc_emb_company_year` on `document_embeddings(company_name, report_year)`
   - Reduces search space from 40k+ to ~200-500 embeddings per query
   - Essential for extraction service performance

2. **Vector Similarity Search**: `idx_doc_emb_vector` using HNSW
   - Enables fast semantic search with cosine distance
   - Uses halfvec(3072) to support Gemini's 3072-dimensional embeddings

3. **Extraction Queries**: Composite indexes on `extracted_indicators`
   - Speeds up queries by company, year, and indicator
   - Supports efficient filtering by validation status and confidence

### Index Tuning

For production, consider tuning pgvector parameters:

```sql
-- HNSW index parameters
-- m: number of connections per layer (default: 16, higher = better recall, slower build)
-- ef_construction: size of dynamic candidate list (default: 64, higher = better quality, slower build)

CREATE INDEX idx_doc_emb_vector ON document_embeddings 
USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops) 
WITH (m = 32, ef_construction = 128);
```

---

## Backup and Restore

### Backup Database

```bash
# Backup entire database
docker-compose exec postgres pg_dump -U esg_user esg_platform > backup.sql

# Backup specific table
docker-compose exec postgres pg_dump -U esg_user -t brsr_indicators esg_platform > brsr_backup.sql
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U esg_user esg_platform < backup.sql
```

---

## Migration History

| Migration | Date | Description | Status |
|-----------|------|-------------|--------|
| 001 | 2024-01-01 | Initial schema | ✅ Complete |
| 002 | 2024-01-02 | BRSR indicators | ✅ Complete |
| 003 | 2024-01-03 | Extraction tables | ✅ Complete |
| 004 | 2024-01-04 | Authentication | ✅ Complete |

---

## Future Migrations

Planned migrations:

- **005_audit_logs**: Add audit logging for data changes
- **006_caching_tables**: Add tables for caching layer
- **007_notification_tables**: Add tables for notification system
- **008_report_metadata**: Add enhanced report metadata tracking

---

## Support

For issues or questions about migrations:

1. Check the PostgreSQL logs
2. Review the migration comments and documentation
3. Test rollback and re-apply if needed
4. Contact the platform team for assistance
