# ESG Platform - Airflow Migration Guide

This guide explains how to migrate from the queue-based architecture to Airflow orchestration.

## Overview

### Current Architecture (Queue-based)

```
Ingestion → RabbitMQ → Embeddings (always running) → RabbitMQ → Extraction (always running)
```

**Issues:**
- Services constantly running, consuming resources
- No visibility into pipeline progress
- Manual queue monitoring required
- Difficult to retry failed tasks
- No built-in scheduling

### New Architecture (Airflow-based)

```
Airflow DAG → Ingestion (on-demand) → Embeddings (on-demand) → Extraction (on-demand)
```

**Benefits:**
- Services start only when needed
- Visual pipeline monitoring
- Built-in retry and error handling
- Easy scheduling and triggering
- Better resource utilization

## Migration Steps

### Step 1: Backup Current Data

```bash
cd infra

# Backup database
make db-backup

# Backup MinIO data (optional)
docker run --rm \
  -v esg-platform_minio_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### Step 2: Stop Current Services

```bash
# Stop all services
make stop

# Or stop specific worker services
docker-compose stop embeddings extraction
```

### Step 3: Start with Airflow

```bash
# Start all services with Airflow
make start-airflow

# Wait for services to be healthy (2-3 minutes)
watch -n 5 'docker-compose -f docker-compose.yml -f docker-compose.airflow.yml ps'
```

### Step 4: Verify Airflow Setup

```bash
# Check Airflow health
curl http://localhost:8081/health

# List DAGs
make airflow-list-dags

# Should show: esg_pipeline

# Open Airflow UI
make open-airflow
# Login: admin / admin
```

### Step 5: Test Pipeline

```bash
# Trigger test run with one company
docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline \
  --conf '{"companies": ["RELIANCE"], "skip_company_sync": true}'

# Monitor in UI
# Go to http://localhost:8081
# Click on "esg_pipeline" DAG
# Watch the Graph View
```

### Step 6: Verify Results

```bash
# Check database for results
docker exec esg-postgres psql -U drfitz -d moz -c "
  SELECT 
    cc.symbol,
    COUNT(DISTINCT ei.id) as indicators,
    COUNT(DISTINCT es.id) as scores
  FROM company_catalog cc
  LEFT JOIN extracted_indicators ei ON cc.id = ei.company_id
  LEFT JOIN esg_scores es ON cc.id = es.company_id
  WHERE cc.symbol = 'RELIANCE'
  GROUP BY cc.symbol;
"
```

## Configuration Changes

### Environment Variables

**No longer needed (queue-based):**
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_DEFAULT_USER`
- `RABBITMQ_DEFAULT_PASS`
- `QUEUE_NAME`
- `EXTRACTION_QUEUE_NAME`

**New (Airflow):**
- `AIRFLOW_UID` - User ID for Airflow (default: 50000)
- `AIRFLOW__*` - Airflow configuration variables

### Service Modifications

**Embeddings Service:**
- Old: `src/main.py` (queue consumer)
- New: `src/batch_processor.py` (batch processor)

**Extraction Service:**
- Old: `main.py` (queue consumer)
- New: `src/batch_extractor.py` (batch processor)

**Ingestion Service:**
- Modified to accept `COMPANIES` env var for filtering

## Usage Patterns

### Manual Trigger (Ad-hoc)

```bash
# Trigger for all companies
make airflow-trigger

# Trigger for specific companies
make airflow-trigger-companies COMPANIES="RELIANCE,TCS,INFY"

# Trigger via API
curl -X POST "http://localhost:8081/api/v1/dags/esg_pipeline/dagRuns" \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d '{"conf": {"companies": ["RELIANCE"]}}'
```

### Scheduled Runs

Edit `services/airflow/dags/esg_pipeline_dag.py`:

```python
# Run daily at 2 AM
schedule_interval='0 2 * * *'

# Run weekly on Monday
schedule_interval='0 3 * * 1'

# Run monthly on 1st
schedule_interval='0 4 1 * *'
```

### Monitoring

**Via UI:**
1. Open http://localhost:8081
2. Click on DAG name
3. View:
   - Graph View - Task dependencies
   - Tree View - Historical runs
   - Gantt View - Task duration
   - Task Duration - Performance trends

**Via CLI:**
```bash
# List recent runs
make airflow-list-runs

# View task logs
docker exec esg-airflow-scheduler \
  airflow tasks logs esg_pipeline ingestion <execution_date>

# Check task status
docker exec esg-airflow-scheduler \
  airflow tasks state esg_pipeline ingestion <execution_date>
```

## Rollback Plan

If you need to rollback to queue-based architecture:

### Step 1: Stop Airflow

```bash
make stop-airflow
```

### Step 2: Start Original Services

```bash
make start
```

### Step 3: Verify Queue Workers

```bash
# Check embeddings worker
docker logs esg-embeddings --tail 50

# Check extraction worker
docker logs esg-extraction --tail 50

# Should see: "Waiting for messages..."
```

### Step 4: Test Queue Flow

```bash
# Trigger ingestion
docker exec esg-ingestion uv run python src/main.py

# Monitor queues
docker exec esg-rabbitmq rabbitmqctl list_queues
```

## Comparison

| Feature | Queue-based | Airflow-based |
|---------|-------------|---------------|
| Resource Usage | High (always running) | Low (on-demand) |
| Visibility | Manual monitoring | Visual DAG UI |
| Retry Logic | Manual | Built-in |
| Scheduling | External cron | Built-in scheduler |
| Debugging | Log files | UI + logs |
| Scalability | Add workers | Dynamic tasks |
| Cost | Higher (24/7 running) | Lower (pay per run) |

## Best Practices

### 1. Start Small

Test with 1-2 companies before running full pipeline:

```bash
docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline \
  --conf '{"companies": ["RELIANCE", "TCS"]}'
```

### 2. Monitor First Runs

Watch the first few runs closely:
- Check task logs for errors
- Verify data quality
- Monitor resource usage

### 3. Set Appropriate Timeouts

Edit DAG file for your environment:

```python
default_args = {
    'execution_timeout': timedelta(hours=2),  # Max task duration
    'retries': 2,  # Retry failed tasks
    'retry_delay': timedelta(minutes=5),
}
```

### 4. Use Alerting

Configure email alerts for failures:

```python
default_args = {
    'email': ['team@example.com'],
    'email_on_failure': True,
}
```

### 5. Regular Cleanup

Clean up old DAG runs:

```bash
# Keep last 30 days
docker exec esg-airflow-scheduler \
  airflow dags delete --yes esg_pipeline --keep-last 30
```

## Troubleshooting

### DAG Not Appearing

```bash
# Check for import errors
docker exec esg-airflow-scheduler airflow dags list-import-errors

# Check DAG file syntax
docker exec esg-airflow-scheduler python -m py_compile /opt/airflow/dags/esg_pipeline_dag.py
```

### Task Failing

```bash
# View task logs
docker exec esg-airflow-scheduler \
  airflow tasks logs esg_pipeline <task_id> <execution_date>

# Test task manually
docker exec esg-airflow-scheduler \
  airflow tasks test esg_pipeline <task_id> <execution_date>
```

### Docker Socket Permission

```bash
# Add airflow user to docker group
docker exec -u root esg-airflow-scheduler usermod -aG docker airflow
docker restart esg-airflow-scheduler
```

### Database Connection

```bash
# Check Airflow database
docker exec esg-airflow-scheduler airflow db check

# Reset if needed (⚠️ deletes history)
docker exec esg-airflow-scheduler airflow db reset
```

## Performance Tuning

### Parallel Processing

Increase parallelism in `docker-compose.airflow.yml`:

```yaml
environment:
  AIRFLOW__CORE__PARALLELISM: 32
  AIRFLOW__CORE__DAG_CONCURRENCY: 16
```

### Resource Limits

Add resource limits to prevent overload:

```yaml
services:
  airflow-scheduler:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Batch Size

Adjust batch size in DAG parameters:

```python
params={
    'batch_size': 10,  # Process 10 companies at once
}
```

## FAQ

**Q: Can I keep RabbitMQ for other uses?**
A: Yes, RabbitMQ can remain for other messaging needs. Just don't use it for the main pipeline.

**Q: What happens to existing queue messages?**
A: They'll remain in queues. Drain them before migration or clear queues.

**Q: Can I run both architectures simultaneously?**
A: Not recommended. Choose one to avoid duplicate processing.

**Q: How do I schedule different companies on different days?**
A: Create multiple DAGs or use branching logic in a single DAG.

**Q: What if a task fails midway?**
A: Airflow will retry automatically. You can also manually re-run from the UI.

**Q: How do I process urgent requests?**
A: Trigger DAG manually with specific companies via CLI or API.

## Support

For issues:
1. Check Airflow logs: `make logs-airflow`
2. Check DAG import errors in UI
3. Test tasks manually: `airflow tasks test`
4. Review service logs for Docker tasks
5. Consult [Airflow Documentation](https://airflow.apache.org/docs/)

## Next Steps

After successful migration:

1. **Remove queue-based code** (optional)
   - Remove queue consumer loops
   - Remove RabbitMQ service (if not needed)

2. **Set up monitoring**
   - Configure email alerts
   - Integrate with Prometheus/Grafana
   - Set up PagerDuty for critical failures

3. **Optimize performance**
   - Tune parallelism settings
   - Add resource limits
   - Implement caching where appropriate

4. **Document workflows**
   - Create runbooks for common operations
   - Document troubleshooting procedures
   - Train team on Airflow UI

5. **Plan for scale**
   - Consider CeleryExecutor for distributed processing
   - Evaluate KubernetesExecutor for cloud deployment
   - Implement auto-scaling policies
