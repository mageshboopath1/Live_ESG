# End-to-End Pipeline Test Script

## Overview

The `test_pipeline_e2e.py` script provides a comprehensive testing framework for the ESG pipeline. It orchestrates all pipeline stages (cleanup, ingestion, embedding, extraction, and validation) and generates detailed test reports with timing and success metrics.

## Features

- **Multiple Test Scenarios**: Pre-configured scenarios for different testing needs
- **Flexible Company Selection**: Test with specific companies or a limited number
- **Incremental Testing**: Option to skip cleanup for faster iteration
- **Detailed Logging**: Comprehensive logging at multiple levels (DEBUG, INFO, WARNING, ERROR)
- **Test Reports**: Generate both text and JSON reports with metrics
- **Performance Metrics**: Track throughput and timing for each stage
- **Validation Checks**: Verify data integrity and completeness

## Test Scenarios

### Quick Test
- **Companies**: 3
- **Embedding Timeout**: 30 minutes
- **Extraction Timeout**: 1 hour
- **Use Case**: Rapid validation during development

### Standard Test (Default)
- **Companies**: 5
- **Embedding Timeout**: 1 hour
- **Extraction Timeout**: 2 hours
- **Use Case**: Balanced coverage for regular testing

### Comprehensive Test
- **Companies**: 10
- **Embedding Timeout**: 2 hours
- **Extraction Timeout**: 4 hours
- **Use Case**: Thorough validation before releases

### Full Pipeline Test
- **Companies**: All available
- **Embedding Timeout**: 4 hours
- **Extraction Timeout**: 8 hours
- **Use Case**: Complete system validation

## Usage

### Basic Usage

```bash
# Run standard test (5 companies)
python scripts/test_pipeline_e2e.py

# Run quick test (3 companies)
python scripts/test_pipeline_e2e.py --scenario quick

# Run comprehensive test (10 companies)
python scripts/test_pipeline_e2e.py --scenario comprehensive
```

### Test with Specific Companies

```bash
# Test with specific companies
python scripts/test_pipeline_e2e.py --companies RELIANCE TCS INFY

# Test with specific companies and skip cleanup
python scripts/test_pipeline_e2e.py --companies RELIANCE TCS --skip-cleanup
```

### Incremental Testing

```bash
# Skip cleanup stage for faster iteration
python scripts/test_pipeline_e2e.py --scenario quick --skip-cleanup

# Force cleanup without confirmation
python scripts/test_pipeline_e2e.py --scenario standard --force-cleanup
```

### Logging and Reports

```bash
# Enable debug logging
python scripts/test_pipeline_e2e.py --scenario quick --log-level DEBUG

# Save reports to specific directory
python scripts/test_pipeline_e2e.py --scenario standard --output-dir ./my_test_reports

# Run without generating report files
python scripts/test_pipeline_e2e.py --scenario quick --no-report
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--scenario` | Test scenario (quick, standard, comprehensive, full) | standard |
| `--companies` | List of company symbols to test | None |
| `--skip-cleanup` | Skip cleanup stage | False |
| `--force-cleanup` | Force cleanup without confirmation | False |
| `--log-level` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `--output-dir` | Directory for test reports | ./test_reports |
| `--no-report` | Do not generate report files | False |

## Test Report

The test script generates comprehensive reports in both text and JSON formats.

### Text Report Contents

1. **Test Information**
   - Test name and scenario
   - Start and end times
   - Total duration

2. **Overall Result**
   - Pass/Fail status
   - Summary message

3. **Stage Results**
   - Cleanup: Items cleaned
   - Ingestion: Duration
   - Embedding: Messages processed and duration
   - Extraction: Messages processed and duration
   - Validation: Checks passed/failed

4. **Data Statistics**
   - Embeddings created
   - Embedding dimensions validation
   - Indicators extracted
   - ESG scores calculated
   - Referential integrity status

5. **Performance Metrics**
   - Embedding throughput (messages/second)
   - Extraction throughput (messages/second)
   - Overall throughput (reports/second)

6. **Errors and Warnings**
   - List of errors encountered
   - List of warnings

7. **Recommendations**
   - Suggested actions for failures

### JSON Report Contents

The JSON report contains all the same information in structured format, plus:
- Pre-test system state
- Post-test system state
- Complete pipeline result data
- Timestamps in ISO format

## Example Output

```
================================================================================
  END-TO-END PIPELINE TEST REPORT
================================================================================

Test Name: E2E Pipeline Test - Standard Test
Scenario: standard
Start Time: 2024-10-31 14:30:00
End Time: 2024-10-31 16:45:30
Total Duration: 2.3h

Overall Result: ✓ PASSED

Stage Results:
--------------------------------------------------------------------------------
  ✓ Cleanup: 1250 items cleaned
  ✓ Ingestion: 5.2m
  ✓ Embedding: 150 messages in 45.3m
  ✓ Extraction: 150 messages in 1.5h
  ✓ Validation: 5/5 checks passed

Data Statistics:
--------------------------------------------------------------------------------
  • Embeddings Created: 15,234
  • Embedding Dimensions: 15,234 total, 0 invalid
  • Indicators Extracted: 2,450 (across 5 reports)
  • ESG Scores Calculated: 5
  • Referential Integrity: ✓ No issues

Performance Metrics:
--------------------------------------------------------------------------------
  • Embedding Throughput: 0.06 messages/second
  • Extraction Throughput: 0.03 messages/second
  • Overall Throughput: 0.0006 reports/second

================================================================================
```

## Integration with CI/CD

The test script can be integrated into CI/CD pipelines:

```bash
# Exit code 0 on success, 1 on failure
python scripts/test_pipeline_e2e.py --scenario quick --force-cleanup --no-report

# Check exit code
if [ $? -eq 0 ]; then
    echo "Pipeline test passed"
else
    echo "Pipeline test failed"
    exit 1
fi
```

## Troubleshooting

### Test Hangs During Embedding Stage

**Possible Causes:**
- Embedding service not running
- Google AI API quota exceeded
- Network connectivity issues

**Solutions:**
- Check embedding service logs
- Verify API key and quota
- Increase embedding timeout

### Test Fails During Validation

**Possible Causes:**
- Incorrect embedding dimensions
- Missing data in database
- Referential integrity issues

**Solutions:**
- Check validation error messages
- Verify database schema
- Review service logs for errors

### Cleanup Fails

**Possible Causes:**
- Database connection issues
- MinIO connection issues
- RabbitMQ connection issues

**Solutions:**
- Verify all services are running
- Check connection credentials
- Review cleanup logs

## Environment Variables

The test script uses the same environment variables as the pipeline orchestrator:

### Database
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: moz)
- `DB_USER`: Database user (default: drfitz)
- `DB_PASSWORD`: Database password

### MinIO
- `MINIO_ENDPOINT`: MinIO endpoint (default: http://localhost:9000)
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `BUCKET_NAME`: Bucket name (default: esg-reports)

### RabbitMQ
- `RABBITMQ_HOST`: RabbitMQ host (default: localhost)
- `RABBITMQ_PORT`: RabbitMQ port (default: 5672)
- `RABBITMQ_DEFAULT_USER`: RabbitMQ user
- `RABBITMQ_DEFAULT_PASS`: RabbitMQ password
- `QUEUE_NAME`: Embedding queue name (default: embedding-tasks)
- `EXTRACTION_QUEUE_NAME`: Extraction queue name (default: extraction-tasks)

### Pipeline Configuration
- `EMBEDDING_TIMEOUT`: Embedding stage timeout in seconds
- `EXTRACTION_TIMEOUT`: Extraction stage timeout in seconds
- `QUEUE_CHECK_INTERVAL`: Queue check interval in seconds
- `EMPTY_QUEUE_WAIT`: Empty queue wait time in seconds

## Best Practices

1. **Start with Quick Tests**: Use the quick scenario during development
2. **Use Incremental Testing**: Skip cleanup when testing specific stages
3. **Save Reports**: Always save reports for later analysis
4. **Monitor Logs**: Use DEBUG level for troubleshooting
5. **Test Specific Companies**: Use known-good companies for faster validation
6. **Check Reports**: Review performance metrics to identify bottlenecks

## Related Scripts

- `pipeline_orchestrator.py`: Core orchestration logic
- `cleanup_pipeline_data.py`: Data cleanup functionality
- `pipeline_config.py`: Centralized configuration

## Requirements

- Python 3.8+
- All pipeline services running (database, MinIO, RabbitMQ, embedding, extraction)
- Valid Google AI API key
- Required Python packages (see pyproject.toml)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review service logs
3. Verify environment configuration
4. Check test reports for detailed error messages
