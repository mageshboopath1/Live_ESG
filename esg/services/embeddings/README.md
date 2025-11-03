# Embeddings Service

This service generates semantic embeddings for PDF documents using Google Gemini AI and stores them in PostgreSQL with pgvector for efficient similarity search.

## Features

- Consumes embedding tasks from RabbitMQ
- Downloads PDFs from MinIO object storage
- Extracts text from PDFs using PyMuPDF
- Splits text into semantic chunks (1000-2000 characters)
- Generates embeddings using Google Gemini (gemini-embedding-001)
- Stores embeddings in PostgreSQL with pgvector extension
- Tracks page numbers and chunk indices for citation

## Dependencies

This service uses [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management.

### Prerequisites

- Python 3.12+
- UV installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- PostgreSQL with pgvector extension
- MinIO object storage running
- RabbitMQ message broker running
- Google AI API key

## Setup

### Install Dependencies

```bash
# Sync dependencies from pyproject.toml and uv.lock
uv sync

# Or sync without dev dependencies
uv sync --no-dev
```

### Environment Variables

Set the following environment variables:

```bash
POSTGRES_USER=esg_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=esg_platform
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
GOOGLE_API_KEY=your_google_ai_api_key
```

## Running the Service

### Using UV

```bash
# Run the service
uv run python main.py
```

### Using Docker

```bash
# Build the Docker image
docker build -t embeddings .

# Run the container
docker run --env-file .env embeddings
```

## Development

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update lock file
uv lock
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Sync after updating
uv sync
```

### Running Python Commands

```bash
# Run any Python command in the UV environment
uv run python -c "import google.genai; print('Google GenAI loaded')"

# Run the main service
uv run python main.py

# Run a specific module
uv run python src/worker.py
```

## Architecture

The embeddings service processes documents in the following pipeline:

1. **Consumer**: Listens to RabbitMQ `embedding-tasks` queue
2. **Downloader**: Fetches PDF from MinIO using object_key
3. **Extractor**: Extracts text from PDF pages using PyMuPDF
4. **Splitter**: Chunks text into 1000-2000 character segments
5. **Embedder**: Generates embeddings using Google Gemini
6. **Storage**: Stores embeddings in PostgreSQL with metadata

### Chunking Strategy

- Chunk size: 1000-2000 characters
- Overlap: 200 characters
- Preserves sentence boundaries
- Tracks page numbers and chunk indices

## Database Schema

The service stores embeddings in the `document_embeddings` table:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    object_key TEXT NOT NULL,
    company_name TEXT NOT NULL,
    report_year INT NOT NULL,
    page_number INT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(3072),
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_object_key ON document_embeddings(object_key);
CREATE INDEX idx_company_year ON document_embeddings(company_name, report_year);
CREATE INDEX idx_embedding_vector ON document_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## Google GenAI Integration

The service uses Google's Gemini embedding model:

```python
from google import genai

client = genai.Client(api_key=GOOGLE_API_KEY)
result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=chunks
)
embeddings = result.embeddings
```

### Embedding Dimensions

- Model: `gemini-embedding-001`
- Dimensions: 3072
- Distance metric: Cosine similarity

## RabbitMQ Integration

The service consumes messages from the `embedding-tasks` queue:

**Message Format:**
```json
{
  "object_key": "RELIANCE/2024_BRSR.pdf"
}
```

**Queue Configuration:**
- Queue: `embedding-tasks`
- Durability: Enabled
- Auto-acknowledge: Disabled (manual ack after processing)
- Prefetch: 1 (process one document at a time)

## Performance Considerations

### Batch Processing

Embeddings are generated in batches to optimize API usage:
- Batch size: 10-50 chunks per request
- Reduces API calls and improves throughput

### Error Handling

- Retry logic with exponential backoff for API failures
- Failed documents are requeued with retry counter
- Dead letter queue for documents exceeding max retries

## Troubleshooting

### Google AI API Issues

If embedding generation fails:

1. Verify API key is valid
2. Check API quota and rate limits
3. Ensure internet connectivity
4. Check if model name is correct

### PostgreSQL pgvector Issues

If vector storage fails:

1. Verify pgvector extension is installed: `CREATE EXTENSION vector;`
2. Check vector dimensions match (3072)
3. Ensure sufficient disk space
4. Check index creation status

### PDF Processing Issues

If PDF extraction fails:

1. Verify PDF is not corrupted
2. Check if PDF is password-protected
3. Ensure PyMuPDF can read the PDF format
4. Check available memory for large PDFs

### RabbitMQ Connection Issues

If message consumption fails:

1. Verify RabbitMQ is running
2. Check connection credentials
3. Ensure queue exists
4. Check network connectivity

## UV Commands Reference

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a new virtual environment
uv venv

# Sync dependencies
uv sync

# Add a package
uv add package-name

# Remove a package
uv remove package-name

# Update lock file
uv lock

# Run a command
uv run python script.py

# Show installed packages
uv pip list

# Show UV version
uv --version
```

## Monitoring

The service logs the following metrics:

- Documents processed
- Chunks generated
- Embeddings created
- Processing time per document
- API call statistics
- Error rates

Monitor these logs to ensure the service is running efficiently.
