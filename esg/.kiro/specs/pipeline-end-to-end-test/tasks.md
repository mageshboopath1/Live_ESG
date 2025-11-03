# Implementation Plan

- [x] 1. Update database schema for 3072-dimensional embeddings
  - Create migration script to alter document_embeddings table from vector(768) to vector(3072)
  - Add backup of existing embeddings table before migration
  - Recreate vector indexes with appropriate parameters for 3072 dimensions
  - _Requirements: 3.4, 5.5_

- [x] 2. Update embedding service to use gemini-embedding-001 with 3072 dimensions
  - [x] 2.1 Update embedder.py to use gemini-embedding-001 model
    - Modify GoogleGenerativeAIEmbeddings initialization to use "models/gemini-embedding-001"
    - Configure output_dimensionality to 3072 using EmbedContentConfig
    - Update batch processing to handle 3072-dimensional vectors
    - _Requirements: 3.4_
  
  - [x] 2.2 Update main.py embedding worker
    - Update embedding generation to use new embedder configuration
    - Ensure database inserts handle 3072-dimensional vectors
    - Add validation to verify embedding dimensions before storage
    - _Requirements: 3.4, 3.5_

- [x] 3. Update extraction service to use gemini-embedding-001 with 3072 dimensions
  - [x] 3.1 Update filtered_retriever.py
    - Modify FilteredPGVectorRetriever to use "models/gemini-embedding-001"
    - Configure embedding function with 3072 dimensions
    - Update vector similarity search to work with 3072-dimensional embeddings
    - _Requirements: 5.5_
  
  - [x] 3.2 Add embedding existence check in extraction worker
    - Create check_embeddings_exist() function to query document_embeddings table
    - Modify callback() to check for embeddings before processing
    - Implement requeue logic with delay when embeddings are not ready
    - Add maximum requeue attempts (10) before sending to DLQ
    - _Requirements: 4.1, 4.2_

- [x] 4. Create comprehensive cleanup script
  - [x] 4.1 Implement MinIO cleanup function
    - Connect to MinIO using boto3 client
    - List all objects in esg-reports bucket
    - Delete all objects recursively
    - Return count of deleted objects
    - _Requirements: 1.1_
  
  - [x] 4.2 Implement database cleanup functions
    - Create cleanup function for document_embeddings table
    - Create cleanup function for extracted_indicators table
    - Create cleanup function for esg_scores table
    - Create cleanup function for ingestion_metadata table
    - Create cleanup function for citations table (if exists)
    - Execute deletions in correct order to respect foreign key constraints
    - Return counts of deleted records per table
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 4.3 Implement RabbitMQ queue purging
    - Connect to RabbitMQ using pika
    - Purge embedding-tasks queue
    - Purge extraction-tasks queue
    - Return count of purged messages per queue
    - _Requirements: 1.7, 1.8_
  
  - [x] 4.4 Create main cleanup orchestration
    - Implement cleanup_all() function that calls all cleanup functions
    - Add confirmation prompt before executing cleanup
    - Add --force flag to skip confirmation
    - Display summary of what will be deleted before confirmation
    - Display summary of deleted items after completion
    - Add error handling with rollback for database operations
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

- [x] 5. Update ingestion service for proper queue publishing
  - [x] 5.1 Add database metadata insertion
    - Ensure company_catalog entries exist before processing reports
    - Insert records into ingestion_metadata table with MinIO object keys
    - Store file_path as MinIO object key for reference
    - _Requirements: 2.3, 2.4_
  
  - [x] 5.2 Update queue message publishing
    - Publish JSON messages to embedding-tasks queue with object_key, company_name, report_year
    - Publish JSON messages to extraction-tasks queue with same structure
    - Add delay mechanism for extraction-tasks messages (5 minutes)
    - Ensure both messages are published only after successful MinIO upload
    - _Requirements: 2.5, 2.6_

- [x] 6. Create pipeline orchestrator script
  - [x] 6.1 Implement queue monitoring functions
    - Create get_queue_message_count() to query RabbitMQ queue depth
    - Create monitor_queue() function with timeout and check interval
    - Implement logic to verify queue stays empty for 30 seconds before considering complete
    - Add progress logging with message counts and elapsed time
    - _Requirements: 6.4, 6.5_
  
  - [x] 6.2 Implement pipeline stage orchestration
    - Create run_cleanup_stage() to execute cleanup and verify
    - Create run_ingestion_stage() to trigger ingestion for specified companies
    - Create monitor_embedding_stage() to wait for embedding queue completion
    - Create monitor_extraction_stage() to wait for extraction queue completion
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 6.3 Implement validation functions
    - Create check_embeddings_count() to verify embeddings were created
    - Create check_embedding_dimensions() to verify all embeddings are 3072 dimensions
    - Create check_indicators_count() to verify indicators were extracted
    - Create check_scores_count() to verify ESG scores were calculated
    - Create check_referential_integrity() to verify no orphaned records
    - Create validate_pipeline_output() to run all validation checks
    - _Requirements: 6.6_
  
  - [x] 6.4 Create main pipeline execution function
    - Implement run_full_pipeline() that orchestrates all stages
    - Add command-line arguments for company selection and limits
    - Display progress information for each stage
    - Display summary statistics at completion
    - Handle errors and provide clear error messages
    - _Requirements: 6.1, 6.2, 6.3, 6.6, 6.7_

- [x] 7. Add configuration and environment setup
  - Create configuration file or environment variables for pipeline settings
  - Add EMBEDDING_MODEL, EMBEDDING_DIMENSIONS configuration
  - Add queue monitoring timeouts and check intervals
  - Add retry limits and delay settings
  - Document all configuration options in README
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Create end-to-end test execution script
  - Create test_pipeline_e2e.py script that uses the orchestrator
  - Add option to test with limited number of companies (e.g., 3-5)
  - Add option to skip cleanup for incremental testing
  - Add detailed logging of each stage
  - Generate test report with timing and success metrics
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
