# Embedding Dimensions Migration Guide

## Overview

This migration updates the `document_embeddings` table from 768-dimensional vectors to 3072-dimensional vectors to support the Google Gemini `gemini-embedding-001` model.

## Requirements

- **Requirements**: 3.4, 5.5 from pipeline-end-to-end-test spec
- **Model**: gemini-embedding-001 (3072 dimensions)
- **Database**: PostgreSQL with pgvector extension

## Migration Files

1. **005_update_embedding_dimensions.sql** - Forward migration script
2. **005_update_embedding_dimensions_rollback.sql** - Rollback script
3. **migrate_embeddings_to_3072.sh** - Automated migration script with safety checks
4. **verify_embedding_dimensions.sh** - Verification script to check current state

## Pre-Migration Checklist

- [ ] Backup your database
- [ ] Stop all services that write to document_embeddings (embedding service, extraction service)
- [ ] Verify database connection parameters
- [ ] Review current embedding count
- [ ] Ensure sufficient disk space for backup table

## Migration Steps

### Option 1: Using the Automated Script (Recommended)

```bash
# 1. Verify current state
cd infra/migrations
./verify_embedding_dimensions.sh

# 2. Run migration (with confirmation prompt)
./migrate_embeddings_to_3072.sh

# 3. Or run without confirmation (use with caution)
./migrate_embeddings_to_3072.sh --force

# 4. Verify migration completed successfully
./verify_embedding_dimensions.sh
```

### Option 2: Using psql Directly

```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export POSTGRES_DB=moz
export POSTGRES_USER=drfitz
export POSTGRES_PASSWORD=h4i1hydr4

# Run migration
psql -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER -d $POSTGRES_DB \
  -f infra/migrations/005_update_embedding_dimensions.sql
```

### Option 3: Using the migrate.sh Script

```bash
cd infra/migrations
./migrate.sh 005
```

## What the Migration Does

1. **Creates Backup**: Creates `document_embeddings_backup` table with all existing data
2. **Drops Old Table**: Removes the existing `document_embeddings` table and its indexes
3. **Creates New Table**: Recreates table with `VECTOR(3072)` type
4. **Recreates Indexes**: 
   - `idx_doc_emb_company_year` - For filtered retrieval
   - `idx_doc_emb_object_key` - For document lookups
   - `idx_doc_emb_vector` - HNSW index for vector similarity search (using halfvec for 3072 dimensions)
5. **Adds Constraints**: Unique constraint on (object_key, chunk_index)
6. **Updates Comments**: Documents the new 3072-dimensional embeddings

## Index Configuration

The migration creates an HNSW (Hierarchical Navigable Small World) index optimized for 3072 dimensions:

```sql
CREATE INDEX idx_doc_emb_vector ON document_embeddings 
USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

**Parameters:**
- `m = 16`: Number of connections per layer (balance between recall and memory)
- `ef_construction = 64`: Size of dynamic candidate list during index build
- `halfvec(3072)`: Uses half-precision floats to support up to 4000 dimensions

## Post-Migration Steps

1. **Verify Migration**:
   ```bash
   ./verify_embedding_dimensions.sh
   ```

2. **Update Services**:
   - Update embedding service to use gemini-embedding-001 with 3072 dimensions
   - Update extraction service retriever to use 3072 dimensions
   - Restart all services

3. **Regenerate Embeddings**:
   - All existing embeddings are deleted during migration
   - Re-run embedding generation for all documents
   - Monitor embedding queue until complete

4. **Clean Up Backup** (after verification):
   ```sql
   DROP TABLE document_embeddings_backup;
   ```

## Rollback

If you need to rollback the migration:

```bash
# Using the rollback script
psql -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER -d $POSTGRES_DB \
  -f infra/migrations/005_update_embedding_dimensions_rollback.sql
```

**Note**: Rollback requires the backup table to exist. If you've dropped it, you'll need to restore from a database backup.

## Verification Queries

### Check Current Dimensions
```sql
SELECT atttypmod - 4 as dimensions
FROM pg_attribute
WHERE attrelid = 'document_embeddings'::regclass
AND attname = 'embedding';
```

### Check Embedding Count
```sql
SELECT COUNT(*) FROM document_embeddings;
```

### Check Indexes
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'document_embeddings';
```

### Verify Sample Embedding
```sql
SELECT 
    id,
    object_key,
    company_name,
    report_year,
    array_length(embedding::float[], 1) as actual_dimensions
FROM document_embeddings
LIMIT 1;
```

## Troubleshooting

### Migration Fails with "relation does not exist"
- The table may not exist yet. This is normal for fresh installations.
- The migration will create the table with 3072 dimensions.

### Migration Fails with "insufficient disk space"
- The backup table requires space equal to the current table size.
- Free up disk space or skip backup (not recommended).

### Indexes Take Too Long to Build
- HNSW index building is CPU-intensive for large datasets.
- Consider building indexes after data is loaded.
- Adjust `ef_construction` parameter (lower = faster, less accurate).

### Vector Search Performance Issues
- Ensure HNSW index is created and being used.
- Check query plans with `EXPLAIN ANALYZE`.
- Consider adjusting `m` and `ef_construction` parameters.

## Performance Impact

- **Migration Time**: ~1-5 minutes for empty table, longer with data
- **Index Build Time**: Depends on data size (can be hours for millions of vectors)
- **Disk Space**: Requires 2x current table size during migration (for backup)
- **Downtime**: Services must be stopped during migration

## Related Files

- `services/embeddings/src/embedder.py` - Update to use gemini-embedding-001
- `services/extraction/src/retrieval/filtered_retriever.py` - Update to use 3072 dimensions
- `.kiro/specs/pipeline-end-to-end-test/design.md` - Design documentation

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Google Gemini Embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
- [HNSW Index Parameters](https://github.com/pgvector/pgvector#hnsw)

