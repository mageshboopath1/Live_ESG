# Design Document

## Overview

This design document outlines the implementation of an end-to-end pipeline testing system that validates the complete ESG data processing workflow. The system will provide comprehensive data cleanup capabilities and orchestrate the sequential execution of ingestion, embedding, extraction, and scoring services with proper synchronization and monitoring.

The pipeline processes BRSR (Business Responsibility and Sustainability Reporting) documents from Indian companies, extracting ESG indicators and calculating scores. The testing system ensures all services work correctly together and validates data flow between components.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Pipeline Test Orchestrator                   │
│  (Python script that coordinates all stages and monitors progress)│
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──► 1. Cleanup Stage
             │    ├─ MinIO (PDF storage)
             │    ├─ PostgreSQL (all tables)
             │    └─ RabbitMQ (all queues)
             │
             ├──► 2. Ingestion Stage
             │    └─ Downloads PDFs → MinIO → Publishes to queues
             │
             ├──► 3. Embedding Stage (wait for completion)
             │    └─ Consumes embedding-tasks → Generates embeddings
             │
             ├──► 4. Extraction Stage (wait for completion)
             │    └─ Consumes extraction-tasks → Extracts indicators
             │
             └──► 5. Scoring & Validation Stage
                  └─ Validates scores and data integrity
```

### Data Flow

```
PDF Links → Ingestion Service → MinIO Storage
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
          embedding-tasks         extraction-tasks
                    ↓                   ↓ (delayed)
          Embedding Service             │
                    ↓                   │
          document_embeddings           │
                    ↓                   │
                (wait complete)         │
                                       ↓
                            Extraction Service
                                       ↓
                            extracted_indicators
                                       ↓
                              Scoring Calculator
                                       ↓
                                  esg_scores
```

### Service Dependencies

1. **Ingestion Service** depends on:
   - MinIO (object storage)
   - PostgreSQL (company_catalog, ingestion_metadata)
   - RabbitMQ (publishing messages)

2. **Embedding Service** depends on:
   - RabbitMQ (consuming embedding-tasks)
   - MinIO (reading PDFs)
   - PostgreSQL (document_embeddings table)
   - Google GenAI API (gemini-embedding-001 model)

3. **Extraction Service** depends on:
   - RabbitMQ (consuming extraction-tasks)
   - PostgreSQL (document_embeddings, brsr_indicators, extracted_indicators)
   - Google GenAI API (gemini-2.5-flash model for extraction)

4. **Scoring Service** depends on:
   - PostgreSQL (extracted_indicators, esg_scores)

## Components and Interfaces

### 1. Cleanup Module (`cleanup_pipeline_data.py`)

**Purpose**: Remove all existing pipeline data to enable fresh testing

**Interface**:
```python
def cleanup_minio_storage() -> int:
    """Delete all objects from esg-reports bucket"""
    
def cleanup_database_tables() -> dict[str, int]:
    """Delete all records from pipeline tables"""
    
def cleanup_rabbitmq_queues() -> dict[str, int]:
    """Purge all messages from queues"""
    
def cleanup_all(confirm: bool = False) -> dict:
    """Execute complete cleanup with optional confirmation"""
```

**Tables to Clean**:
- `document_embeddings` - Vector embeddings (3072 dimensions)
- `extracted_indicators` - Extracted BRSR indicators
- `esg_scores` - Calculated ESG scores
- `ingestion_metadata` - Ingestion tracking
- `company_catalog` - Company information (optional, preserve if needed)

**Queues to Purge**:
- `embedding-tasks` - Pending embedding jobs
- `extraction-tasks` - Pending extraction jobs

**MinIO Cleanup**:
- Bucket: `esg-reports`
- Delete all objects recursively

### 2. Ingestion Orchestration

**Current Implementation**: `services/ingestion/src/download_reports.py`

**Required Modifications**:
- Ensure company metadata is inserted into `company_catalog` before report processing
- Insert report metadata into `ingestion_metadata` table with MinIO object key
- Publish to both `embedding-tasks` and `extraction-tasks` queues
- Add delay/TTL to extraction-tasks messages to prevent premature processing

**Message Format**:
```python
# embedding-tasks message
{
    "object_key": "RELIANCE/2023_2024/BRSR_Report.pdf",
    "company_name": "RELIANCE",
    "report_year": 2023
}

# extraction-tasks message (with delay)
{
    "object_key": "RELIANCE/2023_2024/BRSR_Report.pdf",
    "company_name": "RELIANCE",
    "report_year": 2023,
    "delay_seconds": 300  # Wait 5 minutes for embeddings
}
```

### 3. Embedding Service Updates

**Current Implementation**: `services/embeddings/src/main.py`

**Required Changes**:
1. Update embedding model to `gemini-embedding-001` with 3072 dimensions
2. Update database schema to use `vector(3072)` type
3. Ensure proper error handling and message acknowledgment

**Updated Embedder** (`services/embeddings/src/embedder.py`):
```python
from google import genai
from google.genai import types

embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY,
    config=types.EmbedContentConfig(output_dimensionality=3072)
)
```

**Database Schema Update**:
```sql
ALTER TABLE document_embeddings 
ALTER COLUMN embedding TYPE vector(3072);
```

### 4. Extraction Service Updates

**Current Implementation**: `services/extraction/src/retrieval/filtered_retriever.py`

**Required Changes**:
1. Update retriever to use `gemini-embedding-001` with 3072 dimensions
2. Add embedding existence check before processing extraction tasks
3. Implement requeue logic for premature extraction attempts

**Updated Retriever**:
```python
class FilteredPGVectorRetriever:
    def __init__(self, connection_string, company_name, report_year):
        self.embedding_function = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            config=types.EmbedContentConfig(output_dimensionality=3072)
        )
```

**Extraction Worker Logic** (`services/extraction/main.py`):
```python
def check_embeddings_exist(object_key: str) -> bool:
    """Check if embeddings exist for the given document"""
    # Query document_embeddings table
    # Return True if embeddings found, False otherwise

def callback(ch, method, properties, body):
    object_key = parse_message(body)
    
    # Check if embeddings are ready
    if not check_embeddings_exist(object_key):
        logger.warning(f"Embeddings not ready for {object_key}, requeuing...")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        time.sleep(30)  # Wait before requeue
        return
    
    # Process extraction
    success = process_extraction_task(object_key)
    if success:
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
```

### 5. Pipeline Test Orchestrator

**New Script**: `scripts/test_pipeline_e2e.py`

**Purpose**: Coordinate all pipeline stages and monitor progress

**Interface**:
```python
class PipelineOrchestrator:
    def __init__(self, config: dict):
        """Initialize with database, MinIO, RabbitMQ connections"""
    
    def run_cleanup_stage(self) -> bool:
        """Execute cleanup and verify"""
    
    def run_ingestion_stage(self, limit: int = None) -> dict:
        """Run ingestion for N companies, return stats"""
    
    def monitor_embedding_queue(self, timeout: int = 3600) -> dict:
        """Wait for embedding queue to empty, return stats"""
    
    def monitor_extraction_queue(self, timeout: int = 7200) -> dict:
        """Wait for extraction queue to empty, return stats"""
    
    def validate_pipeline_output(self) -> dict:
        """Verify data integrity and completeness"""
    
    def run_full_pipeline(self, companies: list = None) -> dict:
        """Execute complete pipeline with monitoring"""
```

**Monitoring Logic**:
```python
def monitor_queue(queue_name: str, check_interval: int = 10, timeout: int = 3600):
    """
    Monitor RabbitMQ queue until empty or timeout
    
    Returns:
        - messages_processed: int
        - duration_seconds: float
        - success: bool
    """
    start_time = time.time()
    last_count = get_queue_message_count(queue_name)
    
    while True:
        current_count = get_queue_message_count(queue_name)
        
        if current_count == 0:
            # Queue empty, verify no new messages for 30 seconds
            time.sleep(30)
            if get_queue_message_count(queue_name) == 0:
                return {
                    "messages_processed": last_count,
                    "duration_seconds": time.time() - start_time,
                    "success": True
                }
        
        if time.time() - start_time > timeout:
            return {
                "messages_processed": last_count - current_count,
                "duration_seconds": time.time() - start_time,
                "success": False,
                "error": "Timeout exceeded"
            }
        
        time.sleep(check_interval)
```

## Data Models

### Database Tables

**document_embeddings** (updated):
```sql
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    object_key TEXT NOT NULL,
    company_name TEXT NOT NULL,
    report_year INT NOT NULL,
    page_number INT,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(3072) NOT NULL,  -- Changed from 768 to 3072
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(object_key, chunk_index)
);

CREATE INDEX idx_embeddings_lookup 
ON document_embeddings(company_name, report_year);

CREATE INDEX idx_embeddings_vector 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
```

**ingestion_metadata** (existing):
```sql
CREATE TABLE ingestion_metadata (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES company_catalog(id),
    source TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- MinIO object key
    file_type TEXT NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'SUCCESS'
);
```

**extracted_indicators** (existing):
```sql
CREATE TABLE extracted_indicators (
    id SERIAL PRIMARY KEY,
    object_key TEXT NOT NULL,
    company_id INT REFERENCES company_catalog(id),
    report_year INT NOT NULL,
    indicator_id INT REFERENCES brsr_indicators(id),
    extracted_value TEXT NOT NULL,
    numeric_value DECIMAL,
    confidence_score DECIMAL(3,2),
    validation_status TEXT DEFAULT 'pending',
    source_pages INT[],
    source_chunk_ids INT[],
    extracted_at TIMESTAMP DEFAULT NOW()
);
```

**esg_scores** (existing):
```sql
CREATE TABLE esg_scores (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES company_catalog(id),
    report_year INT NOT NULL,
    environmental_score DECIMAL(5,2),
    social_score DECIMAL(5,2),
    governance_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    calculation_metadata JSONB,
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

### Configuration

**Environment Variables**:
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
POSTGRES_DB=moz
POSTGRES_USER=drfitz
POSTGRES_PASSWORD=h4i1hydr4

# MinIO
MINIO_ENDPOINT=http://localhost:9000
MINIO_ROOT_USER=esg_minio
MINIO_ROOT_PASSWORD=esg_secret

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_DEFAULT_USER=esg_rabbitmq
RABBITMQ_DEFAULT_PASS=esg_secret

# Google GenAI
GENAI_API_KEY=<your-api-key>

# Pipeline Config
EMBEDDING_BATCH_SIZE=32
EXTRACTION_BATCH_SIZE=10
MAX_RETRIES=3
QUEUE_CHECK_INTERVAL=10
```

## Error Handling

### Cleanup Stage Errors

1. **MinIO Connection Failure**:
   - Retry with exponential backoff (3 attempts)
   - Log error and continue with database cleanup
   - Report partial cleanup status

2. **Database Connection Failure**:
   - Fail fast with clear error message
   - Do not proceed to ingestion stage

3. **RabbitMQ Connection Failure**:
   - Retry with exponential backoff
   - Log warning if queues cannot be purged
   - Continue with pipeline (queues may be empty)

### Ingestion Stage Errors

1. **PDF Download Failure**:
   - Log error with company name and URL
   - Continue with remaining companies
   - Report failed downloads in summary

2. **MinIO Upload Failure**:
   - Retry upload 3 times
   - Skip document if all retries fail
   - Do not publish queue messages for failed uploads

3. **Queue Publishing Failure**:
   - Retry with exponential backoff
   - Log error if message cannot be published
   - Mark document as "pending_queue" in metadata

### Embedding Stage Errors

1. **PDF Processing Failure**:
   - Log error with object_key
   - Reject message (send to DLQ after retries)
   - Continue processing other documents

2. **Embedding Generation Failure**:
   - Retry with exponential backoff (3 attempts)
   - Use batch processing to isolate failures
   - Store partial embeddings if some chunks succeed

3. **Database Insert Failure**:
   - Rollback transaction
   - Reject message for retry
   - Log detailed error information

### Extraction Stage Errors

1. **Missing Embeddings**:
   - Requeue message with delay (30 seconds)
   - Maximum 10 requeue attempts
   - Send to DLQ if embeddings never appear

2. **Extraction Chain Failure**:
   - Log error with indicator code
   - Continue with remaining indicators
   - Store partial results

3. **Scoring Calculation Failure**:
   - Log error with company and year
   - Store extracted indicators without scores
   - Allow manual score recalculation

### Monitoring Timeouts

1. **Embedding Queue Timeout** (default: 1 hour):
   - Log warning with remaining message count
   - Provide option to continue or abort
   - Generate partial results report

2. **Extraction Queue Timeout** (default: 2 hours):
   - Log warning with remaining message count
   - Provide option to continue or abort
   - Generate partial results report

## Testing Strategy

### Unit Tests

1. **Cleanup Module Tests**:
   - Test MinIO deletion with mock client
   - Test database cleanup with test database
   - Test queue purging with mock RabbitMQ

2. **Orchestrator Tests**:
   - Test queue monitoring logic
   - Test timeout handling
   - Test progress reporting

3. **Service Update Tests**:
   - Test embedding dimension changes
   - Test retriever with 3072-dimensional vectors
   - Test extraction requeue logic

### Integration Tests

1. **Single Document Pipeline**:
   - Process one PDF through complete pipeline
   - Verify embeddings created (3072 dimensions)
   - Verify indicators extracted
   - Verify scores calculated

2. **Multi-Document Pipeline**:
   - Process 3-5 documents concurrently
   - Verify queue processing order
   - Verify no data corruption

3. **Error Recovery Tests**:
   - Test extraction requeue when embeddings missing
   - Test retry logic for failed operations
   - Test DLQ handling

### End-to-End Tests

1. **Full Pipeline Test**:
   - Clean all data
   - Ingest 10 companies
   - Wait for embedding completion
   - Wait for extraction completion
   - Validate all scores calculated

2. **Performance Test**:
   - Process 50 documents
   - Measure throughput (documents/hour)
   - Identify bottlenecks

3. **Data Integrity Test**:
   - Verify no orphaned records
   - Verify referential integrity
   - Verify embedding dimensions match
   - Verify score calculations correct

### Validation Checks

**Post-Pipeline Validation**:
```python
def validate_pipeline_output():
    checks = {
        "embeddings_created": check_embeddings_count(),
        "embeddings_dimension": check_embedding_dimensions(),
        "indicators_extracted": check_indicators_count(),
        "scores_calculated": check_scores_count(),
        "no_orphaned_records": check_referential_integrity(),
        "embedding_model_match": verify_embedding_model(),
    }
    return checks

def check_embedding_dimensions():
    """Verify all embeddings are 3072 dimensions"""
    query = """
        SELECT COUNT(*) as count
        FROM document_embeddings
        WHERE array_length(embedding, 1) != 3072
    """
    # Should return 0

def verify_embedding_model():
    """Verify embeddings were created with gemini-embedding-001"""
    # Check metadata or sample embedding
    # Verify cosine similarity with known test vector
```

## Performance Considerations

### Embedding Service

- **Batch Size**: 32 chunks per API call
- **Concurrency**: Single worker (API rate limits)
- **Expected Throughput**: ~50-100 pages/minute
- **Bottleneck**: Google GenAI API rate limits

### Extraction Service

- **Batch Size**: Process all indicators for one document
- **Concurrency**: Single worker (avoid database contention)
- **Expected Throughput**: ~1-2 documents/minute
- **Bottleneck**: LLM inference time

### Database

- **Connection Pooling**: Max 10 connections per service
- **Index Usage**: Ensure indexes on company_name, report_year
- **Vector Search**: Use IVFFlat index for embeddings

### Queue Management

- **Prefetch Count**: 1 (ensure fair distribution)
- **Message TTL**: 24 hours (prevent stale messages)
- **DLQ**: Capture failed messages after 3 retries

## Deployment Considerations

### Docker Compose Updates

**Add environment variables**:
```yaml
services:
  embeddings:
    environment:
      - EMBEDDING_MODEL=gemini-embedding-001
      - EMBEDDING_DIMENSIONS=3072
  
  extraction:
    environment:
      - EMBEDDING_MODEL=gemini-embedding-001
      - EMBEDDING_DIMENSIONS=3072
      - CHECK_EMBEDDINGS_BEFORE_EXTRACTION=true
```

### Database Migration

**Migration Script** (`migrations/005_update_embedding_dimensions.sql`):
```sql
-- Backup existing embeddings
CREATE TABLE document_embeddings_backup AS 
SELECT * FROM document_embeddings;

-- Drop existing table
DROP TABLE document_embeddings CASCADE;

-- Recreate with new dimensions
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

-- Recreate indexes
CREATE INDEX idx_embeddings_lookup 
ON document_embeddings(company_name, report_year);

CREATE INDEX idx_embeddings_vector 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Monitoring and Logging

**Metrics to Track**:
- Documents processed per stage
- Average processing time per document
- Queue depths over time
- Error rates by stage
- Embedding dimension validation
- Score calculation success rate

**Log Aggregation**:
- Centralize logs from all services
- Use structured logging (JSON format)
- Include correlation IDs (object_key)
- Track processing duration

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **Database Credentials**: Use secrets management
3. **MinIO Access**: Restrict bucket permissions
4. **RabbitMQ**: Use authentication, limit queue access
5. **Cleanup Confirmation**: Require explicit confirmation before data deletion

## Rollback Plan

If pipeline test fails:

1. **Stop all services** to prevent further processing
2. **Restore database** from backup (if available)
3. **Clear RabbitMQ queues** to prevent reprocessing
4. **Investigate logs** to identify root cause
5. **Fix issues** in service code
6. **Re-run cleanup** and restart pipeline

## Success Criteria

Pipeline test is successful when:

1. ✅ All data cleaned successfully
2. ✅ All PDFs ingested and uploaded to MinIO
3. ✅ All embeddings generated with 3072 dimensions
4. ✅ All extraction tasks completed
5. ✅ All ESG scores calculated
6. ✅ No orphaned records in database
7. ✅ No messages remaining in queues
8. ✅ All validation checks pass
9. ✅ Processing completed within expected timeframe
10. ✅ No critical errors in logs
