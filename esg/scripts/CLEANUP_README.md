# Pipeline Data Cleanup Script

## Overview

The `cleanup_pipeline_data.py` script provides comprehensive cleanup of all ESG pipeline data across MinIO, PostgreSQL, and RabbitMQ. This enables fresh pipeline testing from a clean state.

## What Gets Cleaned

### Database Tables
- `document_embeddings` - All vector embeddings
- `extracted_indicators` - All extracted BRSR indicators
- `esg_scores` - All calculated ESG scores
- `ingestion_metadata` - All ingestion tracking records

**Note:** The `company_catalog` table is preserved by default to maintain company reference data.

### MinIO Storage
- All objects in the `esg-reports` bucket

### RabbitMQ Queues
- `embedding-tasks` - All pending embedding jobs
- `extraction-tasks` - All pending extraction jobs

## Usage

### Interactive Mode (with confirmation)
```bash
cd scripts
python cleanup_pipeline_data.py
```

This will:
1. Connect to all services
2. Display a summary of data to be deleted
3. Prompt for confirmation
4. Execute cleanup if confirmed
5. Display summary of deleted items

### Force Mode (no confirmation)
```bash
python cleanup_pipeline_data.py --force
```

Use this for automated scripts or when you're certain you want to proceed.

## Environment Variables

The script uses the following environment variables (with defaults):

### Database
- `DB_HOST` (default: localhost)
- `DB_PORT` (default: 5432)
- `DB_NAME` (default: moz)
- `DB_USER` (default: drfitz)
- `DB_PASSWORD` (default: h4i1hydr4)

### MinIO
- `MINIO_ENDPOINT` (default: http://localhost:9000)
- `MINIO_ACCESS_KEY` (default: esg_minio)
- `MINIO_SECRET_KEY` (default: esg_secret)
- `BUCKET_NAME` (default: esg-reports)
- `MINIO_SECURE` (default: false)

### RabbitMQ
- `RABBITMQ_HOST` (default: localhost)
- `RABBITMQ_PORT` (default: 5672)
- `RABBITMQ_DEFAULT_USER` (default: esg_rabbitmq)
- `RABBITMQ_DEFAULT_PASS` (default: esg_secret)
- `QUEUE_NAME` (default: embedding-tasks)
- `EXTRACTION_QUEUE_NAME` (default: extraction-tasks)

## Requirements

Install dependencies:
```bash
cd scripts
uv sync
```

Or with pip:
```bash
pip install psycopg2-binary pika boto3
```

## Error Handling

The script includes robust error handling:

- **MinIO failures**: Logged but don't stop other cleanups
- **Database failures**: Transaction rollback ensures data integrity
- **RabbitMQ failures**: Logged but don't stop other cleanups

If database cleanup fails, the transaction is rolled back and no data is deleted.

## Safety Features

1. **Confirmation prompt**: Requires explicit "yes" to proceed (unless --force)
2. **Summary display**: Shows what will be deleted before proceeding
3. **Transaction safety**: Database operations use transactions with rollback
4. **Detailed logging**: Clear output of what's being deleted
5. **Final summary**: Shows exactly what was deleted

## Example Output

```
======================================================================
ESG Pipeline Data Cleanup
======================================================================

📊 Connecting to database...
🔍 Analyzing current data...

Data to be deleted:
======================================================================

📊 Database Tables:
  • document_embeddings: 1,234 records
  • extracted_indicators: 567 records
  • esg_scores: 45 records
  • ingestion_metadata: 89 records

📦 MinIO Storage:
  • esg-reports: 45 objects

📨 RabbitMQ Queues:
  • embedding-tasks: 12 messages
  • extraction-tasks: 5 messages

⚠️  WARNING: This will permanently delete all pipeline data!
⚠️  This action cannot be undone.

Do you want to proceed? (yes/no): yes

🗑️  Executing cleanup...

  Cleaning MinIO storage...
  ✓ Deleted 45 objects from MinIO

  Cleaning database tables...
  ✓ Deleted 45 records from esg_scores
  ✓ Deleted 567 records from extracted_indicators
  ✓ Deleted 1,234 records from document_embeddings
  ✓ Deleted 89 records from ingestion_metadata

  Cleaning RabbitMQ queues...
  ✓ Purged 12 messages from embedding-tasks
  ✓ Purged 5 messages from extraction-tasks

======================================================================
✓ Cleanup completed successfully!
======================================================================

📊 Summary:

  Database:
    • esg_scores: 45 records deleted
    • extracted_indicators: 567 records deleted
    • document_embeddings: 1,234 records deleted
    • ingestion_metadata: 89 records deleted

  MinIO:
    • 45 objects deleted

  RabbitMQ:
    • embedding-tasks: 12 messages purged
    • extraction-tasks: 5 messages purged

  Total items cleaned: 1,997
```

## Integration with Pipeline Testing

This script is designed to be used as the first step in end-to-end pipeline testing:

1. **Cleanup**: Run this script to clear all data
2. **Ingestion**: Run ingestion service to process PDFs
3. **Embedding**: Wait for embedding service to complete
4. **Extraction**: Wait for extraction service to complete
5. **Validation**: Verify all data was processed correctly

See the pipeline orchestrator script for automated end-to-end testing.

## Troubleshooting

### Connection Errors

If you get connection errors, verify services are running:
```bash
docker ps | grep -E "postgres|minio|rabbitmq"
```

### Permission Errors

Ensure the script has execute permissions:
```bash
chmod +x cleanup_pipeline_data.py
```

### MinIO Bucket Not Found

If the bucket doesn't exist, the script will report 0 objects deleted and continue.

### Queue Not Found

If queues don't exist, the script will report 0 messages purged and continue.
