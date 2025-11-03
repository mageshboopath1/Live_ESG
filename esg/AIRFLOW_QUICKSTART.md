# Airflow Quick Start Guide

Get started with Airflow orchestration in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- ESG platform repository cloned
- `.env` file configured in `infra/` directory

## Quick Start

### 1. Start Services with Airflow

```bash
cd infra
make start-airflow
```

This will start:
- PostgreSQL (with airflow database)
- MinIO
- Redis
- API Gateway
- Frontend
- **Airflow Webserver** (port 8081)
- **Airflow Scheduler**
- **Airflow Triggerer**

Wait 2-3 minutes for all services to be healthy.

### 2. Access Airflow UI

Open http://localhost:8081

**Login:**
- Username: `admin`
- Password: `admin`

### 3. Trigger Your First Pipeline

**Option A: Via UI**
1. Click on the `esg_pipeline` DAG
2. Click the "Play" button (▶️) in the top right
3. Click "Trigger DAG"
4. Watch the Graph View as tasks execute

**Option B: Via Command Line**
```bash
# Trigger for all companies
make airflow-trigger

# Trigger for specific companies
make airflow-trigger-companies COMPANIES="RELIANCE,TCS"
```

**Option C: Via API**
```bash
curl -X POST "http://localhost:8081/api/v1/dags/esg_pipeline/dagRuns" \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d '{
    "conf": {
      "companies": ["RELIANCE"],
      "skip_company_sync": true
    }
  }'
```

### 4. Monitor Progress

In the Airflow UI:
- **Graph View**: See task dependencies and current status
- **Tree View**: See historical runs
- **Gantt View**: See task duration and parallelism
- **Logs**: Click any task → "Log" button

### 5. View Results

Once the pipeline completes (green checkmarks):

```bash
# Check database
docker exec esg-postgres psql -U drfitz -d moz -c "
  SELECT 
    cc.symbol,
    COUNT(DISTINCT ei.id) as indicators,
    es.overall_score
  FROM company_catalog cc
  LEFT JOIN extracted_indicators ei ON cc.id = ei.company_id
  LEFT JOIN esg_scores es ON cc.id = es.company_id
  GROUP BY cc.symbol, es.overall_score
  ORDER BY cc.symbol;
"
```

Or view in the frontend: http://localhost:3000

## Pipeline Stages

The `esg_pipeline` DAG has these stages:

1. **Preflight Check** - Verify database and MinIO connectivity
2. **Company Sync** (optional) - Sync NIFTY 50 company data
3. **Ingestion** - Download PDF reports from company websites
4. **Embeddings** - Generate vector embeddings for semantic search
5. **Extraction** - Extract BRSR indicators using AI
6. **Validation** - Verify data quality and generate report

## Common Commands

```bash
# Start with Airflow
make start-airflow

# Stop Airflow
make stop-airflow

# View Airflow logs
make logs-airflow

# Trigger pipeline
make airflow-trigger

# Trigger for specific companies
make airflow-trigger-companies COMPANIES="RELIANCE,TCS,INFY"

# List DAGs
make airflow-list-dags

# List recent runs
make airflow-list-runs

# Open Airflow UI
make open-airflow
```

## Configuration

### DAG Parameters

When triggering the DAG, you can configure:

```json
{
  "companies": ["RELIANCE", "TCS"],  // Empty = all companies
  "report_year": 2024,                // null = latest
  "skip_company_sync": true,          // Skip company catalog sync
  "batch_size": 5                     // Process N companies at once
}
```

### Scheduling

To run automatically, edit `services/airflow/dags/esg_pipeline_dag.py`:

```python
# Run daily at 2 AM
schedule_interval='0 2 * * *'

# Run weekly on Monday at 3 AM
schedule_interval='0 3 * * 1'

# Run monthly on 1st at 4 AM
schedule_interval='0 4 1 * *'
```

## Troubleshooting

### DAG Not Showing Up

```bash
# Check for import errors
docker exec esg-airflow-scheduler airflow dags list-import-errors
```

### Task Failed

1. Click on the failed task (red box)
2. Click "Log" button
3. Review error message
4. Fix issue
5. Click "Clear" to retry

### Services Not Starting

```bash
# Check service status
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml ps

# View logs
docker logs esg-airflow-scheduler
docker logs esg-airflow-webserver
```

### Permission Denied (Docker Socket)

```bash
# Add airflow user to docker group
docker exec -u root esg-airflow-scheduler usermod -aG docker airflow
docker restart esg-airflow-scheduler
```

## Architecture Comparison

### Before (Queue-based)
```
Ingestion → RabbitMQ → Embeddings (always running) → RabbitMQ → Extraction (always running)
```
- Services run 24/7
- Manual monitoring
- No retry logic
- Resource intensive

### After (Airflow)
```
Airflow DAG → Ingestion (on-demand) → Embeddings (on-demand) → Extraction (on-demand)
```
- Services start only when needed
- Visual monitoring
- Built-in retry
- Resource efficient

## Next Steps

1. **Explore the UI**
   - Try different views (Graph, Tree, Gantt)
   - Check task logs
   - View task duration trends

2. **Customize the DAG**
   - Edit `services/airflow/dags/esg_pipeline_dag.py`
   - Add custom tasks
   - Modify parameters

3. **Set Up Alerts**
   - Configure email notifications
   - Set up Slack integration
   - Add PagerDuty for critical failures

4. **Scale Up**
   - Process more companies in parallel
   - Use CeleryExecutor for distributed processing
   - Deploy to Kubernetes

## Resources

- **Airflow UI**: http://localhost:8081
- **API Docs**: http://localhost:8081/api/v1/ui/
- **Airflow Documentation**: https://airflow.apache.org/docs/
- **DAG File**: `services/airflow/dags/esg_pipeline_dag.py`
- **Full Guide**: `AIRFLOW_MIGRATION_GUIDE.md`

## Support

For help:
1. Check logs: `make logs-airflow`
2. Review DAG import errors in UI
3. Test tasks manually: `airflow tasks test`
4. Consult the migration guide: `AIRFLOW_MIGRATION_GUIDE.md`

---

**Happy Orchestrating! 🚀**
