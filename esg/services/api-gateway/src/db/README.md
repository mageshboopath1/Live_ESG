# Database Module

This module provides SQLAlchemy models and database connection management for the API Gateway service.

## Overview

The database module consists of two main components:

1. **models.py**: SQLAlchemy ORM models for all database tables
2. **connection.py**: Database connection pooling, session management, and error handling

## Models

### CompanyCatalog
Stores company information from NIFTY 50.

**Fields:**
- `id`: Primary key
- `company_name`: Company name
- `industry`: Industry sector
- `symbol`: Stock symbol
- `series`: Stock series
- `isin_code`: ISIN code
- `created_at`, `updated_at`: Timestamps

### IngestionMetadata
Tracks document ingestion status.

**Fields:**
- `id`: Primary key
- `company_id`: Foreign key to CompanyCatalog
- `source`: Data source (NSE, MCA, etc.)
- `file_path`: MinIO object path
- `file_type`: File type (pdf, csv, json)
- `ingested_at`: Ingestion timestamp
- `status`: Processing status

### DocumentEmbedding
Stores document embeddings for semantic search.

**Fields:**
- `id`: Primary key
- `object_key`: MinIO object key
- `company_name`: Company name
- `report_year`: Report year
- `page_number`: Page number
- `chunk_index`: Chunk index
- `embedding`: Vector embedding (3072 dimensions)
- `chunk_text`: Text content
- `created_at`: Creation timestamp

### BRSRIndicator
BRSR Core indicator definitions.

**Fields:**
- `id`: Primary key
- `indicator_code`: Unique indicator code
- `attribute_number`: BRSR attribute (1-9)
- `parameter_name`: Parameter name
- `measurement_unit`: Unit of measurement
- `description`: Indicator description
- `pillar`: ESG pillar (E, S, G)
- `weight`: Weight for scoring (0.0-1.0)
- `data_assurance_approach`: Assurance approach
- `brsr_reference`: BRSR reference
- `created_at`, `updated_at`: Timestamps

### ExtractedIndicator
Stores extracted indicator values from documents.

**Fields:**
- `id`: Primary key
- `object_key`: Source document key
- `company_id`: Foreign key to CompanyCatalog
- `report_year`: Report year
- `indicator_id`: Foreign key to BRSRIndicator
- `extracted_value`: Extracted text value
- `numeric_value`: Numeric value (if applicable)
- `confidence_score`: LLM confidence (0.0-1.0)
- `validation_status`: Validation status (valid, invalid, pending)
- `source_pages`: Array of source page numbers
- `source_chunk_ids`: Array of source chunk IDs
- `extracted_at`: Extraction timestamp

### ESGScore
Stores calculated ESG scores.

**Fields:**
- `id`: Primary key
- `company_id`: Foreign key to CompanyCatalog
- `report_year`: Report year
- `environmental_score`: Environmental pillar score
- `social_score`: Social pillar score
- `governance_score`: Governance pillar score
- `overall_score`: Overall ESG score
- `calculation_metadata`: JSON metadata with weights and methodology
- `calculated_at`: Calculation timestamp

## Connection Management

### Database Engine

The module creates a SQLAlchemy engine with connection pooling:

```python
from src.db import engine

# Engine is pre-configured with:
# - Pool size: 10 connections
# - Max overflow: 20 connections
# - Pool timeout: 30 seconds
# - Pool recycle: 3600 seconds (1 hour)
# - Pre-ping: Enabled (health checks)
```

### Session Management

#### FastAPI Dependency

Use `get_db()` as a FastAPI dependency:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from src.db import get_db, CompanyCatalog

@app.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(CompanyCatalog).all()
    return companies
```

#### Context Manager

Use `get_db_context()` for scripts or background tasks:

```python
from src.db import get_db_context, CompanyCatalog

with get_db_context() as db:
    companies = db.query(CompanyCatalog).all()
    # Automatic commit on success, rollback on error
```

### Error Handling

The module provides comprehensive error handling:

```python
from src.db import handle_database_error
from sqlalchemy.exc import SQLAlchemyError

try:
    # Database operation
    pass
except SQLAlchemyError as e:
    error_response = handle_database_error(e)
    # Returns: {"status_code": 409, "detail": "..."}
```

**Custom Exceptions:**
- `DatabaseConnectionError`: Connection failures
- `DatabaseQueryError`: Query execution failures

### Health Checks

Check database connectivity:

```python
from src.db import check_database_connection

if check_database_connection():
    print("Database is healthy")
else:
    print("Database connection failed")
```

### Cleanup

Close connections on shutdown:

```python
from src.db import close_database_connections

@app.on_event("shutdown")
def shutdown():
    close_database_connections()
```

## Configuration

Database connection is configured via environment variables:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=esg_platform
DB_USER=esg_user
DB_PASSWORD=your_password
```

The connection URL is automatically constructed in `config.py`:

```python
from src.config import settings

print(settings.database_url)
# postgresql://esg_user:password@localhost:5432/esg_platform
```

## Testing

Run the database setup test:

```bash
uv run python test_db_setup.py
```

This verifies:
- Model imports
- Database connection
- Query execution
- Data retrieval

## Relationships

The models define SQLAlchemy relationships for easy navigation:

```python
from src.db import get_db_context, CompanyCatalog

with get_db_context() as db:
    company = db.query(CompanyCatalog).first()
    
    # Access related data
    print(company.ingestion_metadata)  # List of ingestion records
    print(company.extracted_indicators)  # List of extracted indicators
    print(company.esg_scores)  # List of ESG scores
```

## Performance Considerations

1. **Connection Pooling**: Pre-configured with optimal pool settings
2. **Indexes**: All foreign keys and frequently queried columns are indexed
3. **Pre-ping**: Ensures connections are healthy before use
4. **Pool Recycle**: Prevents stale connections
5. **Vector Index**: HNSW index on embeddings for fast similarity search

## Migration Notes

- The database schema is created via SQL migration scripts in `infra/db-init/`
- Models in this module must match the schema defined in those scripts
- Use Alembic for future schema migrations if needed

## Dependencies

- `sqlalchemy>=2.0.44`: ORM and database toolkit
- `psycopg2-binary>=2.9.11`: PostgreSQL adapter
- `pgvector>=0.3.6`: PostgreSQL vector extension support
