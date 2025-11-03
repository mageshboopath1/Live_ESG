# Error Handling and Logging

This document describes the comprehensive error handling and logging implementation in the extraction service.

## Overview

The extraction service implements robust error handling with:
- Comprehensive error logging for all failure scenarios
- LLM API error handling with exponential backoff retry logic
- Validation failure logging with detailed indicator context
- Document status tracking for monitoring
- Dead letter queue (DLQ) for failed tasks after max retries

## Requirements Addressed

- **9.1**: Comprehensive error logging for extraction failures
- **9.2**: Log LLM API errors with retry attempts
- **11.5**: Retry logic with exponential backoff for API failures
- **5.3**: Retry failed tasks according to configured retry logic
- **5.4**: Increment retry counter in task metadata
- **5.5**: Move tasks to dead letter queue after max retries
- **13.1-13.4**: Validation error logging with indicator details

## Error Handling Components

### 1. Main Extraction Pipeline (`main.py`)

#### Document Processing Errors

The `process_extraction_task()` function handles errors at each pipeline stage:

```python
# Parse errors
try:
    company_name, report_year = parse_object_key(object_key)
except ValueError as e:
    logger.error(f"Failed to parse object key: {e}", extra={...})
    return False

# Database errors
try:
    company_id = get_company_id_by_name(company_name)
except Exception as e:
    logger.error(f"Database error: {e}", extra={...})
    return False

# Extraction errors
try:
    extracted_indicators = extract_indicators_batch(...)
except Exception as e:
    logger.error(f"Batch extraction failed: {e}", extra={...})
    return False
```

#### Structured Logging

All errors include structured context using the `extra` parameter:

```python
logger.error(
    f"Failed to process extraction task for {object_key}: {e}",
    exc_info=True,
    extra={
        "object_key": object_key,
        "error_type": "unexpected_error",
        "error_message": str(e),
        "processing_time_seconds": elapsed_time,
        "success": False
    }
)
```

#### Document Status Tracking

The service updates document status at key points:

```python
# Start processing
update_document_status(object_key, "PROCESSING")

# On success
update_document_status(object_key, "SUCCESS")

# On failure
update_document_status(object_key, "FAILED", error_message)
```

### 2. RabbitMQ Retry Logic (`callback()`)

The message callback implements retry logic with dead letter queue support:

```python
def callback(ch, method, properties, body):
    # Track retry count from message headers
    retry_count = properties.headers.get("x-retry-count", 0)
    max_retries = config.max_retries  # Default: 3
    
    success = process_extraction_task(object_key)
    
    if success:
        # Acknowledge and remove from queue
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        if retry_count < max_retries:
            # Requeue for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.warning(f"Requeuing for retry {retry_count}/{max_retries}")
        else:
            # Send to dead letter queue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            logger.error(f"Max retries exceeded, sending to DLQ")
```

#### Dead Letter Queue Configuration

The main queue is configured with DLQ routing:

```python
# Declare DLQ
dlq_name = f"{config.extraction_queue}.dlq"
channel.queue_declare(queue=dlq_name, durable=True)

# Declare main queue with DLQ routing
channel.queue_declare(
    queue=config.extraction_queue,
    durable=True,
    arguments={
        'x-dead-letter-exchange': '',
        'x-dead-letter-routing-key': dlq_name,
    }
)
```

### 3. LLM API Error Handling (`extraction_chain.py`)

#### Exponential Backoff Retry

The `_execute_chain_with_retry()` method implements exponential backoff:

```python
for attempt in range(self.max_retries):
    try:
        result = chain.invoke({"context": context})
        return result
    except Exception as e:
        if attempt < self.max_retries - 1:
            # Exponential backoff
            delay = self.initial_retry_delay * (2 ** attempt)
            
            # Extra delay for rate limit errors
            if "rate" in str(e).lower():
                delay *= 2
            
            logger.warning(
                f"LLM API error on attempt {attempt + 1}: {e}. "
                f"Retrying in {delay}s...",
                extra={
                    "attempt": attempt + 1,
                    "retry_delay": delay,
                    "error_type": type(e).__name__,
                    "is_rate_limit": is_rate_limit
                }
            )
            time.sleep(delay)
        else:
            logger.error(f"LLM API failed after {self.max_retries} attempts")
            raise
```

#### Retry Delays

Default retry delays with exponential backoff:
- Attempt 1: 1.0s
- Attempt 2: 2.0s
- Attempt 3: 4.0s

For rate limit errors, delays are doubled:
- Attempt 1: 2.0s
- Attempt 2: 4.0s
- Attempt 3: 8.0s

#### Vector Retrieval Retry

Similar retry logic for vector database queries:

```python
def _retrieve_with_retry(self, query: str, k: int):
    for attempt in range(self.max_retries):
        try:
            documents = self.retriever.get_relevant_documents(query, k)
            return documents
        except Exception as e:
            # Exponential backoff with logging
            ...
```

### 4. Validation Error Logging (`main.py`)

Validation errors are logged with full indicator context:

```python
if validation_result.errors:
    error_detail = {
        "indicator_code": indicator_def.indicator_code,
        "indicator_name": indicator_def.parameter_name,
        "extracted_value": extracted.extracted_value,
        "numeric_value": extracted.numeric_value,
        "confidence_score": extracted.confidence_score,
        "errors": validation_result.errors
    }
    
    logger.warning(
        f"Validation errors for {indicator_def.indicator_code}: "
        f"{validation_result.errors}",
        extra={
            "object_key": object_key,
            "indicator_code": indicator_def.indicator_code,
            "validation_errors": validation_result.errors,
            "error_type": "validation_error"
        }
    )
```

#### Validation Summary

After validating all indicators, a summary is logged:

```python
logger.info(
    f"Validation complete: {validation_stats['valid']} valid, "
    f"{validation_stats['invalid']} invalid, "
    f"{validation_stats['warnings']} warnings",
    extra={
        "object_key": object_key,
        "validation_stats": validation_stats,
        "validation_errors_count": len(validation_errors_detail)
    }
)
```

### 5. Batch Extraction Error Handling (`extractor.py`)

Individual indicator extraction failures don't stop the batch:

```python
for indicator in attribute_indicators:
    try:
        extracted = extract_indicator(...)
        extracted_indicators.append(extracted)
    except Exception as e:
        failed_count += 1
        logger.error(
            f"Failed to extract indicator {indicator.indicator_code}: {e}",
            exc_info=True,
            extra={
                "indicator_code": indicator.indicator_code,
                "attribute_number": attribute_number,
                "error_type": type(e).__name__,
                "failed_count": failed_count
            }
        )
        # Continue with next indicator
```

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Retry configuration
MAX_RETRIES=3  # Maximum retry attempts
INITIAL_RETRY_DELAY=1.0  # Initial delay in seconds

# RabbitMQ
EXTRACTION_QUEUE_NAME=extraction-tasks
```

### Logging Format

All logs use structured format with timestamp, level, and context:

```
2024-01-15 10:30:45 [ERROR] main: Failed to extract indicator GHG_SCOPE1: API rate limit exceeded
```

Structured logging includes extra fields for monitoring:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "ERROR",
  "message": "Failed to extract indicator GHG_SCOPE1",
  "object_key": "RELIANCE/2024_BRSR.pdf",
  "indicator_code": "GHG_SCOPE1",
  "error_type": "RateLimitError",
  "retry_count": 2,
  "max_retries": 3
}
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Extraction Success Rate**
   - Track ratio of successful to failed extractions
   - Alert if success rate drops below threshold

2. **Retry Rate**
   - Monitor frequency of retries
   - High retry rate may indicate API issues

3. **DLQ Size**
   - Track number of messages in dead letter queue
   - Alert if DLQ grows beyond threshold

4. **Validation Error Rate**
   - Monitor percentage of indicators with validation errors
   - May indicate data quality issues

5. **Processing Time**
   - Track average processing time per document
   - Alert on significant increases

### Log Queries

#### Find all failed extractions:
```bash
grep "Failed to process extraction task" extraction.log
```

#### Find LLM API errors:
```bash
grep "LLM API error" extraction.log
```

#### Find validation errors:
```bash
grep "Validation errors for" extraction.log
```

#### Find documents sent to DLQ:
```bash
grep "sending to DLQ" extraction.log
```

## Error Recovery

### Reprocessing Failed Documents

Documents in the DLQ can be reprocessed:

1. **Inspect DLQ messages**:
   ```bash
   # Using RabbitMQ management UI
   # Navigate to Queues -> extraction-tasks.dlq
   ```

2. **Move messages back to main queue**:
   ```python
   # Using RabbitMQ shovel or manual republish
   ```

3. **Fix underlying issues** before reprocessing:
   - Check API quotas and rate limits
   - Verify database connectivity
   - Ensure document embeddings exist

### Manual Status Reset

Reset document status to reprocess:

```sql
UPDATE ingestion_metadata
SET status = 'PENDING'
WHERE file_path = 'RELIANCE/2024_BRSR.pdf';

-- Delete existing extracted indicators if needed
DELETE FROM extracted_indicators
WHERE object_key = 'RELIANCE/2024_BRSR.pdf';
```

## Best Practices

1. **Always check logs** before reprocessing failed documents
2. **Monitor DLQ size** regularly to catch systemic issues
3. **Set up alerts** for high error rates
4. **Review validation errors** to improve extraction prompts
5. **Track retry patterns** to identify API stability issues
6. **Use structured logging** for easier querying and analysis
7. **Preserve failed extractions** for debugging (don't delete)

## Troubleshooting

### High Retry Rate

**Symptoms**: Many retries, slow processing

**Possible causes**:
- API rate limits
- Network instability
- Database connection issues

**Solutions**:
- Increase `INITIAL_RETRY_DELAY`
- Reduce concurrent workers
- Check API quota usage

### Documents Stuck in DLQ

**Symptoms**: Growing DLQ, no progress

**Possible causes**:
- Invalid document format
- Missing embeddings
- Corrupted data

**Solutions**:
- Inspect DLQ messages
- Verify document embeddings exist
- Check for data corruption

### Validation Errors

**Symptoms**: Many indicators marked invalid

**Possible causes**:
- Incorrect extraction prompts
- Document format changes
- Schema mismatches

**Solutions**:
- Review validation rules
- Update extraction prompts
- Check BRSR indicator definitions

## Future Enhancements

1. **Metrics Export**: Export metrics to Prometheus
2. **Distributed Tracing**: Add OpenTelemetry tracing
3. **Alerting**: Integrate with PagerDuty/Slack
4. **Auto-recovery**: Automatic DLQ reprocessing
5. **Circuit Breaker**: Prevent cascading failures
