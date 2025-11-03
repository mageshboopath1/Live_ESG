# Extraction Service Examples

This directory contains example scripts demonstrating how to use the extraction service components.

## Example Files

### Batch Processing
- `example_batch_usage.py` - Demonstrates batch extraction of multiple indicators
  ```bash
  uv run python examples/example_batch_usage.py
  ```

### Scoring
- `example_esg_scoring.py` - Shows how to calculate ESG scores
  ```bash
  uv run python examples/example_esg_scoring.py
  ```

- `example_pillar_scoring.py` - Demonstrates pillar score calculation
  ```bash
  uv run python examples/example_pillar_scoring.py
  ```

### Validation
- `example_validation_usage.py` - Shows indicator validation workflow
  ```bash
  uv run python examples/example_validation_usage.py
  ```

### Utilities
- `trigger_extraction.py` - Utility to manually trigger extraction tasks
  ```bash
  uv run python examples/trigger_extraction.py
  ```

## Requirements

Examples require:
- PostgreSQL with pgvector
- MinIO object storage
- RabbitMQ message broker
- Google AI API key

Configure environment variables in `.env` file (see `.env.example`).

## Usage

All examples can be run directly with UV:

```bash
# Run an example
uv run python examples/<example_file>.py

# With custom parameters (where supported)
uv run python examples/example_esg_scoring.py --company TCS --year 2023
```

See individual example files for specific usage instructions and parameters.
