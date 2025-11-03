# Architecture Comparison: Queue-based vs Airflow

## Visual Comparison

### Queue-based Architecture (Current)

```
┌─────────────────────────────────────────────────────────────────┐
│                         ALWAYS RUNNING                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Ingestion   │  (Runs once, publishes to queue)
│   Service    │
└──────┬───────┘
       │ Publishes: object_key
       ▼
┌──────────────┐
│  RabbitMQ    │  embedding-tasks queue
│   Queue      │  (Messages waiting)
└──────┬───────┘
       │ Consumes
       ▼
┌──────────────┐
│  Embeddings  │  ◀── ALWAYS LISTENING (24/7)
│   Worker     │      • 2 GB RAM
│              │      • 1 CPU core
│  while True: │      • Waiting for messages...
│    consume() │
└──────┬───────┘
       │ Publishes: object_key
       ▼
┌──────────────┐
│  RabbitMQ    │  extraction-tasks queue
│   Queue      │  (Messages waiting)
└──────┬───────┘
       │ Consumes
       ▼
┌──────────────┐
│  Extraction  │  ◀── ALWAYS LISTENING (24/7)
│   Worker     │      • 2 GB RAM
│              │      • 1 CPU core
│  while True: │      • Waiting for messages...
│    consume() │
└──────────────┘

Total Idle Resources: 4 GB RAM, 2 CPUs (24/7)
```

### Airflow Architecture (New)

```
┌─────────────────────────────────────────────────────────────────┐
│                      ON-DEMAND EXECUTION                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    Airflow Scheduler                          │
│                  (Lightweight, 512 MB RAM)                    │
│                                                               │
│  • Monitors DAG files                                         │
│  • Triggers tasks when needed                                │
│  • Manages dependencies                                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Trigger
                         ▼
              ┌──────────────────────┐
              │   esg_pipeline DAG   │
              │                      │
              │  [Graph View in UI]  │
              └──────────┬───────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Ingestion   │  │  Embeddings  │  │  Extraction  │
│              │  │              │  │              │
│  START       │─▶│  START       │─▶│  START       │
│  PROCESS     │  │  PROCESS     │  │  PROCESS     │
│  STOP        │  │  STOP        │  │  STOP        │
│              │  │              │  │              │
│  (2 GB RAM)  │  │  (2 GB RAM)  │  │  (2 GB RAM)  │
│  (1 CPU)     │  │  (1 CPU)     │  │  (1 CPU)     │
│              │  │              │  │              │
│  Duration:   │  │  Duration:   │  │  Duration:   │
│  10 minutes  │  │  30 minutes  │  │  60 minutes  │
└──────────────┘  └──────────────┘  └──────────────┘

Total Idle Resources: 1 GB RAM, 1 CPU (Airflow only)
Total Active Resources: 3 GB RAM, 2 CPUs (during runs)
```

## Side-by-Side Comparison

| Aspect | Queue-based | Airflow-based |
|--------|-------------|---------------|
| **Resource Usage (Idle)** | 4 GB RAM, 2 CPUs | 1 GB RAM, 1 CPU |
| **Resource Usage (Active)** | 4 GB RAM, 2 CPUs | 3 GB RAM, 2 CPUs |
| **Running Time** | 24/7 | On-demand |
| **Visibility** | RabbitMQ Management UI | Airflow DAG UI |
| **Monitoring** | Manual queue checks | Visual graph + logs |
| **Retry Logic** | Manual requeue | Built-in automatic |
| **Debugging** | Log files only | UI + logs + task history |
| **Scheduling** | External cron | Built-in scheduler |
| **Alerting** | Custom scripts | Built-in email/Slack |
| **Scalability** | Add more workers | Dynamic task mapping |
| **Cost (Cloud)** | High (24/7 compute) | Low (pay per run) |

## Data Flow Comparison

### Queue-based Flow

```
1. Ingestion runs
   ↓
2. Publishes to embedding-tasks queue
   ↓
3. Embeddings worker (always listening) picks up message
   ↓
4. Processes document
   ↓
5. Publishes to extraction-tasks queue
   ↓
6. Extraction worker (always listening) picks up message
   ↓
7. Processes document
   ↓
8. Done

Timeline: Continuous, workers always running
```

### Airflow Flow

```
1. User triggers DAG (UI/CLI/API)
   ↓
2. Airflow scheduler starts ingestion task
   ↓
3. Ingestion container starts, processes, stops
   ↓
4. Airflow starts embeddings task
   ↓
5. Embeddings container starts, processes, stops
   ↓
6. Airflow starts extraction task
   ↓
7. Extraction container starts, processes, stops
   ↓
8. Airflow generates report
   ↓
9. Done

Timeline: Sequential, containers start/stop as needed
```

## Monitoring Comparison

### Queue-based Monitoring

```
RabbitMQ Management UI:
┌─────────────────────────────────────┐
│ Queue: embedding-tasks              │
│ Messages: 5                         │
│ Consumers: 1                        │
│ Message rate: 0.5/s                 │
└─────────────────────────────────────┘

Issues:
• No visibility into what's being processed
• Can't see which document is stuck
• No task duration history
• Manual queue depth monitoring
```

### Airflow Monitoring

```
Airflow UI - Graph View:
┌─────────────────────────────────────────────────────┐
│  [✓] preflight_check                                │
│       ↓                                              │
│  [✓] get_companies                                  │
│       ↓                                              │
│  [✓] ingestion (10m 23s)                           │
│       ↓                                              │
│  [▶] embeddings_batch (running... 15m elapsed)     │
│       ↓                                              │
│  [ ] extraction (waiting)                           │
│       ↓                                              │
│  [ ] generate_report (waiting)                      │
└─────────────────────────────────────────────────────┘

Benefits:
• See exactly which task is running
• View task duration in real-time
• Click any task to see logs
• Historical performance data
• Automatic retry on failure
```

## Cost Comparison (AWS Example)

### Queue-based (24/7)

```
Embeddings Worker:
• Instance: t3.medium (2 vCPU, 4 GB)
• Cost: $0.0416/hour × 730 hours = $30.37/month

Extraction Worker:
• Instance: t3.medium (2 vCPU, 4 GB)
• Cost: $0.0416/hour × 730 hours = $30.37/month

RabbitMQ:
• Instance: t3.small (2 vCPU, 2 GB)
• Cost: $0.0208/hour × 730 hours = $15.18/month

Total: $75.92/month (running 24/7)
```

### Airflow-based (On-demand)

```
Airflow Scheduler + Webserver:
• Instance: t3.small (2 vCPU, 2 GB)
• Cost: $0.0208/hour × 730 hours = $15.18/month

Workers (on-demand):
• Instance: t3.medium (2 vCPU, 4 GB)
• Usage: 2 hours/day average
• Cost: $0.0416/hour × 60 hours = $2.50/month

Total: $17.68/month

Savings: $58.24/month (77% reduction)
```

## Scaling Comparison

### Queue-based Scaling

```
To process more documents:
1. Add more worker instances
2. Configure them to consume from same queue
3. Manage load balancing manually
4. All workers run 24/7

Example: 5 companies → 10 companies
• Need 2x workers
• 2x cost (24/7)
• Manual configuration
```

### Airflow Scaling

```
To process more documents:
1. Increase parallelism in DAG config
2. Use dynamic task mapping
3. Airflow handles distribution
4. Workers start/stop automatically

Example: 5 companies → 10 companies
• Same infrastructure
• 2x processing time (or parallel tasks)
• Automatic scaling
• Cost scales with usage
```

## Failure Handling Comparison

### Queue-based

```
Task fails:
1. Message stays in queue or goes to DLQ
2. Manual investigation required
3. Manual requeue needed
4. No automatic retry
5. No visibility into failure history

Example:
• Extraction fails for RELIANCE
• Message in DLQ
• Need to manually republish
• No record of why it failed
```

### Airflow

```
Task fails:
1. Airflow automatically retries (configurable)
2. Failure logged in UI with full context
3. Can manually retry from UI
4. Full failure history visible
5. Email/Slack alert sent

Example:
• Extraction fails for RELIANCE
• Airflow retries 2 times automatically
• Still fails → marked as failed in UI
• Click task → see full error log
• Click "Clear" → retry manually
• Email sent to team
```

## Developer Experience

### Queue-based

```python
# Embeddings worker
while True:
    message = queue.consume()
    process(message)
    queue.publish_to_next(message)
```

**Issues:**
- Hard to test locally
- Need RabbitMQ running
- Can't easily replay specific documents
- No visibility into processing

### Airflow

```python
# Airflow DAG
embeddings = DockerOperator(
    task_id='embeddings',
    image='esg-embeddings:latest',
    environment={'DOCUMENTS': '{{ ti.xcom_pull(...) }}'},
)
```

**Benefits:**
- Easy to test individual tasks
- Can run tasks independently
- Clear dependencies
- Full execution history

## Conclusion

### When to Use Queue-based
- Need real-time processing (< 1 second latency)
- Unpredictable workload spikes
- Multiple producers/consumers
- Event-driven architecture

### When to Use Airflow
- ✅ Batch processing (our use case)
- ✅ Scheduled workflows
- ✅ Complex dependencies
- ✅ Need visibility and monitoring
- ✅ Cost optimization important
- ✅ Retry logic required

**For ESG Platform: Airflow is the better choice**

We process reports in batches, need visibility, want cost efficiency, and benefit from built-in retry logic. The queue-based approach was over-engineered for our use case.
