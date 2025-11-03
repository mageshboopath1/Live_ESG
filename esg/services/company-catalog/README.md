# Company Catalog Service

This service syncs NIFTY 50 company data from the NSE (National Stock Exchange) and maintains the company catalog in PostgreSQL.

## Features

- Fetches the latest NIFTY 50 company list from NSE
- Syncs company data (name, symbol, ISIN, industry) to PostgreSQL
- Removes companies no longer in NIFTY 50
- Upserts current companies with conflict resolution

## Dependencies

This service uses [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management.

### Prerequisites

- Python 3.12+
- UV installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- PostgreSQL database running

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
docker build -t company-catalog .

# Run the container
docker run --env-file .env company-catalog
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
uv run python -c "import pandas; print(pandas.__version__)"

# Run a script
uv run python src/main.py
```

## Database Schema

The service interacts with the `company_catalog` table:

```sql
CREATE TABLE company_catalog (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    industry TEXT,
    symbol TEXT NOT NULL,
    series TEXT,
    isin_code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, isin_code)
);
```

## Troubleshooting

### Database Connection Issues

If the service fails to connect to PostgreSQL:

1. Verify PostgreSQL is running
2. Check environment variables are set correctly
3. Ensure the database exists
4. Check network connectivity (especially in Docker)

### NSE Data Fetch Issues

If fetching NSE data fails:

1. Check internet connectivity
2. Verify the NSE URL is accessible
3. Check if NSE has changed their CSV format or URL

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
