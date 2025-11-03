-- Migration 005 Rollback: Revert Embedding Dimensions Update
-- Description: Rollback document_embeddings table from vector(3072) to vector(768)
-- Date: 2024-01-05
-- Author: ESG Platform Team

-- Step 1: Drop the current document_embeddings table with 3072 dimensions
DROP TABLE IF EXISTS document_embeddings CASCADE;

-- Step 2: Restore from backup if it exists
CREATE TABLE document_embeddings AS 
SELECT * FROM document_embeddings_backup;

-- Step 3: Add primary key constraint back
ALTER TABLE document_embeddings ADD PRIMARY KEY (id);

-- Step 4: Recreate unique constraint
ALTER TABLE document_embeddings ADD CONSTRAINT document_embeddings_object_key_chunk_index_key 
UNIQUE (object_key, chunk_index);

-- Step 5: Recreate indexes

-- Index on (company_name, report_year)
CREATE INDEX idx_doc_emb_company_year ON document_embeddings(company_name, report_year);

-- Index on object_key
CREATE INDEX idx_doc_emb_object_key ON document_embeddings(object_key);

-- Vector index (assuming 768 dimensions in backup)
-- Note: Adjust the dimension if your backup has different dimensions
CREATE INDEX idx_doc_emb_vector ON document_embeddings 
USING hnsw ((embedding::halfvec(768)) halfvec_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Step 6: Restore comments
COMMENT ON TABLE document_embeddings IS 'Stores document text chunks with vector embeddings for semantic search';
COMMENT ON COLUMN document_embeddings.embedding IS 'Vector embedding (768 dimensions)';

-- Step 7: Drop the backup table
DROP TABLE IF EXISTS document_embeddings_backup;

-- Note: This rollback assumes the backup table exists and contains valid data
-- If the backup doesn't exist, you will need to restore from a database backup

