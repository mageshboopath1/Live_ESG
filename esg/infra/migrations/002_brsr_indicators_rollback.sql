-- Rollback Migration 002: BRSR Core Indicators
-- Description: Drop BRSR indicators table and related indexes
-- Date: 2024-01-02
-- Author: ESG Platform Team

-- Drop indexes on document_embeddings table
DROP INDEX IF EXISTS idx_doc_emb_vector;
DROP INDEX IF EXISTS idx_doc_emb_object_key;
DROP INDEX IF EXISTS idx_doc_emb_company_year;

-- Drop indexes on brsr_indicators table
DROP INDEX IF EXISTS idx_brsr_code;
DROP INDEX IF EXISTS idx_brsr_pillar;
DROP INDEX IF EXISTS idx_brsr_attribute;

-- Drop brsr_indicators table
DROP TABLE IF EXISTS brsr_indicators CASCADE;
