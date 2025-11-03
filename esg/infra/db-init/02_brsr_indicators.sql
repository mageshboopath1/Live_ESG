-- Migration: Create BRSR Core indicators table and indexes
-- This table stores the standardized BRSR Core indicator definitions

CREATE TABLE IF NOT EXISTS brsr_indicators (
    id SERIAL PRIMARY KEY,
    indicator_code TEXT NOT NULL UNIQUE,
    attribute_number INT NOT NULL CHECK (attribute_number >= 1 AND attribute_number <= 9),
    parameter_name TEXT NOT NULL,
    measurement_unit TEXT,
    description TEXT,
    pillar TEXT NOT NULL CHECK (pillar IN ('E', 'S', 'G')),
    weight DECIMAL(5,4) NOT NULL DEFAULT 1.0,
    data_assurance_approach TEXT,
    brsr_reference TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index on attribute_number for efficient filtering
CREATE INDEX IF NOT EXISTS idx_brsr_attribute ON brsr_indicators(attribute_number);

-- Create index on pillar for ESG score calculations
CREATE INDEX IF NOT EXISTS idx_brsr_pillar ON brsr_indicators(pillar);

-- Add composite index on (company_name, report_year) to document_embeddings table
-- This is CRITICAL for filtered vector retrieval performance
CREATE INDEX IF NOT EXISTS idx_doc_emb_company_year ON document_embeddings(company_name, report_year);

-- Add index on object_key for document lookups
CREATE INDEX IF NOT EXISTS idx_doc_emb_object_key ON document_embeddings(object_key);

-- Add pgvector HNSW index on embedding column with cosine distance
-- Note: pgvector has a 2000 dimension limit for vector type indexes
-- Since gemini-embedding-001 produces 3072-dimensional vectors, we cannot index the vector column directly
-- Solution: Cast to halfvec (half-precision float16) which supports up to 4000 dimensions
-- This provides efficient similarity search with minimal accuracy loss
CREATE INDEX IF NOT EXISTS idx_doc_emb_vector ON document_embeddings 
USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Add created_at timestamp to document_embeddings if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'document_embeddings' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE document_embeddings ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
    END IF;
END $$;

COMMENT ON TABLE brsr_indicators IS 'BRSR Core indicator definitions based on SEBI framework with 9 attributes';
COMMENT ON COLUMN brsr_indicators.indicator_code IS 'Unique identifier for the indicator (e.g., GHG_SCOPE1_TOTAL)';
COMMENT ON COLUMN brsr_indicators.attribute_number IS 'BRSR Core attribute number (1-9)';
COMMENT ON COLUMN brsr_indicators.pillar IS 'ESG pillar: E (Environmental), S (Social), G (Governance)';
COMMENT ON COLUMN brsr_indicators.weight IS 'Weight for score calculation (0.0-1.0)';
