# Monitoring and Metrics Implementation

This document describes the monitoring and metrics implementation for the extraction service.

## Overview

The extraction service now includes comprehensive monitoring and metrics tracking capabilities:

1. **Metrics Collection** - Track extraction performance, validation statistics, and API usage
2. **Health Checks** - Monitor service and component health
3. **HTTP Endpoints** - Expose metrics and health status via HTTP

## Features

### 1. Metrics Collection

The `MetricsCollector` tracks detailed metrics for each document processed:

#### Per-Document Metrics
- Processing time (start to finish)
- Number of indicators extracted
- Validation statistics (valid/invalid/warnings)
- Confidence score statistics (average, min, max)
- ESG scores (overall and pillar scores)
- API usage (total calls and errors)
- Error tracking (error message and type)

#### Aggregate Metrics
- Total documents processed
- Success/failure rates
- Total indicators extracted across all documents
- Validation success rates
- Processing time statistics (avg, min, max)
- Average confidence scores
- API usage and error rates
- First and last document timestamps

### 2. Health Checks

The `HealthChecker` monitors service health:

#### Component Health
- **Database** - PostgreSQL connectivity and response time
- **RabbitMQ** - Message queue connectivity
- **Google GenAI** - API availability (optional check)

#### Service Health
- Overall service status (healthy/degraded/unhealthy)
- Service uptime
- Last successful extraction timestamp
- Last failed extraction timestamp

### 3. HTTP Endpoints

The service exposes HTTP endpoints for monitoring:

#### `GET /health`
Returns service health status.

**Response (200 OK if healthy, 503 if unhealthy):**
```json
{
  "status": "healthy",
  "timestamp": "2024-10-27T14:30:00",
  "uptime_seconds": 3600.5,
  "components": {
    "database": {
      "name": "database",
      "status": "healthy",
      "message": "Database connection successful",
      "last_check": "2024-10-27T14:30:00",
      "response_time_ms": 15.2
    },
    "rabbitmq": {
      "name": "rabbitmq",
      "status": "healthy",
      "message": "RabbitMQ connection successful",
      "last_check": "2024-10-27T14:30:00",
      "response_time_ms": 8.5
    }
  },
  "last_successful_extraction": "2024-10-27T14:29:45",
  "last_failed_extraction": null
}
```

#### `GET /metrics`
Returns aggregate and recent document metrics.

**Response (200 OK):**
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
    "api_error_rate": 0.01,
    "first_document_time": "2024-10-27T10:00:00",
    "last_document_time": "2024-10-27T14:30:00"
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
      "validation_warnings": 3,
      "avg_confidence_score": 0.89,
      "min_confidence_score": 0.75,
      "max_confidence_score": 0.98,
      "overall_esg_score": 75.5,
      "environmental_score": 72.0,
      "social_score": 78.0,
      "governance_score": 76.5,
      "api_calls": 50,
      "api_errors": 1,
      "error_message": null,
      "error_type": null
    }
  ]
}
```

#### `GET /`
Returns service information and available endpoints.

**Response (200 OK):**
```json
{
  "service": "ESG Extraction Service",
  "endpoints": {
    "/health": "Health check endpoint",
    "/metrics": "Metrics endpoint"
  }
}
```

## Configuration

### Environment Variables

```bash
# Monitoring configuration
HEALTH_PORT=8080  # Port for health check and metrics HTTP server
```

### Docker Configuration

The Dockerfile exposes port 8080 for health checks:

```dockerfile
EXPOSE 8080
```

### Docker Compose

Add health check configuration to docker-compose.yml:

```yaml
services:
  extraction:
    build:
      context: ./services/extraction
      dockerfile: Dockerfile
    ports:
      - "8080:8080"  # Expose health check port
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    environment:
      HEALTH_PORT: 8080
```

## Usage

### Local Development

```bash
# Start the service
uv run python main.py

# In another terminal, check health
curl http://localhost:8080/health

# Check metrics
curl http://localhost:8080/metrics
```

### Docker

```bash
# Build and run
docker-compose up extraction

# Check health
curl http://localhost:8080/health

# Check metrics
curl http://localhost:8080/metrics
```

### Kubernetes

For Kubernetes deployments, configure liveness and readiness probes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: extraction-service
spec:
  containers:
  - name: extraction
    image: extraction-service:latest
    ports:
    - containerPort: 8080
      name: health
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
```

## Logging

All metrics are also logged with structured logging for integration with log aggregation systems:

```python
# Document metrics are logged when processing completes
logger.info(
    "Document metrics for RELIANCE/2024_BRSR.pdf",
    extra={"document_metrics": {
        "object_key": "RELIANCE/2024_BRSR.pdf",
        "success": true,
        "processing_time_seconds": 125.5,
        "indicators_extracted": 45,
        # ... full metrics
    }}
)

# Aggregate metrics are logged on shutdown
logger.info(
    "Aggregate extraction metrics",
    extra={"aggregate_metrics": {
        "total_documents_processed": 10,
        "success_rate": 0.9,
        # ... full aggregate metrics
    }}
)
```

## Monitoring Integration

### Prometheus

To integrate with Prometheus, you can:

1. Use a log exporter to parse structured logs
2. Add a Prometheus client library to expose metrics in Prometheus format
3. Use the HTTP endpoints with a custom exporter

### Grafana

Create dashboards using:
- Processing time trends
- Success/failure rates
- Validation statistics
- API usage and error rates
- Confidence score distributions

### ELK Stack

The structured logging format is compatible with Elasticsearch:

```json
{
  "@timestamp": "2024-10-27T14:30:00",
  "level": "INFO",
  "message": "Document metrics for RELIANCE/2024_BRSR.pdf",
  "document_metrics": {
    "object_key": "RELIANCE/2024_BRSR.pdf",
    "success": true,
    "processing_time_seconds": 125.5
  }
}
```

## Testing

Run the monitoring tests:

```bash
# Test metrics collector and health checker
uv run python tests/test_monitoring.py

# Test HTTP server
uv run python tests/test_http_server.py
```

## Requirements

This implementation satisfies requirement 9.4:
- ✅ Track extraction metrics (indicators extracted, confidence scores, processing time)
- ✅ Expose health check endpoint
- ✅ Log processing statistics per document
- ✅ Track API usage and costs

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Extraction Service                        │
│                                                              │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Main Worker    │  │  Metrics     │  │  Health        │  │
│  │                │──│  Collector   │  │  Checker       │  │
│  │ - Process docs │  │              │  │                │  │
│  │ - Track metrics│  │ - Per-doc    │  │ - DB health    │  │
│  │ - Update health│  │ - Aggregate  │  │ - RabbitMQ     │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
│           │                  │                  │           │
│           └──────────────────┴──────────────────┘           │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │  HTTP Server      │                    │
│                    │  (Port 8080)      │                    │
│                    │                   │                    │
│                    │  GET /health      │                    │
│                    │  GET /metrics     │                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    External Monitoring
                    - Docker health checks
                    - Kubernetes probes
                    - Prometheus/Grafana
                    - Log aggregation
```

## Future Enhancements

Potential improvements:
1. Add Prometheus metrics format support
2. Add custom alerting rules
3. Add performance profiling
4. Add distributed tracing (OpenTelemetry)
5. Add cost estimation per document
6. Add SLA tracking
