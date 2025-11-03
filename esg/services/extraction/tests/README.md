# Extraction Service Tests

This directory contains all test files for the extraction service.

## Test Files

### End-to-End Tests
- `test_e2e_extraction.py` - Complete pipeline E2E test
- `test_e2e_structure.py` - Structure validation test

### Component Tests
- `test_extractor.py` - Extractor unit tests
- `test_extractor_batch.py` - Batch extraction tests
- `test_extraction_chain.py` - LangChain extraction tests
- `test_extraction_chain_simple.py` - Simplified chain tests
- `test_extraction_prompts.py` - Prompt template tests

### Retrieval Tests
- `test_filtered_retriever.py` - Filtered retriever tests
- `test_retriever_structure.py` - Retriever structure tests

### Validation & Scoring Tests
- `test_validator.py` - Indicator validation tests
- `test_esg_calculator.py` - ESG score calculation tests
- `test_pillar_calculator.py` - Pillar score calculation tests

### Infrastructure Tests
- `test_repository.py` - Database repository tests
- `test_http_server.py` - HTTP server tests
- `test_monitoring.py` - Metrics and health check tests
- `test_main_worker.py` - Main worker tests

## Running Tests

### Run all tests
```bash
uv run pytest tests/ -v
```

### Run specific test file
```bash
uv run pytest tests/test_e2e_extraction.py -v
```

### Run with coverage
```bash
uv run pytest tests/ --cov=src --cov-report=html
```

## Test Requirements

Tests require:
- PostgreSQL with pgvector
- MinIO object storage
- RabbitMQ message broker
- Google AI API key

See main [README.md](../README.md) for setup instructions.
