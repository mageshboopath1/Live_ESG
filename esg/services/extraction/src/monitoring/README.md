# Monitoring and Metrics

This module provides monitoring and metrics functionality for the extraction service.

## Features

### 1. Metrics Collection

The `MetricsCollector` tracks:

- **Per-document metrics:**
  - Processing time
  - Number of indicators extracted
  - Validation statistics (valid/invalid/warnings)
  - Confidence score statistics (avg/min/max)
  - ESG scores (overall and pillar scores)
  - API usage (calls and errors)
  - Error tracking

- **Aggregate metrics:**
  - Total documents processed
  - Success/failure rates
  - Total indicators extracted
  - Validation success rates
  - Processing time statistics
  - API usage and error rates

### 2. Health Checks

The `HealthChecker` monitors:

- Database connectivity
- RabbitMQ connectivity
- Google GenAI API availability
- Service uptime
- Last successful/failed extraction timestamps

### 3. HTTP Endpoints

The service exposes HTTP endpoints for monitoring:

- `GET /health` - Health check endpoint
  - Returns 200 if healthy, 503 if unhealthy
  - Includes status of all components
  
- `GET /metrics` - Metrics endpoint
  - Returns aggregate metrics
  - Returns recent document metrics (last 10)

- `GET /` - Service information

## Usage

### Accessing Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics

# Service info
curl http://localhost:8080/
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "uptime_seconds": 3600.5,
  "components": {
    "database": {
      "name": "database",
      "status": "healthy",
      "message": "Database connection successful",
      "last_check": "2024-01-15T10:30:00",
      "response_time_ms": 15.2
    },
    "rabbitmq": {
      "name": "rabbitmq",
      "status": "healthy",
      "message": "RabbitMQ connection successful",
      "last_check": "2024-01-15T10:30:00",
      "response_time_ms": 8.5
    }
  },
  "last_successful_extraction": "2024-01-15T10:29:45",
  "last_failed_extraction": null
}
```

### Metrics Response

```json
{
  "aggregate": {
    "total_documents_processed": 10,
    "successful_documents": 9,
    "failed_documents": 1,
    "success_rate": 0.9,
    "total_indicators_extracted": 450,
    "total_indicators_valid": 430,
    "total_indicators_invalid": 20,
    "validation_success_rate": 0.956,
    "total_processing_time_seconds": 1250.5,
    "avg_processing_time_seconds": 125.05,
    "min_processing_time_seconds": 95.2,
    "max_processing_time_seconds": 180.3,
    "avg_confidence_score": 0.87,
    "total_api_calls": 500,
    "total_api_errors": 5,
    "api_error_rate": 0.01
  },
  "recent_documents": [
    {
      "object_key": "RELIANCE/2024_BRSR.pdf",
      "company_name": "RELIANCE",
      "report_year": 2024,
      "success": true,
      "processing_time_seconds": 125.5,
      "indicators_extracted": 45,
      "indicators_valid": 43,
      "indicators_invalid": 2,
      "avg_confidence_score": 0.89,
      "overall_esg_score": 75.5
    }
  ]
}
```

## Configuration

Set the health check port in environment variables:

```bash
HEALTH_PORT=8080
```

## Docker Integration

The health endpoint can be used for Docker health checks:

```yaml
services:
  extraction:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Logging

All metrics are also logged with structured logging:

```python
logger.info(
    "Document metrics for RELIANCE/2024_BRSR.pdf",
    extra={"document_metrics": {...}}
)

logger.info(
    "Aggregate extraction metrics",
    extra={"aggregate_metrics": {...}}
)
```

## Requirements

Implements requirement 9.4:
- Track extraction metrics (indicators extracted, confidence scores, processing time)
- Expose health check endpoint
- Log processing statistics per document
- Track API usage and costs
