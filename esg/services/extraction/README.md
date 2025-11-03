# ESG Intelligence Platform - Extraction Service

This service handles the extraction of BRSR Core indicators from company sustainability reports using LangChain and Google's Generative AI. It consumes messages from RabbitMQ, extracts indicators using RAG (Retrieval-Augmented Generation), validates the results, calculates ESG scores, and stores everything in PostgreSQL.

## Features

- **RabbitMQ Consumer**: Listens to `extraction-tasks` queue for document processing requests
- **LangChain RAG Pipeline**: Uses filtered vector retrieval with Google GenAI for accurate extraction
- **Batch Processing**: Extracts all 9 BRSR Core attributes (~50 indicators) per document
- **Validation**: Validates extracted indicators against BRSR schema with confidence scoring
- **ESG Scoring**: Calculates pillar scores (E, S, G) and overall ESG score with full transparency
- **Source Citations**: Tracks PDF page numbers and chunk IDs for every extracted value
- **Error Handling**: Graceful error handling with automatic retry and dead letter queue support

## Project Structure

```
services/extraction/
├── src/
│   ├── chains/            # LangChain extraction chains
│   ├── db/                # Database repository functions
│   ├── extraction/        # Indicator extraction logic
│   ├── models/            # Pydantic data models
│   ├── prompts/           # LangChain prompt templates
│   ├── retrieval/         # Filtered vector retrieval
│   ├── scoring/           # ESG score calculation
│   ├── validation/        # Indicator validation
│   ├── __init__.py
│   └── config.py          # Environment configuration
├── main.py                # RabbitMQ worker entry point
├── Dockerfile             # Multi-stage Docker build
├── pyproject.toml         # UV project configuration
├── uv.lock               # Locked dependencies
├── .env.example          # Example environment variables
└── README.md
```

## Setup

### Prerequisites

- Python 3.12+
- UV package manager
- PostgreSQL database with pgvector extension
- RabbitMQ message broker
- Google API key for Generative AI
- Document embeddings already generated (by embeddings service)

### Installation

1. Install dependencies using UV:
```bash
uv sync
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Update the `.env` file with your configuration:
   - Database credentials
   - RabbitMQ credentials
   - Google API key
   - Queue name
   - Log level

## Configuration

The service uses environment variables for configuration. See `.env.example` for all available options.

Key configuration parameters:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL connection details
- `RABBITMQ_HOST`, `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`: RabbitMQ connection details
- `EXTRACTION_QUEUE_NAME`: Queue name to consume from (default: `extraction-tasks`)
- `GOOGLE_API_KEY`: Google Generative AI API key
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Running the Service

### Local Development

Run the extraction worker:
```bash
uv run python main.py
```

The worker will:
1. Connect to RabbitMQ
2. Declare the `extraction-tasks` queue (creates if doesn't exist)
3. Start consuming messages
4. Process each document extraction task
5. Store results in PostgreSQL

### Sending Test Messages

To trigger extraction for a document, publish a message to the `extraction-tasks` queue with the object key as the message body:

```python
import pika

# Connect to RabbitMQ
credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost', credentials=credentials)
)
channel = connection.channel()

# Declare queue
channel.queue_declare(queue='extraction-tasks', durable=True)

# Publish message
object_key = "RELIANCE/2024_BRSR.pdf"
channel.basic_publish(
    exchange='',
    routing_key='extraction-tasks',
    body=object_key,
    properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
)

print(f"Sent extraction task: {object_key}")
connection.close()
```

## Docker

Build the Docker image:
```bash
docker build -t esg-extraction-service .
```

Run the container:
```bash
docker run --env-file .env esg-extraction-service
```

The Dockerfile uses a multi-stage build with UV for efficient dependency management and minimal image size.

## How It Works

### Extraction Pipeline

1. **Message Consumption**: Worker receives object_key from RabbitMQ queue
2. **Document Check**: Verifies if document already processed (skip if yes)
3. **Parsing**: Extracts company name and report year from object_key
4. **Indicator Loading**: Loads all BRSR Core indicator definitions from database
5. **Batch Extraction**: 
   - Groups indicators by BRSR attribute (1-9)
   - For each indicator:
     - Retrieves relevant chunks using filtered vector search (company + year)
     - Executes LangChain extraction chain with Google GenAI
     - Parses structured output with confidence scores
     - Tracks source citations (page numbers, chunk IDs)
6. **Validation**: Validates each extracted indicator against BRSR schema
7. **Storage**: Stores all extracted indicators in database (atomic transaction)
8. **Score Calculation**: 
   - Calculates pillar scores (E, S, G) using weighted averages
   - Calculates overall ESG score
   - Stores scores with full calculation metadata
9. **Acknowledgment**: Acknowledges RabbitMQ message (or rejects on failure)

### Error Handling

- **Already Processed**: Documents already processed are skipped
- **Invalid Object Key**: Malformed keys are rejected without requeue
- **Company Not Found**: Missing companies are rejected without requeue
- **Extraction Failures**: Individual indicator failures are logged but don't stop the batch
- **Database Errors**: Transaction rollback ensures data consistency
- **Connection Errors**: Automatic reconnection with exponential backoff

## Development

### Running Tests

Run all tests:
```bash
uv run pytest -v
```

Run specific test file:
```bash
uv run pytest tests/test_main_worker.py -v
```

Run with coverage:
```bash
uv run pytest --cov=src --cov-report=html
```

### Code Quality

Format code:
```bash
uv run black .
```

Lint code:
```bash
uv run ruff check .
```

## Dependencies

Main dependencies:
- `langchain`: LLM orchestration framework
- `langchain-google-genai`: Google Generative AI integration
- `psycopg2-binary`: PostgreSQL adapter
- `pydantic`: Data validation
- `pydantic-settings`: Settings management
- `python-dotenv`: Environment variable management
- `pika`: RabbitMQ client

## Monitoring and Metrics

The service includes comprehensive monitoring and metrics tracking. See [MONITORING.md](MONITORING.md) for detailed documentation.

### HTTP Endpoints

The service exposes HTTP endpoints for monitoring:

- `GET /health` - Health check endpoint (returns 200 if healthy, 503 if unhealthy)
- `GET /metrics` - Metrics endpoint (aggregate and recent document metrics)
- `GET /` - Service information

```bash
# Check health
curl http://localhost:8080/health

# View metrics
curl http://localhost:8080/metrics
```

### Metrics Tracked

- Processing time per document
- Indicators extracted, validated, and scored
- Confidence score statistics
- ESG scores (overall and pillar scores)
- API usage and error rates
- Success/failure rates

### Logging

The service logs comprehensive information at different levels:

- **INFO**: Normal operation (messages received, extraction progress, scores calculated)
- **WARNING**: Validation failures, missing data, partial extraction
- **ERROR**: Database errors, API failures, connection issues
- **DEBUG**: Detailed extraction steps, query results, intermediate values

Example log output:
```
2024-10-27 10:30:15 [INFO] main: Received extraction task: RELIANCE/2024_BRSR.pdf
2024-10-27 10:30:15 [INFO] main: Parsed document: company=RELIANCE, year=2024
2024-10-27 10:30:16 [INFO] main: Loaded 50 indicator definitions
2024-10-27 10:30:16 [INFO] main: Starting batch extraction for 50 indicators
2024-10-27 10:32:45 [INFO] main: Batch extraction complete: 48 indicators extracted
2024-10-27 10:32:46 [INFO] main: Validation complete: 45 valid, 3 invalid, 12 warnings
2024-10-27 10:32:47 [INFO] main: ESG scores calculated - Overall: 67.5, E: 72.3, S: 65.8, G: 64.2
2024-10-27 10:32:48 [INFO] main: ✓ Extraction task completed successfully for RELIANCE/2024_BRSR.pdf
```

## Troubleshooting

### Worker not consuming messages

1. Check RabbitMQ connection:
   ```bash
   # Verify RabbitMQ is running
   docker ps | grep rabbitmq
   
   # Check RabbitMQ logs
   docker logs rabbitmq
   ```

2. Verify queue exists:
   - Open RabbitMQ Management UI: http://localhost:15672
   - Check if `extraction-tasks` queue exists
   - Verify messages are being published

3. Check worker logs for connection errors

### Extraction failures

1. Verify embeddings exist:
   ```sql
   SELECT COUNT(*) FROM document_embeddings 
   WHERE object_key = 'RELIANCE/2024_BRSR.pdf';
   ```

2. Check Google API key is valid and has quota

3. Review extraction logs for specific indicator failures

### Database errors

1. Verify PostgreSQL is running and accessible
2. Check database schema is up to date (run migrations)
3. Verify pgvector extension is installed:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

## Architecture

The extraction service is part of the ESG Intelligence Platform microservices architecture:

```
Ingestion Service → Embeddings Service → [Extraction Service] → API Gateway → Frontend
                         ↓                        ↓
                    RabbitMQ              PostgreSQL + pgvector
```

The extraction service:
- Consumes from `extraction-tasks` queue (published by embeddings service)
- Reads embeddings from PostgreSQL
- Stores extracted indicators and scores in PostgreSQL
- Does NOT publish to any queues (end of pipeline)
