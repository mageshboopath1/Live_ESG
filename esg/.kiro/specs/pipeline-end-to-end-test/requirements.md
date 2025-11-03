# Requirements Document

## Introduction

This document defines requirements for implementing an end-to-end pipeline testing system that validates the complete data flow from ingestion through embedding to extraction and scoring. The system must support clean slate testing by removing all existing data and processing a fresh dataset through the entire pipeline with proper sequencing and validation.

## Glossary

- **Pipeline System**: The complete data processing workflow consisting of ingestion, embedding, extraction, and scoring services
- **Ingestion Service**: The service that downloads PDF reports from links, uploads to MinIO, and publishes queue messages
- **Embedding Service**: The service that processes PDFs to create vector embeddings and stores them in the database
- **Extraction Service**: The service that extracts BRSR indicators from reports using RAG
- **Scoring Service**: The component within extraction that calculates ESG and pillar scores
- **MinIO**: The object storage system for PDF files
- **RabbitMQ**: The message queue system for inter-service communication
- **PostgreSQL**: The relational database storing metadata, embeddings, and extracted data
- **Embedding Queue**: The RabbitMQ queue for embedding tasks
- **Extraction Queue**: The RabbitMQ queue for extraction tasks

## Requirements

### Requirement 1

**User Story:** As a developer, I want to clean all existing pipeline data, so that I can test the pipeline from a fresh state

#### Acceptance Criteria

1. WHEN the cleanup script is executed, THE Pipeline System SHALL remove all PDF files from MinIO storage
2. WHEN the cleanup script is executed, THE Pipeline System SHALL delete all records from the reports table in PostgreSQL
3. WHEN the cleanup script is executed, THE Pipeline System SHALL delete all records from the companies table in PostgreSQL
4. WHEN the cleanup script is executed, THE Pipeline System SHALL delete all records from the embeddings table in PostgreSQL
5. WHEN the cleanup script is executed, THE Pipeline System SHALL delete all records from the indicator_values table in PostgreSQL
6. WHEN the cleanup script is executed, THE Pipeline System SHALL delete all records from the citations table in PostgreSQL
7. WHEN the cleanup script is executed, THE Pipeline System SHALL purge all messages from the Embedding Queue
8. WHEN the cleanup script is executed, THE Pipeline System SHALL purge all messages from the Extraction Queue

### Requirement 2

**User Story:** As a developer, I want the ingestion service to process reports and publish messages correctly, so that downstream services receive the necessary tasks

#### Acceptance Criteria

1. WHEN the Ingestion Service processes a PDF link, THE Ingestion Service SHALL download the PDF file to local storage
2. WHEN the Ingestion Service downloads a PDF, THE Ingestion Service SHALL upload the PDF to MinIO with a unique object key
3. WHEN the Ingestion Service uploads a PDF to MinIO, THE Ingestion Service SHALL insert company metadata into the companies table
4. WHEN the Ingestion Service uploads a PDF to MinIO, THE Ingestion Service SHALL insert report metadata into the reports table with the MinIO object key
5. WHEN the Ingestion Service inserts report metadata, THE Ingestion Service SHALL publish an embedding task message to the Embedding Queue containing the report ID
6. WHEN the Ingestion Service inserts report metadata, THE Ingestion Service SHALL publish an extraction task message to the Extraction Queue containing the report ID with a delayed delivery
7. IF the PDF download fails, THEN THE Ingestion Service SHALL log the error and continue processing remaining links

### Requirement 3

**User Story:** As a developer, I want the embedding service to process reports before extraction begins, so that the extraction service has the necessary vector data

#### Acceptance Criteria

1. WHEN the Embedding Service receives an embedding task message, THE Embedding Service SHALL retrieve the PDF from MinIO using the report metadata
2. WHEN the Embedding Service retrieves a PDF, THE Embedding Service SHALL extract text content from the PDF
3. WHEN the Embedding Service extracts text, THE Embedding Service SHALL split the text into chunks with appropriate overlap
4. WHEN the Embedding Service creates chunks, THE Embedding Service SHALL generate vector embeddings for each chunk using the gemini-embedding-001 model with 3072 dimensions
5. WHEN the Embedding Service generates embeddings, THE Embedding Service SHALL store embeddings in the embeddings table with report ID and chunk metadata as 3072-dimensional vectors
6. WHEN the Embedding Service completes processing, THE Embedding Service SHALL acknowledge the message from the Embedding Queue
7. IF embedding generation fails, THEN THE Embedding Service SHALL log the error and reject the message for retry

### Requirement 4

**User Story:** As a developer, I want the extraction service to wait until embeddings are complete, so that it can successfully retrieve relevant context

#### Acceptance Criteria

1. WHEN the Extraction Service receives an extraction task message, THE Extraction Service SHALL verify that embeddings exist for the report ID
2. IF embeddings do not exist for the report, THEN THE Extraction Service SHALL reject the message and requeue it with a delay
3. WHEN embeddings exist for the report, THE Extraction Service SHALL retrieve the report metadata from the reports table
4. WHEN the Extraction Service retrieves report metadata, THE Extraction Service SHALL process each BRSR indicator sequentially
5. WHEN the Extraction Service processes an indicator, THE Extraction Service SHALL use the filtered retriever with gemini-embedding-001 model (3072 dimensions) to fetch relevant chunks from the embeddings table
6. WHEN the Extraction Service retrieves chunks, THE Extraction Service SHALL invoke the extraction chain to extract indicator values
7. WHEN the Extraction Service extracts indicator values, THE Extraction Service SHALL store the values in the indicator_values table with citations
8. WHEN the Extraction Service stores indicator values, THE Extraction Service SHALL store citation information in the citations table

### Requirement 5

**User Story:** As a developer, I want the scoring service to calculate ESG scores after extraction, so that I can validate the complete pipeline output

#### Acceptance Criteria

1. WHEN all indicators are extracted for a report, THE Scoring Service SHALL retrieve all indicator values for the report ID
2. WHEN the Scoring Service retrieves indicator values, THE Scoring Service SHALL calculate pillar scores for Environmental, Social, and Governance pillars
3. WHEN the Scoring Service calculates pillar scores, THE Scoring Service SHALL calculate the overall ESG score as a weighted average
4. WHEN the Scoring Service calculates scores, THE Scoring Service SHALL store pillar scores in the database with the report ID
5. WHEN the Scoring Service calculates scores, THE Scoring Service SHALL store the ESG score in the database with the report ID

### Requirement 6

**User Story:** As a developer, I want to execute and monitor the entire pipeline, so that I can verify each stage completes successfully

#### Acceptance Criteria

1. THE Pipeline System SHALL provide a test script that executes all pipeline stages in sequence
2. WHEN the test script runs, THE Pipeline System SHALL display progress information for each pipeline stage
3. WHEN the test script runs, THE Pipeline System SHALL verify that each stage completes before proceeding to the next
4. WHEN the embedding stage runs, THE Pipeline System SHALL monitor the Embedding Queue until all messages are processed
5. WHEN the extraction stage runs, THE Pipeline System SHALL monitor the Extraction Queue until all messages are processed
6. WHEN the pipeline completes, THE Pipeline System SHALL display summary statistics including counts of processed reports, embeddings, and extracted indicators
7. IF any stage fails, THEN THE Pipeline System SHALL display error information and halt execution
