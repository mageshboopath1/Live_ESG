# Document Ingestion Service

This service fetches and downloads company sustainability reports (BRSR, annual reports) from various sources and stores them in MinIO object storage.

## Features

- Fetches report URLs for NIFTY 50 companies
- Downloads PDF reports using Selenium for dynamic content
- Uploads PDFs to MinIO with structured object keys
- Publishes embedding tasks to RabbitMQ
- Tracks ingestion metadata in PostgreSQL

## Dependencies

This service uses [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management.

### Prerequisites

- Python 3.12+
- UV installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- PostgreSQL database running
- MinIO object storage running
- RabbitMQ message broker running
- Chrome/Chromium browser (for Selenium)

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
```

## Running the Service

### Using UV

```bash
# Run the service
uv run python src/main.py
```

### Using Docker

```bash
# Build the Docker image
docker build -t ingestion .

# Run the container
docker run --env-file .env ingestion
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
uv run python -c "import selenium; print(selenium.__version__)"

# Run a specific script
uv run python src/fetch_links.py
uv run python src/download_reports.py
```

## Architecture

The ingestion service consists of two main components:

1. **fetch_links.py**: Scrapes company websites to find report URLs
2. **download_reports.py**: Downloads PDFs and uploads to MinIO

### Object Key Format

PDFs are stored in MinIO with the following structure:

```
{company_name}/{year}_{report_type}.pdf
```

Example: `RELIANCE/2024_BRSR.pdf`

## Database Schema

The service interacts with the `ingestion_metadata` table:

```sql
CREATE TABLE ingestion_metadata (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES company_catalog(id),
    source TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'SUCCESS',
    UNIQUE(company_id, source, file_path)
);
```

## RabbitMQ Integration

After uploading a PDF to MinIO, the service publishes a message to the `embedding-tasks` queue:

```json
{
  "object_key": "RELIANCE/2024_BRSR.pdf"
}
```

## Troubleshooting

### Selenium WebDriver Issues

If Selenium fails to start:

1. Install Chrome/Chromium browser
2. Use webdriver-manager (already included) for automatic driver management
3. Check if running in headless mode for Docker environments

### MinIO Connection Issues

If MinIO uploads fail:

1. Verify MinIO is running
2. Check endpoint and credentials
3. Ensure the bucket exists
4. Check network connectivity

### RabbitMQ Connection Issues

If RabbitMQ publishing fails:

1. Verify RabbitMQ is running
2. Check connection credentials
3. Ensure the queue exists or can be created
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

## Links Directory

The `links/` directory contains text files with report URLs for each company. These files are used by the download service to fetch reports.

Format: `{SYMBOL}_{Company_Name}.txt`

Example: `RELIANCE_Reliance_Industries_Limited.txt`
