-- Migration 005: Update Embedding Dimensions
-- Description: Update document_embeddings table from vector(768) to vector(3072) for gemini-embedding-001
-- Date: 2024-01-05
-- Author: ESG Platform Team
-- Requirements: 3.4, 5.5

-- Step 1: Create backup table with existing embeddings
CREATE TABLE IF NOT EXISTS document_embeddings_backup AS 
SELECT * FROM document_embeddings;

-- Add comment to backup table
COMMENT ON TABLE document_embeddings_backup IS 'Backup of document_embeddings before migration to 3072 dimensions';

-- Step 2: Drop existing vector index (if it exists)
DROP INDEX IF EXISTS idx_doc_emb_vector;

-- Step 3: Drop the document_embeddings table (CASCADE to handle dependencies)
DROP TABLE IF EXISTS document_embeddings CASCADE;

-- Step 4: Recreate document_embeddings table with 3072 dimensions
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    object_key TEXT NOT NULL,
    company_name TEXT NOT NULL,
    report_year INT NOT NULL,
    page_number INT,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(3072) NOT NULL,
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(object_key, chunk_index)
);

-- Step 5: Recreate indexes for efficient querying

-- Index on (company_name, report_year) - CRITICAL for filtered vector retrieval
CREATE INDEX idx_doc_emb_company_year ON document_embeddings(company_name, report_year);

-- Index on object_key for document lookups
CREATE INDEX idx_doc_emb_object_key ON document_embeddings(object_key);

-- Step 6: Create HNSW vector index for efficient similarity search
-- Using halfvec for 3072 dimensions (supports up to 4000 dimensions)
-- HNSW parameters:
--   m = 16: Number of connections per layer (higher = better recall, more memory)
--   ef_construction = 64: Size of dynamic candidate list (higher = better index quality, slower build)
CREATE INDEX idx_doc_emb_vector ON document_embeddings 
USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Step 7: Add table and column comments
COMMENT ON TABLE document_embeddings IS 'Stores document text chunks with 3072-dimensional vector embeddings for semantic search using gemini-embedding-001';
COMMENT ON COLUMN document_embeddings.id IS 'Primary key';
COMMENT ON COLUMN document_embeddings.object_key IS 'MinIO object key in format: company_name/year_reporttype.pdf';
COMMENT ON COLUMN document_embeddings.company_name IS 'Company name for filtering';
COMMENT ON COLUMN document_embeddings.report_year IS 'Report year for filtering';
COMMENT ON COLUMN document_embeddings.page_number IS 'Page number in source document';
COMMENT ON COLUMN document_embeddings.chunk_index IS 'Sequential chunk index within document';
COMMENT ON COLUMN document_embeddings.embedding IS '3072-dimensional vector embedding generated using Google Gemini gemini-embedding-001 model';
COMMENT ON COLUMN document_embeddings.chunk_text IS 'Text content of the chunk';
COMMENT ON COLUMN document_embeddings.created_at IS 'Timestamp when embedding was created';

-- Step 8: Grant appropriate permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON document_embeddings TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE document_embeddings_id_seq TO your_app_user;

