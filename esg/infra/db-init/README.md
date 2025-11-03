# Database Initialization Scripts

This directory contains SQL migration scripts and seed data for the ESG Intelligence Platform database.

## Docker Setup

**Dockerfile** - Extends the pgvector/pgvector:pg15 image with Python 3 and psycopg2-binary to support running seed scripts.

## Migration Scripts

The scripts are executed in numerical order by PostgreSQL on container initialization:

1. **01_init.sql** - Initial schema (company catalog, ingestion metadata, document embeddings)
2. **02_brsr_indicators.sql** - BRSR Core indicators table and indexes
3. **03_extraction_tables.sql** - Extracted indicators and ESG scores tables

## Seed Data

**main.py** - Python script to populate 54 BRSR Core indicators

This is a uv-based project with dependencies managed in `pyproject.toml`.

### Running the Seed Script

#### Option 1: Using Docker Compose (Recommended)

The postgres container is built with Python support using a custom Dockerfile. The migration SQL scripts run automatically on container initialization, but the seed script must be run manually.

**First time setup:**

```bash
# From the infra directory
cd infra

# Build the custom postgres image with Python
docker compose build postgres

# Start the containers
docker compose up -d postgres

# Wait for postgres to be ready (check logs)
docker compose logs -f postgres

# Run the seed script
docker compose exec postgres python3 /docker-entrypoint-initdb.d/main.py
```

**Subsequent runs:**

```bash
# From the infra directory
cd infra

# Run the seed script inside the postgres container
docker compose exec postgres python3 /docker-entrypoint-initdb.d/main.py
```

Or using docker directly:

```bash
# Execute the seed script
docker exec -it esg-postgres python3 /docker-entrypoint-initdb.d/main.py
```

#### Option 2: Local Development (Outside Docker)

If running locally without Docker:

```bash
# From the infra/db-init directory
cd infra/db-init

# Install dependencies (first time only)
uv sync

# Load environment variables from infra/.env
export $(cat ../.env | grep -v '^#' | xargs)

# Override host for local connection
export POSTGRES_HOST=localhost

# Run the seed script
uv run python main.py
```

## BRSR Core Framework

The indicators are based on the SEBI BRSR Core framework with 9 attributes:

1. **GHG Footprint** (Environmental) - Scope 1, Scope 2, emission intensity
2. **Water Footprint** (Environmental) - Consumption, intensity, discharge
3. **Energy Footprint** (Environmental) - Total consumption, renewable %, intensity
4. **Waste Management** (Environmental) - Plastic, e-waste, hazardous, recycling
5. **Employee Wellbeing** (Social) - Safety metrics, LTIFR, fatalities
6. **Gender Diversity** (Social) - Female wages, POSH complaints
7. **Inclusive Development** (Social) - MSME sourcing, smaller town employment
8. **Customer Fairness** (Governance) - Data breaches, payment terms
9. **Business Openness** (Governance) - Trading house concentration, RPTs

## Indexes

The migration scripts create the following critical indexes:

- **idx_doc_emb_company_year** - Composite index on (company_name, report_year) for filtered vector retrieval
- **idx_doc_emb_vector** - pgvector IVFFlat index on embedding column with cosine distance
- **idx_brsr_attribute** - Index on attribute_number for filtering
- **idx_brsr_pillar** - Index on pillar (E/S/G) for score calculations

## Database Configuration

The database connection uses environment variables from `infra/.env`:

- `POSTGRES_DB` - Database name (default: moz)
- `POSTGRES_USER` - Database user (default: drfitz)
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_HOST` - Database host (postgres for Docker, localhost for local)
- `POSTGRES_PORT` - Database port (default: 5432)

## Notes

- The seed script checks for existing data and skips seeding if indicators already exist
- All indicators include weights for ESG score calculation
- Indicators reference the official BRSR Essential Indicators questions
- The postgres container needs Python and psycopg2 installed to run the seed script
- Migration SQL files (01, 02, 03) run automatically on container initialization
