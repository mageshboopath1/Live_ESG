# ESG Platform - Airflow Orchestration

This directory contains Apache Airflow configuration for orchestrating the ESG Intelligence Platform pipeline.

## Why Airflow?

**Before (Queue-based):**
- Services constantly running, listening to RabbitMQ queues
- Resource-intensive (always consuming memory/CPU)
- Harder to monitor and debug
- No built-in retry/failure handling UI
- Manual queue management

**After (Airflow-based):**
- Services start only when needed
- Better resource utilization
- Visual DAG monitoring and debugging
- Built-in retry, alerting, and logging
- Easy to trigger manually or via API
- Clear dependency management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow Scheduler                         │
│                  (Monitors DAGs, triggers tasks)             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DAG: esg_pipeline                       │
│                                                              │
│  1. Preflight Check (Python)                                │
│  2. Company Catalog Sync (Docker: company-catalog)          │
│  3. Ingestion (Docker: ingestion)                           │
│  4. Embeddings (Docker: embeddings batch_processor)         │
│  5. Extraction (Docker: extraction batch_extractor)         │
│  6. Validation & Report (Python)                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

Each stage runs as a Docker container task, started on-demand by Airflow.

## Quick Start

### 1. Start Airflow with the Platform

```bash
cd infra

# Start all services including Airflow
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml up -d

# Or using make (if added to Makefile)
make start-with-airflow
```

### 2. Access Airflow UI

Open http://localhost:8081

**Default credentials:**
- Username: `admin`
- Password: `admin`

### 3. Trigger the Pipeline

**Via UI:**
1. Go to http://localhost:8081
2. Find the `esg_pipeline` DAG
3. Click the "Play" button
4. Configure parameters (optional):
   - `companies`: List of company symbols (e.g., `["RELIANCE", "TCS"]`)
   - `report_year`: Specific year or leave empty for latest
   - `skip_company_sync`: Skip company catalog sync (default: true)
   - `batch_size`: Number of companies to process at once

**Via CLI:**
```bash
# Trigger with default parameters
docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline

# Trigger with specific companies
docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline \
  --conf '{"companies": ["RELIANCE", "TCS", "INFY"]}'

# Trigger for specific year
docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline \
  --conf '{"companies": ["RELIANCE"], "report_year": 2023}'
```

**Via API:**
```bash
# Trigger via REST API
curl -X POST "http://localhost:8081/api/v1/dags/esg_pipeline/dagRuns" \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d '{
    "conf": {
      "companies": ["RELIANCE", "TCS"],
      "report_year": null,
      "skip_company_sync": true
    }
  }'
```

## DAG Configuration

### Parameters

The `esg_pipeline` DAG accepts the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `companies` | list | `[]` | List of company symbols to process. Empty = all companies |
| `report_year` | int | `null` | Specific year to process. Null = latest available |
| `skip_company_sync` | bool | `true` | Skip company catalog sync stage |
| `batch_size` | int | `5` | Number of companies to process in parallel |

### Schedule

By default, the DAG has `schedule_interval=None` (manual trigger only).

To enable scheduled runs, edit `dags/esg_pipeline_dag.py`:

```python
# Run daily at 2 AM
schedule_interval='0 2 * * *'

# Run weekly on Monday at 3 AM
schedule_interval='0 3 * * 1'

# Run monthly on 1st at 4 AM
schedule_interval='0 4 1 * *'
```

## Monitoring

### View DAG Runs

1. Go to http://localhost:8081
2. Click on `esg_pipeline` DAG
3. View:
   - **Graph View**: Visual representation of task dependencies
   - **Tree View**: Historical runs and task status
   - **Gantt View**: Task duration and parallelism
   - **Task Duration**: Performance over time

### View Logs

**Via UI:**
1. Click on a task in the DAG
2. Click "Log" button
3. View real-time logs

**Via CLI:**
```bash
# View scheduler logs
docker logs esg-airflow-scheduler -f

# View webserver logs
docker logs esg-airflow-webserver -f

# View task logs
docker exec esg-airflow-scheduler airflow tasks logs esg_pipeline ingestion 2024-01-01
```

### Metrics

Airflow provides built-in metrics:
- Task success/failure rates
- Task duration
- DAG run duration
- Scheduler performance

Access via:
- Airflow UI: Browse → Task Instances
- Prometheus (if configured)
- StatsD (if configured)

## Service Modifications

### Embeddings Service

**New file:** `services/embeddings/src/batch_processor.py`

Processes multiple documents in batch mode:
```python
# Reads DOCUMENTS env var
DOCUMENTS="RELIANCE/2024_BRSR.pdf,TCS/2024_BRSR.pdf"
python src/batch_processor.py
```

### Extraction Service

**New file:** `services/extraction/src/batch_extractor.py`

Processes multiple documents in batch mode:
```python
# Reads DOCUMENTS env var
DOCUMENTS="RELIANCE/2024_BRSR.pdf,TCS/2024_BRSR.pdf"
python src/batch_extractor.py
```

### Ingestion Service

**Modified:** `services/ingestion/src/main.py`

Now accepts company filter via env var:
```python
# Process specific companies
COMPANIES="RELIANCE,TCS,INFY"
python src/main.py
```

## Migration from Queue-based

### What Changes?

**Remove:**
- RabbitMQ service (optional, can keep for other uses)
- Queue consumer loops in embeddings/extraction services
- Queue monitoring scripts

**Keep:**
- All database schemas
- MinIO storage
- API Gateway
- Frontend
- Core processing logic

### Migration Steps

1. **Stop old services:**
   ```bash
   docker-compose down
   ```

2. **Start with Airflow:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.airflow.yml up -d
   ```

3. **Verify services:**
   ```bash
   # Check Airflow
   curl http://localhost:8081/health
   
   # Check database
   docker exec esg-postgres pg_isready
   
   # Check MinIO
   curl http://localhost:9000/minio/health/live
   ```

4. **Trigger test run:**
   ```bash
   docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline \
     --conf '{"companies": ["RELIANCE"], "skip_company_sync": true}'
   ```

5. **Monitor in UI:**
   - Open http://localhost:8081
   - Watch the DAG run progress

### Rollback Plan

If you need to rollback to queue-based:

1. Stop Airflow:
   ```bash
   docker-compose -f docker-compose.airflow.yml down
   ```

2. Start original setup:
   ```bash
   docker-compose up -d
   ```

## Advanced Configuration

### Parallel Processing

To process multiple documents in parallel, use dynamic task mapping:

```python
# In DAG file
embeddings = DockerOperator.partial(
    task_id='embeddings',
    image='esg-embeddings:latest',
).expand(
    command=[f'python src/process_single.py {doc}' for doc in documents]
)
```

### Custom Operators

Create custom operators in `plugins/`:

```python
# plugins/esg_operators.py
from airflow.models import BaseOperator

class ESGValidationOperator(BaseOperator):
    def execute(self, context):
        # Custom validation logic
        pass
```

### Alerting

Configure email alerts in `docker-compose.airflow.yml`:

```yaml
environment:
  AIRFLOW__SMTP__SMTP_HOST: smtp.gmail.com
  AIRFLOW__SMTP__SMTP_PORT: 587
  AIRFLOW__SMTP__SMTP_USER: your-email@gmail.com
  AIRFLOW__SMTP__SMTP_PASSWORD: your-password
  AIRFLOW__SMTP__SMTP_MAIL_FROM: airflow@example.com
```

Then in DAG:
```python
default_args = {
    'email': ['team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

### Sensors

Use sensors to wait for external conditions:

```python
from airflow.sensors.filesystem import FileSensor

wait_for_file = FileSensor(
    task_id='wait_for_file',
    filepath='/path/to/trigger/file',
    poke_interval=60,
)
```

## Troubleshooting

### DAG not appearing in UI

```bash
# Check DAG syntax
docker exec esg-airflow-scheduler airflow dags list

# Check for errors
docker exec esg-airflow-scheduler airflow dags list-import-errors
```

### Task failing

1. Check logs in UI
2. Check Docker container logs:
   ```bash
   docker logs <container-name>
   ```
3. Test task manually:
   ```bash
   docker exec esg-airflow-scheduler airflow tasks test esg_pipeline ingestion 2024-01-01
   ```

### Database connection issues

```bash
# Check Airflow database
docker exec esg-airflow-scheduler airflow db check

# Reset database (⚠️ deletes all history)
docker exec esg-airflow-scheduler airflow db reset
```

### Docker socket permission denied

```bash
# Add airflow user to docker group
docker exec -u root esg-airflow-scheduler usermod -aG docker airflow
docker restart esg-airflow-scheduler
```

## Performance Tuning

### Parallelism

Edit `docker-compose.airflow.yml`:

```yaml
environment:
  AIRFLOW__CORE__PARALLELISM: 32  # Max tasks across all DAGs
  AIRFLOW__CORE__DAG_CONCURRENCY: 16  # Max tasks per DAG
  AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG: 3  # Max concurrent DAG runs
```

### Executor

For production, use CeleryExecutor or KubernetesExecutor:

```yaml
environment:
  AIRFLOW__CORE__EXECUTOR: CeleryExecutor
  AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
  AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://...
```

## Production Deployment

### Security

1. **Change default password:**
   ```bash
   docker exec esg-airflow-scheduler airflow users create \
     --username admin \
     --firstname Admin \
     --lastname User \
     --role Admin \
     --email admin@example.com \
     --password <strong-password>
   ```

2. **Use secrets management:**
   - Store credentials in AWS Secrets Manager / Vault
   - Use Airflow Connections for sensitive data

3. **Enable HTTPS:**
   - Configure reverse proxy (nginx)
   - Use SSL certificates

### Scaling

1. **Use CeleryExecutor** with multiple workers
2. **Use KubernetesExecutor** for dynamic scaling
3. **Separate scheduler and webserver** on different nodes
4. **Use external database** (RDS, Cloud SQL)

### Monitoring

1. **Enable StatsD:**
   ```yaml
   AIRFLOW__METRICS__STATSD_ON: 'true'
   AIRFLOW__METRICS__STATSD_HOST: statsd
   AIRFLOW__METRICS__STATSD_PORT: 8125
   ```

2. **Integrate with Prometheus:**
   - Use `airflow-prometheus-exporter`
   - Scrape metrics endpoint

3. **Set up alerting:**
   - Email alerts
   - Slack notifications
   - PagerDuty integration

## Resources

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Docker Operator Guide](https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/operators/docker.html)
- [Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)

## Support

For issues:
1. Check Airflow logs: `docker logs esg-airflow-scheduler`
2. Check DAG import errors in UI
3. Test tasks manually with `airflow tasks test`
4. Review service logs for Docker tasks
