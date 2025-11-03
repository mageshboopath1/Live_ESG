# ESG Pipeline Scripts

This directory contains scripts for testing, orchestrating, and managing the ESG Intelligence Platform pipeline.

## Overview

The scripts provide end-to-end testing, data cleanup, and pipeline orchestration capabilities for the ESG platform.

## Scripts

### Pipeline Testing

**`test_pipeline_e2e.py`** - Comprehensive end-to-end pipeline testing

Tests the complete pipeline flow from ingestion through extraction with detailed reporting.

```bash
# Quick test (3 companies)
python test_pipeline_e2e.py --scenario quick

# Standard test (5 companies)
python test_pipeline_e2e.py --scenario standard

# Test specific companies
python test_pipeline_e2e.py --companies RELIANCE TCS INFY

# Skip cleanup for faster iteration
python test_pipeline_e2e.py --scenario quick --skip-cleanup
```

See [E2E_TEST_README.md](E2E_TEST_README.md) for detailed documentation.

### Data Cleanup

**`cleanup_pipeline_data.py`** - Clean all pipeline data

Removes all data from database, MinIO, and RabbitMQ for fresh testing.

```bash
# Interactive mode (with confirmation)
python cleanup_pipeline_data.py

# Force mode (no confirmation)
python cleanup_pipeline_data.py --force
```

See [CLEANUP_README.md](CLEANUP_README.md) for detailed documentation.

### Pipeline Orchestration

**`pipeline_orchestrator.py`** - Core orchestration logic

Provides the orchestration framework used by the E2E test script. Not typically run directly.

**`pipeline_config.py`** - Centralized configuration

Configuration management for all pipeline scripts.

### Task Publishing

**`publish_extraction_tasks.py`** - Publish extraction tasks to RabbitMQ

Manually trigger extraction tasks for specific reports.

**`trigger_extraction.py`** - Trigger extraction for specific companies

Convenience script for triggering extraction jobs.

### Service Verification

**`verify_extraction_service.sh`** - Verify extraction service health

Quick health check for the extraction service.

```bash
./verify_extraction_service.sh
```

## Quick Start

### Prerequisites

```bash
# Install dependencies
uv sync

# Or with pip
pip install -r requirements.txt
```

### Environment Setup

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running Tests

```bash
# Quick validation
python test_pipeline_e2e.py --scenario quick

# Full test
python test_pipeline_e2e.py --scenario comprehensive
```

## Test Scenarios

| Scenario | Companies | Embedding Timeout | Extraction Timeout | Use Case |
|----------|-----------|-------------------|-------------------|----------|
| quick | 3 | 30 min | 1 hour | Rapid validation |
| standard | 5 | 1 hour | 2 hours | Regular testing |
| comprehensive | 10 | 2 hours | 4 hours | Pre-release validation |
| full | All | 4 hours | 8 hours | Complete system test |

## Environment Variables

### Database
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: moz)
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password

### MinIO
- `MINIO_ENDPOINT` - MinIO endpoint (default: http://localhost:9000)
- `MINIO_ACCESS_KEY` - MinIO access key
- `MINIO_SECRET_KEY` - MinIO secret key
- `BUCKET_NAME` - Bucket name (default: esg-reports)

### RabbitMQ
- `RABBITMQ_HOST` - RabbitMQ host (default: localhost)
- `RABBITMQ_PORT` - RabbitMQ port (default: 5672)
- `RABBITMQ_DEFAULT_USER` - RabbitMQ user
- `RABBITMQ_DEFAULT_PASS` - RabbitMQ password
- `QUEUE_NAME` - Embedding queue (default: embedding-tasks)
- `EXTRACTION_QUEUE_NAME` - Extraction queue (default: extraction-tasks)

## Test Reports

Test reports are saved to `test_reports/` directory:

- `test_report_<scenario>_<timestamp>.txt` - Human-readable report
- `test_report_<scenario>_<timestamp>.json` - Machine-readable report
- `test_<scenario>_<timestamp>.log` - Detailed execution log

## Common Workflows

### Fresh Pipeline Test

```bash
# 1. Clean all data
python cleanup_pipeline_data.py --force

# 2. Run E2E test
python test_pipeline_e2e.py --scenario standard

# 3. Review report
cat test_reports/test_report_standard_*.txt
```

### Incremental Testing

```bash
# Test without cleanup (faster iteration)
python test_pipeline_e2e.py --scenario quick --skip-cleanup
```

### Specific Company Testing

```bash
# Test specific companies
python test_pipeline_e2e.py --companies RELIANCE TCS --skip-cleanup
```

## Troubleshooting

### Services Not Running

Ensure all services are up:
```bash
cd ../infra
docker-compose ps
```

### Connection Errors

Check environment variables in `.env` match your Docker setup.

### Test Timeouts

Increase timeouts for slower systems:
```bash
export EMBEDDING_TIMEOUT=7200  # 2 hours
export EXTRACTION_TIMEOUT=14400  # 4 hours
python test_pipeline_e2e.py --scenario standard
```

## CI/CD Integration

```bash
# Exit code 0 on success, 1 on failure
python test_pipeline_e2e.py --scenario quick --force-cleanup --no-report

if [ $? -eq 0 ]; then
    echo "✓ Pipeline test passed"
else
    echo "✗ Pipeline test failed"
    exit 1
fi
```

## Related Documentation

- [E2E Test Documentation](E2E_TEST_README.md) - Detailed E2E testing guide
- [Cleanup Documentation](CLEANUP_README.md) - Data cleanup guide
- [Infrastructure Setup](../infra/README.md) - Docker setup guide
- [Main README](../README.md) - Project overview

## Support

For issues:
1. Check service logs: `cd ../infra && docker-compose logs`
2. Verify environment configuration in `.env`
3. Review test reports in `test_reports/`
4. Check service health endpoints
