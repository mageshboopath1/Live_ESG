# Design Document: Pipeline Data Fix

## Overview

This design addresses the issue of sample data in the ESG platform by removing sample data generation scripts, cleaning existing sample data from the database, and ensuring the complete pipeline (ingestion → embedding → extraction → scoring) processes actual BRSR reports. The solution focuses on:

1. Removing sample data scripts
2. Creating a cleanup script to remove existing sample data
3. Updating the trigger script to queue actual documents for extraction
4. Verifying the extraction service processes documents correctly

## Architecture

### Current State

```
Ingestion Service → MinIO → Embeddings Service → extraction-tasks queue
                                                         ↓
                                                  [BYPASSED]
                                                         ↓
Sample Data Scripts → Database (extracted_indicators, esg_scores)
```

### Target State

```
Ingestion Service → MinIO → Embeddings Service → extraction-tasks queue
                                                         ↓
                                                  Extraction Service
                                                         ↓
                                                  Database (actual data)
```

## Components and Interfaces

### 1. Sample Data Removal

**Files to Remove:**
- `scripts/populate_data.sql` - Creates sample extracted indicators and ESG scores
- `scripts/populate_missing_data.py` - Python script that generates sample data

**Action:** Delete these files completely from the repository.

### 2. Database Cleanup Script

**File:** `scripts/cleanup_sample_data.py`

**Purpose:** Remove existing sample data from the database

**Interface:**
```python
def identify_sample_data(conn) -> Dict[str, int]:
    """
    Identify sample data in the database.
    Returns count of sample records by table.
    """
    
def delete_sample_indicators(conn) -> int:
    """
    Delete extracted indicators with 'Sample:' prefix.
    Returns number of deleted records.
    """
    
def delete_orphaned_scores(conn) -> int:
    """
    Delete ESG scores that have no associated extracted indicators.
    Returns number of deleted records.
    """
```

**Database Queries:**
```sql
-- Identify sample indicators
SELECT COUNT(*) FROM extracted_indicators 
WHERE extracted_value LIKE 'Sample:%';

-- Delete sample indicators
DELETE FROM extracted_indicators 
WHERE extracted_value LIKE 'Sample:%';

-- Delete orphaned scores (scores with no indicators)
DELETE FROM esg_scores es
WHERE NOT EXISTS (
    SELECT 1 FROM extracted_indicators ei 
    WHERE ei.company_id = es.company_id 
    AND ei.report_year = es.report_year
);
```

### 3. Enhanced Trigger Script

**File:** `scripts/trigger_extraction.py` (update existing)

**Purpose:** Queue documents with embeddings for extraction

**Changes:**
- Add `--limit` parameter to control batch size (default: 10)
- Add `--dry-run` parameter to preview without queuing
- Improve logging to show document details
- Add validation to ensure extraction queue exists

**Interface:**
```python
def get_documents_needing_extraction(conn, limit: int) -> List[Dict]:
    """
    Get documents that have embeddings but no extractions.
    
    Args:
        conn: Database connection
        limit: Maximum number of documents to return
        
    Returns:
        List of document records with object_key, company_id, etc.
    """
    
def send_extraction_task(channel, document: Dict) -> bool:
    """
    Send extraction task to RabbitMQ queue.
    
    Args:
        channel: RabbitMQ channel
        document: Document record with object_key, company_id, etc.
        
    Returns:
        True if message was published successfully
    """
```

**Updated Query:**
```sql
SELECT DISTINCT 
    de.object_key,
    cc.id as company_id,
    cc.company_name,
    cc.symbol,
    de.report_year,
    COUNT(DISTINCT de.id) as embedding_count
FROM document_embeddings de
JOIN company_catalog cc ON de.company_name = cc.symbol
WHERE NOT EXISTS (
    SELECT 1 FROM extracted_indicators ei 
    WHERE ei.object_key = de.object_key
)
GROUP BY de.object_key, cc.id, cc.company_name, cc.symbol, de.report_year
ORDER BY cc.company_name, de.report_year
LIMIT %s
```

### 4. Extraction Service Verification

**File:** `services/extraction/main.py` (no changes needed)

**Verification Points:**
- Service connects to RabbitMQ on startup
- Service declares extraction-tasks queue
- Service processes messages with manual acknowledgment
- Service extracts indicators using LLM
- Service calculates and stores ESG scores
- Service updates document status

**Monitoring:**
```bash
# Check extraction service logs
docker logs -f esg-extraction

# Check queue status
docker exec rabbitmq rabbitmqctl list_queues name messages consumers
```

## Data Models

### Document Processing Status

```
document_embeddings (existing)
├── object_key: VARCHAR (e.g., "RELIANCE/2024_BRSR.pdf")
├── company_name: VARCHAR
├── report_year: INTEGER
├── embedding: VECTOR
└── chunk_text: TEXT

extracted_indicators (existing)
├── object_key: VARCHAR (FK to document_embeddings)
├── company_id: INTEGER (FK to company_catalog)
├── indicator_id: INTEGER (FK to brsr_indicators)
├── extracted_value: TEXT
├── numeric_value: DECIMAL
├── confidence_score: DECIMAL
└── validation_status: VARCHAR

esg_scores (existing)
├── company_id: INTEGER (FK to company_catalog)
├── report_year: INTEGER
├── environmental_score: DECIMAL
├── social_score: DECIMAL
├── governance_score: DECIMAL
└── overall_score: DECIMAL
```

## Error Handling

### Cleanup Script Errors

1. **Database Connection Failure**
   - Log error with connection details
   - Exit with non-zero status code
   - Provide troubleshooting guidance

2. **No Sample Data Found**
   - Log informational message
   - Exit successfully (nothing to clean)

3. **Partial Deletion Failure**
   - Use database transactions
   - Rollback on error
   - Log detailed error information

### Trigger Script Errors

1. **No Documents to Process**
   - Log informational message
   - Exit successfully

2. **RabbitMQ Connection Failure**
   - Log error with connection details
   - Exit with non-zero status code
   - Provide troubleshooting guidance

3. **Queue Declaration Failure**
   - Log error (queue may not exist or have wrong configuration)
   - Exit with non-zero status code

### Extraction Service Errors

1. **Document Already Processed**
   - Skip processing
   - Acknowledge message
   - Log informational message

2. **Company Not Found**
   - Log error with company name
   - Mark document as failed
   - Acknowledge message (don't requeue)

3. **Extraction Failure**
   - Log error with details
   - Requeue message (up to max retries)
   - Send to dead letter queue after max retries

## Testing Strategy

### 1. Cleanup Script Testing

**Test Cases:**
- Verify sample data identification
- Verify sample data deletion
- Verify orphaned score deletion
- Verify transaction rollback on error
- Verify dry-run mode (if implemented)

**Validation:**
```sql
-- Before cleanup
SELECT COUNT(*) FROM extracted_indicators WHERE extracted_value LIKE 'Sample:%';
SELECT COUNT(*) FROM esg_scores;

-- After cleanup
SELECT COUNT(*) FROM extracted_indicators WHERE extracted_value LIKE 'Sample:%';
-- Should be 0

SELECT COUNT(*) FROM esg_scores es
WHERE NOT EXISTS (
    SELECT 1 FROM extracted_indicators ei 
    WHERE ei.company_id = es.company_id 
    AND ei.report_year = es.report_year
);
-- Should be 0
```

### 2. Trigger Script Testing

**Test Cases:**
- Verify document query returns correct results
- Verify limit parameter works
- Verify dry-run mode (if implemented)
- Verify messages are published to queue
- Verify queue connection handling

**Validation:**
```bash
# Check queue has messages
docker exec rabbitmq rabbitmqctl list_queues name messages

# Check extraction service logs
docker logs esg-extraction | grep "Received extraction task"
```

### 3. End-to-End Pipeline Testing

**Test Cases:**
- Verify embeddings service publishes to extraction queue
- Verify extraction service processes messages
- Verify indicators are extracted (not sample data)
- Verify ESG scores are calculated
- Verify document status is updated

**Validation:**
```sql
-- Check for actual extracted data (not sample)
SELECT object_key, indicator_id, extracted_value, confidence_score
FROM extracted_indicators
WHERE object_key = 'RELIANCE/2024_BRSR.pdf'
LIMIT 10;

-- Verify no sample data
SELECT COUNT(*) FROM extracted_indicators 
WHERE extracted_value LIKE 'Sample:%';

-- Check ESG scores
SELECT company_id, report_year, overall_score, environmental_score, social_score, governance_score
FROM esg_scores
WHERE company_id = (SELECT id FROM company_catalog WHERE symbol = 'RELIANCE')
ORDER BY report_year DESC;
```

### 4. Service Health Checks

**Validation:**
```bash
# Check all services are running
docker ps | grep -E "esg-(ingestion|embeddings|extraction)"

# Check RabbitMQ queues
docker exec rabbitmq rabbitmqctl list_queues name messages consumers

# Check database connections
docker exec postgres psql -U esg_user -d esg_platform -c "SELECT COUNT(*) FROM document_embeddings;"
```

## Implementation Notes

### Execution Order

1. **Remove sample data scripts** (delete files)
2. **Create and run cleanup script** (remove existing sample data)
3. **Update trigger script** (add parameters and validation)
4. **Verify extraction service** (check logs and configuration)
5. **Trigger extraction** (queue documents for processing)
6. **Monitor pipeline** (watch logs and database)

### Configuration

**Environment Variables (no changes needed):**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database connection
- `RABBITMQ_HOST`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD` - RabbitMQ connection
- `EXTRACTION_QUEUE_NAME` - Queue name (default: "extraction-tasks")

### Monitoring

**Key Metrics:**
- Number of documents with embeddings
- Number of documents with extractions
- Number of documents in extraction queue
- Extraction service processing rate
- Extraction success/failure rate

**Monitoring Commands:**
```bash
# Database metrics
docker exec postgres psql -U esg_user -d esg_platform -c "
SELECT 
    (SELECT COUNT(DISTINCT object_key) FROM document_embeddings) as docs_with_embeddings,
    (SELECT COUNT(DISTINCT object_key) FROM extracted_indicators) as docs_with_extractions,
    (SELECT COUNT(*) FROM esg_scores) as companies_with_scores;
"

# Queue metrics
docker exec rabbitmq rabbitmqctl list_queues name messages consumers

# Service logs
docker logs --tail 50 esg-extraction
```

## Rollback Plan

If issues occur during implementation:

1. **Sample data scripts removed but needed**
   - Restore from git history: `git checkout HEAD~1 scripts/populate_data.sql`

2. **Cleanup script deleted too much data**
   - Restore from database backup
   - Re-run embeddings service to regenerate embeddings
   - Re-trigger extraction

3. **Extraction service not processing**
   - Check service logs: `docker logs esg-extraction`
   - Verify queue configuration: `docker exec rabbitmq rabbitmqctl list_queues`
   - Restart service: `docker restart esg-extraction`

## Success Criteria

The implementation is successful when:

1. ✅ Sample data scripts are removed from repository
2. ✅ No sample data exists in database (extracted_indicators with "Sample:" prefix)
3. ✅ Trigger script successfully queues documents for extraction
4. ✅ Extraction service processes documents and extracts actual indicators
5. ✅ ESG scores are calculated from actual extracted data
6. ✅ Pipeline processes at least 5 documents end-to-end successfully
