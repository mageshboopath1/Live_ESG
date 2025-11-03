# Requirements Document

## Introduction

This document outlines the requirements for fixing the ingestion → embedding → extraction → scoring pipeline to work with actual data instead of sample/mock data. The system currently has scripts that populate sample data, bypassing the actual extraction and scoring processes. This fix will ensure the complete pipeline processes real BRSR reports from ingestion through to ESG score calculation.

## Glossary

- **Pipeline**: The complete data processing flow from ingestion through embedding, extraction, and scoring
- **Ingestion Service**: Service that downloads BRSR reports from NSE and stores them in MinIO
- **Embeddings Service**: Service that processes PDFs, creates text chunks, generates embeddings, and queues documents for extraction
- **Extraction Service**: Service that extracts BRSR indicators from documents using LLM and stores results
- **Sample Data**: Mock/fake data created by scripts instead of actual extracted data
- **Extraction Queue**: RabbitMQ queue (extraction-tasks) that triggers indicator extraction
- **Object Key**: MinIO path identifier for a document (e.g., "RELIANCE/2024_BRSR.pdf")

## Requirements

### Requirement 1: Remove Sample Data Scripts

**User Story:** As a system administrator, I want to remove all sample data generation scripts, so that the system only contains real extracted data.

#### Acceptance Criteria

1. WHEN the system is deployed, THE System SHALL NOT include any scripts that generate sample extracted indicators
2. WHEN the system is deployed, THE System SHALL NOT include any scripts that generate sample ESG scores
3. THE System SHALL remove the populate_data.sql script from the scripts directory
4. THE System SHALL remove the populate_missing_data.py script from the scripts directory

### Requirement 2: Verify Pipeline Data Flow

**User Story:** As a developer, I want to verify that the complete pipeline processes actual documents, so that I can ensure data integrity.

#### Acceptance Criteria

1. WHEN a document is ingested, THE Ingestion Service SHALL upload the document to MinIO with a valid object key
2. WHEN a document is uploaded to MinIO, THE Ingestion Service SHALL publish the object key to the embedding-tasks queue
3. WHEN the Embeddings Service processes a document, THE Embeddings Service SHALL publish the object key to the extraction-tasks queue
4. WHEN the Extraction Service processes a document, THE Extraction Service SHALL extract actual indicators using the LLM
5. WHEN indicators are extracted, THE Extraction Service SHALL calculate and store actual ESG scores

### Requirement 3: Trigger Extraction for Existing Embeddings

**User Story:** As a system administrator, I want to trigger extraction for documents that already have embeddings, so that existing data can be processed through the complete pipeline.

#### Acceptance Criteria

1. THE System SHALL provide a script that identifies documents with embeddings but no extractions
2. WHEN the trigger script is executed, THE Script SHALL publish object keys to the extraction-tasks queue for unprocessed documents
3. THE Script SHALL limit the initial batch to a configurable number of documents to prevent queue overload
4. THE Script SHALL log the number of documents queued for extraction

### Requirement 4: Clean Existing Sample Data

**User Story:** As a system administrator, I want to remove existing sample data from the database, so that only real extracted data remains.

#### Acceptance Criteria

1. THE System SHALL provide a script that identifies sample data in the extracted_indicators table
2. WHEN sample data is identified, THE Script SHALL delete records where extracted_value contains "Sample:"
3. WHEN sample extracted indicators are deleted, THE Script SHALL delete associated ESG scores that were calculated from sample data
4. THE Script SHALL log the number of records deleted

### Requirement 5: Verify Extraction Service Configuration

**User Story:** As a developer, I want to verify the extraction service is properly configured, so that it can process documents from the queue.

#### Acceptance Criteria

1. THE Extraction Service SHALL connect to the extraction-tasks queue on startup
2. WHEN the extraction service starts, THE Service SHALL log its configuration including database, RabbitMQ, and queue name
3. THE Extraction Service SHALL process messages from the extraction-tasks queue with manual acknowledgment
4. WHEN extraction fails, THE Extraction Service SHALL requeue messages up to the configured retry limit
5. THE Extraction Service SHALL update document status to SUCCESS when extraction completes successfully
