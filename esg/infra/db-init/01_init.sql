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

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    object_key TEXT,
    company_name TEXT,
    report_year INT,
    page_number INT,
    chunk_index INTEGER,
    embedding VECTOR(3072),
    chunk_text TEXT
);
