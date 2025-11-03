# Implementation Plan

- [x] 1. Remove sample data generation scripts
  - Delete `scripts/populate_data.sql` file that creates sample extracted indicators and ESG scores
  - Delete `scripts/populate_missing_data.py` file that generates sample data programmatically
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Create database cleanup script
  - [x] 2.1 Create `scripts/cleanup_sample_data.py` with database connection setup
    - Import required libraries (psycopg2, os, sys)
    - Define database configuration from environment variables
    - Create connection helper function
    - _Requirements: 4.1_
  
  - [x] 2.2 Implement sample data identification function
    - Write SQL query to count extracted_indicators with "Sample:" prefix
    - Write SQL query to count orphaned ESG scores
    - Return dictionary with counts by table
    - _Requirements: 4.1_
  
  - [x] 2.3 Implement sample data deletion functions
    - Write function to delete extracted_indicators with "Sample:" prefix
    - Write function to delete orphaned ESG scores (scores with no indicators)
    - Use database transactions for atomic operations
    - Log number of records deleted
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [x] 2.4 Implement main execution flow
    - Connect to database
    - Identify sample data and display counts
    - Prompt user for confirmation (or add --force flag)
    - Execute deletions in transaction
    - Display summary of deleted records
    - Handle errors with rollback
    - _Requirements: 4.2, 4.3, 4.4_

- [x] 3. Update trigger extraction script
  - [x] 3.1 Add command-line argument parsing
    - Add `--limit` parameter (default: 10) to control batch size
    - Add `--dry-run` parameter to preview without queuing
    - Add `--help` parameter for usage information
    - _Requirements: 3.3_
  
  - [x] 3.2 Update document query function
    - Modify SQL query to include embedding count
    - Add GROUP BY clause for proper aggregation
    - Add parameterized LIMIT clause
    - Return list of document dictionaries with all required fields
    - _Requirements: 3.1_
  
  - [x] 3.3 Enhance RabbitMQ publishing function
    - Add validation to check if queue exists
    - Add error handling for connection failures
    - Add retry logic for transient failures
    - Return boolean success indicator
    - _Requirements: 3.2_
  
  - [x] 3.4 Improve logging and output
    - Log document details (company, year, embedding count)
    - Display summary table of documents to be queued
    - Log successful queue operations
    - Add dry-run mode that shows what would be queued
    - _Requirements: 3.2, 3.4_

- [x] 4. Verify extraction service configuration
  - [x] 4.1 Check extraction service startup and queue connection
    - Review extraction service logs for startup messages
    - Verify queue declaration in logs
    - Verify database connection in logs
    - Document any configuration issues found
    - _Requirements: 5.1, 5.2_
  
  - [x] 4.2 Verify message processing configuration
    - Check that manual acknowledgment is enabled
    - Verify retry logic is configured
    - Verify dead letter queue is configured
    - Check QoS settings (prefetch_count)
    - _Requirements: 5.3, 5.4_
  
  - [x] 4.3 Test extraction service with sample message
    - Manually publish a test message to extraction-tasks queue
    - Monitor extraction service logs for message processing
    - Verify indicator extraction occurs
    - Verify ESG score calculation occurs
    - Verify document status update occurs
    - _Requirements: 5.5_

- [ ] 5. Execute pipeline cleanup and trigger
  - [ ] 5.1 Run cleanup script to remove sample data
    - Execute `scripts/cleanup_sample_data.py`
    - Verify sample indicators are deleted
    - Verify orphaned scores are deleted
    - Document number of records removed
    - _Requirements: 4.2, 4.3_
  
  - [ ] 5.2 Verify database state after cleanup
    - Query database to confirm no sample data remains
    - Query database to confirm real embeddings still exist
    - Query database to get count of documents needing extraction
    - _Requirements: 4.2, 4.3_
  
  - [ ] 5.3 Trigger extraction for existing documents
    - Run `scripts/trigger_extraction.py --limit 5` for initial test batch
    - Monitor RabbitMQ queue to verify messages are published
    - Monitor extraction service logs for message processing
    - Verify indicators are extracted (check database)
    - Verify ESG scores are calculated (check database)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ] 5.4 Validate end-to-end pipeline with actual data
    - Query extracted_indicators table to verify no "Sample:" values
    - Query extracted_indicators to verify actual extracted values exist
    - Query esg_scores to verify scores are calculated
    - Compare before/after counts to confirm pipeline processed documents
    - Document successful processing of at least 5 documents
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 6. Document pipeline operation
  - [ ] 6.1 Create pipeline verification script
    - Create `scripts/verify_pipeline.sh` that checks pipeline health
    - Include database queries for document counts
    - Include RabbitMQ queue status checks
    - Include service health checks
    - Make script executable and add usage documentation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 6.2 Update README with pipeline operation instructions
    - Document how to trigger extraction for new documents
    - Document how to monitor pipeline progress
    - Document how to verify data is not sample data
    - Add troubleshooting section for common issues
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
