-- Migration 003: Extraction Tables
-- Description: Create tables for extracted indicators and ESG scores
-- Date: 2024-01-03
-- Author: ESG Platform Team

-- Create extracted_indicators table
CREATE TABLE IF NOT EXISTS extracted_indicators (
    id SERIAL PRIMARY KEY,
    object_key TEXT NOT NULL,
    company_id INT REFERENCES company_catalog(id),
    report_year INT NOT NULL,
    indicator_id INT REFERENCES brsr_indicators(id),
    extracted_value TEXT NOT NULL,
    numeric_value DECIMAL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    validation_status TEXT CHECK (validation_status IN ('valid', 'invalid', 'pending')) DEFAULT 'pending',
    source_pages INT[],
    source_chunk_ids INT[],
    extracted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(object_key, indicator_id)
);

-- Create esg_scores table
CREATE TABLE IF NOT EXISTS esg_scores (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES company_catalog(id),
    report_year INT NOT NULL,
    environmental_score DECIMAL(5,2),
    social_score DECIMAL(5,2),
    governance_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    calculation_metadata JSONB,
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, report_year)
);

-- Create indexes for efficient querying on extracted_indicators
CREATE INDEX IF NOT EXISTS idx_extracted_object_key ON extracted_indicators(object_key);
CREATE INDEX IF NOT EXISTS idx_extracted_company_id ON extracted_indicators(company_id);
CREATE INDEX IF NOT EXISTS idx_extracted_indicator_id ON extracted_indicators(indicator_id);
CREATE INDEX IF NOT EXISTS idx_extracted_report_year ON extracted_indicators(report_year);
CREATE INDEX IF NOT EXISTS idx_extracted_validation ON extracted_indicators(validation_status);
CREATE INDEX IF NOT EXISTS idx_extracted_confidence ON extracted_indicators(confidence_score);

-- Create composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_extracted_company_year ON extracted_indicators(company_id, report_year);

-- Create indexes for efficient querying on esg_scores
CREATE INDEX IF NOT EXISTS idx_scores_company_id ON esg_scores(company_id);
CREATE INDEX IF NOT EXISTS idx_scores_report_year ON esg_scores(report_year);
CREATE INDEX IF NOT EXISTS idx_scores_overall ON esg_scores(overall_score);

-- Add comments for documentation
COMMENT ON TABLE extracted_indicators IS 'Stores ESG indicators extracted from documents using LLM-based extraction with LangChain and Google GenAI';
COMMENT ON TABLE esg_scores IS 'Stores calculated ESG scores aggregated from extracted indicators with transparent methodology';

COMMENT ON COLUMN extracted_indicators.object_key IS 'MinIO object key referencing the source document';
COMMENT ON COLUMN extracted_indicators.extracted_value IS 'Raw text value extracted by LLM';
COMMENT ON COLUMN extracted_indicators.numeric_value IS 'Parsed numeric value if applicable';
COMMENT ON COLUMN extracted_indicators.confidence_score IS 'LLM confidence score (0.0-1.0) indicating extraction reliability';
COMMENT ON COLUMN extracted_indicators.validation_status IS 'Validation status: valid (passed validation), invalid (failed validation), pending (not yet validated)';
COMMENT ON COLUMN extracted_indicators.source_pages IS 'Array of page numbers where indicator was found in the source document';
COMMENT ON COLUMN extracted_indicators.source_chunk_ids IS 'Array of chunk IDs from document_embeddings table used for extraction';

COMMENT ON COLUMN esg_scores.environmental_score IS 'Aggregated Environmental pillar score (0-100)';
COMMENT ON COLUMN esg_scores.social_score IS 'Aggregated Social pillar score (0-100)';
COMMENT ON COLUMN esg_scores.governance_score IS 'Aggregated Governance pillar score (0-100)';
COMMENT ON COLUMN esg_scores.overall_score IS 'Overall ESG score calculated from pillar scores with configurable weights';
COMMENT ON COLUMN esg_scores.calculation_metadata IS 'JSON containing weights, methodology, indicator contributions, and source citations for transparency';
