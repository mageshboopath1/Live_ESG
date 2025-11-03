-- Migration 001: Initial Schema
-- Description: Create base tables for company catalog, ingestion metadata, and document embeddings
-- Date: 2024-01-01
-- Author: ESG Platform Team

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create company_catalog table
CREATE TABLE IF NOT EXISTS company_catalog (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    industry TEXT,
    symbol TEXT NOT NULL,
    series TEXT,
    isin_code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, isin_code)
);

-- Create ingestion_metadata table
CREATE TABLE IF NOT EXISTS ingestion_metadata (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES company_catalog(id),
    source TEXT NOT NULL, -- NSE, MCA, CPCB, SPCB, NEWS
    file_path TEXT NOT NULL, -- where in MinIO
    file_type TEXT NOT NULL, -- pdf, csv, json
    ingested_at TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'SUCCESS',
    UNIQUE(company_id, source, file_path)
);

-- Create document_embeddings table
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    object_key TEXT NOT NULL,
    company_name TEXT NOT NULL,
    report_year INT NOT NULL,
    page_number INT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(3072),
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE company_catalog IS 'Stores company information from NSE NIFTY 50';
COMMENT ON TABLE ingestion_metadata IS 'Tracks document ingestion status and metadata';
COMMENT ON TABLE document_embeddings IS 'Stores document text chunks with vector embeddings for semantic search';
COMMENT ON COLUMN document_embeddings.embedding IS 'Vector embedding generated using Google Gemini (gemini-embedding-001) - 3072 dimensions';
COMMENT ON COLUMN document_embeddings.object_key IS 'MinIO object key in format: company_name/year_reporttype.pdf';
