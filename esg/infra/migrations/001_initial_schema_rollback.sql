-- Rollback Migration 001: Initial Schema
-- Description: Drop base tables for company catalog, ingestion metadata, and document embeddings
-- Date: 2024-01-01
-- Author: ESG Platform Team

-- Drop tables in reverse order of creation (respecting foreign key dependencies)
DROP TABLE IF EXISTS document_embeddings CASCADE;
DROP TABLE IF EXISTS ingestion_metadata CASCADE;
DROP TABLE IF EXISTS company_catalog CASCADE;

-- Drop extension (only if no other tables use it)
-- Note: Commented out to avoid breaking other migrations that may depend on vector extension
-- DROP EXTENSION IF EXISTS vector CASCADE;
