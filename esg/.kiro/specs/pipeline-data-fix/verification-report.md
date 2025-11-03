# Extraction Service Configuration Verification Report

## Task 4.1: Extraction Service Startup and Queue Connection

### ✅ Service Status
- **Container**: `esg-extraction` is running (Up About an hour, unhealthy status)
- **Startup**: Service started successfully
- **HTTP Server**: Health and metrics server running on port 8080
  - Health check: http://0.0.0.0:8080/health
  - Metrics: http://0.0.0.0:8080/metrics

### ✅ Configuration Verified
```
Database: postgres:5432/moz
RabbitMQ: rabbitmq
Queue: extraction-tasks
Log Level: INFO
```

### ✅ RabbitMQ Connection
- **Initial Connection**: Failed initially (RabbitMQ not ready)
- **Retry Logic**: Successfully connected after 15 seconds with exponential backoff
- **Connection Status**: ✓ Connected successfully
- **Queue Declaration**: ✓ Successfully declared `extraction-tasks` queue
- **Dead Letter Queue**: ✓ Successfully declared `extraction-tasks.dlq`

### ✅ Database Connection
- Database health check performed during startup
- Connection string: `postgresql://postgres:***@postgres:5432/moz`

### Queue Status
```
Queue Name           Messages    Consumers
extraction-tasks     20          1
extraction-tasks.dlq 0           0
embedding-tasks      0           1
```

---

## Task 4.2: Message Processing Configuration

### ✅ Manual Acknowledgment
**Status**: Enabled
```python
channel.basic_consume(
    queue=config.extraction_queue,
    on_message_callback=callback,
    auto_ack=False,  # Manual acknowledgment
)
```

### ✅ Retry Logic
**Status**: Configured
- **Max Retries**: 3 (from config.max_retries)
- **Retry Tracking**: Uses message headers (`x-retry-count`)
- **Requeue on Failure**: Yes, up to max_retries
- **Implementation**: 
  - Success: `ch.basic_ack(delivery_tag=method.delivery_tag)`
  - Retry: `ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)`
  - Final Failure: `ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)`

### ✅ Dead Letter Queue
**Status**: Configured
```python
channel.queue_declare(
    queue=config.extraction_queue,
    durable=True,
    arguments={
        'x-dead-letter-exchange': '',
        'x-dead-letter-routing-key': dlq_name,
    }
)
```
- **DLQ Name**: `extraction-tasks.dlq`
- **Routing**: Messages sent to DLQ after max retries exceeded

### ✅ QoS Settings
**Status**: Configured
```python
channel.basic_qos(prefetch_count=1)
```
- **Prefetch Count**: 1 (processes one message at a time)
- **Purpose**: Ensures fair distribution across multiple workers

---

## Task 4.3: Test Extraction Service with Sample Message

### ❌ CRITICAL ISSUE IDENTIFIED

**Problem**: Message format mismatch between ingestion service and extraction service

**Current Message Format** (from ingestion service):
```json
{
  "object_key": "ADANIPORTS/2023_2024/rkbhagia_28052024212854_IntimationofAnnualReport.pdf",
  "company_id": 2,
  "company_name": "Adani Ports and Special Economic Zone Ltd.",
  "report_year": 2023
}
```

**Expected Format** (by extraction service):
```
Plain string: "ADANIPORTS/2023_2024/rkbhagia_28052024212854_IntimationofAnnualReport.pdf"
```

### Error Messages
```
2025-10-30 15:29:17,497 [ERROR] __main__: Failed to parse object key 
'{"object_key": "ADANIPORTS/2023_2024/rkbhagia_28052024212854_IntimationofAnnualReport.pdf", 
"company_id": 2, "company_name": "Adani Ports and Special Economic Zone Ltd.", 
"report_year": 2023}': Invalid object key format
```

### Impact
- **20 messages** stuck in queue, continuously retrying
- All messages failing at parse stage
- No successful extractions occurring
- Messages being requeued repeatedly (attempt 1/4, 2/4, etc.)

### Root Cause
The extraction service `callback` function expects:
```python
object_key = body.decode("utf-8")  # Expects plain string
```

But receives JSON objects that need to be parsed first.

---

## Configuration Issues Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Service Startup | ✅ Working | Service starts and connects successfully |
| Queue Connection | ✅ Working | Connected to RabbitMQ with retry logic |
| Database Connection | ✅ Working | Database health check passes |
| Manual Acknowledgment | ✅ Configured | auto_ack=False |
| Retry Logic | ✅ Configured | Max 3 retries with header tracking |
| Dead Letter Queue | ✅ Configured | extraction-tasks.dlq created |
| QoS Settings | ✅ Configured | prefetch_count=1 |
| **Message Format** | ❌ **BROKEN** | **JSON vs plain string mismatch** |

---

## Recommendations

1. **Immediate Fix Required**: Update extraction service to parse JSON messages
2. **Alternative**: Update ingestion service to send plain object_key strings
3. **Preferred Solution**: Fix extraction service (maintains richer message context)

The extraction service configuration is correct, but it cannot process messages due to the format mismatch.
