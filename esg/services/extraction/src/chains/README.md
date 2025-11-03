# Extraction Chains

This module provides LangChain-based extraction chains for BRSR Core indicator extraction from company sustainability reports.

## Overview

The extraction chain combines:
- **FilteredPGVectorRetriever**: Company/year-specific document retrieval using pgvector
- **Google GenAI (gemini-2.5-flash)**: LLM for intelligent extraction
- **Prompt Templates**: Structured prompts for accurate indicator extraction
- **Retry Logic**: Exponential backoff for API failures

## Usage

### Basic Usage

```python
from src.chains.extraction_chain import create_extraction_chain
from src.db.repository import load_brsr_indicators
from src.config import config

# Create extraction chain for a specific company and year
chain = create_extraction_chain(
    connection_string=config.database_url,
    company_name="RELIANCE",
    report_year=2024,
    google_api_key=config.google_api_key,
)

# Load BRSR indicator definitions
indicators = load_brsr_indicators(config.database_url)

# Extract a single indicator
ghg_indicator = next(
    ind for ind in indicators 
    if ind.indicator_code == "GHG_SCOPE1"
)
result = chain.extract_indicator(ghg_indicator)

print(f"Extracted value: {result.value}")
print(f"Confidence: {result.confidence}")
print(f"Source pages: {result.source_pages}")
```

### Batch Extraction

```python
# Extract multiple indicators
results = chain.extract_indicators_batch(indicators[:10])

for result in results:
    print(f"{result.indicator_code}: {result.value} (confidence: {result.confidence})")
```

### Custom Configuration

```python
# Create chain with custom parameters
chain = create_extraction_chain(
    connection_string=config.database_url,
    company_name="TCS",
    report_year=2023,
    google_api_key=config.google_api_key,
    model_name="gemini-2.5-flash",  # LLM model
    temperature=0.1,                 # Low temperature for consistency
    max_retries=5,                   # Retry attempts for API failures
    initial_retry_delay=2.0,         # Initial delay in seconds
)
```

## Architecture

### Retrieval-Augmented Generation (RAG)

The extraction chain follows the RAG pattern:

1. **Retrieval**: Query vector store with company/year filtering
   - Reduces search space from 40k+ to ~200-500 embeddings
   - Uses cosine similarity for semantic search
   - Returns top-k most relevant chunks

2. **Augmentation**: Format retrieved chunks into context
   - Includes page numbers for citations
   - Preserves chunk order and metadata

3. **Generation**: LLM extracts structured indicator data
   - Uses prompt template with indicator details
   - Returns structured output via Pydantic parser
   - Includes confidence scores and source citations

### Error Handling

The chain implements robust error handling:

- **Exponential Backoff**: Retries API calls with increasing delays (1s, 2s, 4s)
- **Graceful Degradation**: Returns "Not Found" for missing indicators
- **Partial Failures**: Continues batch extraction even if individual indicators fail
- **Comprehensive Logging**: Tracks all extraction attempts and failures

## Components

### ExtractionChain Class

Main class that encapsulates the extraction pipeline.

**Methods:**
- `extract_indicator(indicator, k=10)`: Extract a single indicator
- `extract_indicators_batch(indicators, k=10)`: Extract multiple indicators
- `_build_search_query(indicator)`: Build search query from indicator definition
- `_retrieve_with_retry(query, k)`: Retrieve documents with retry logic
- `_execute_chain_with_retry(prompt, context)`: Execute LLM chain with retry logic

### create_extraction_chain Function

Factory function to create configured ExtractionChain instances.

**Parameters:**
- `connection_string`: PostgreSQL connection string
- `company_name`: Company name for filtering (e.g., "RELIANCE")
- `report_year`: Report year for filtering (e.g., 2024)
- `google_api_key`: Google GenAI API key
- `model_name`: LLM model (default: "gemini-2.5-flash")
- `temperature`: LLM temperature (default: 0.1)
- `max_retries`: Maximum retry attempts (default: 3)
- `initial_retry_delay`: Initial retry delay in seconds (default: 1.0)

## Requirements

This module implements the following requirements:
- **6.2**: LangChain retrieval chain with Google GenAI
- **6.3**: Structured output using Pydantic models
- **11.2**: RetrievalQA chain with filtered retriever
- **11.4**: LangChain output parsers for validation
- **11.5**: Retry logic with exponential backoff

## Testing

Run the structure tests:

```bash
uv run python test_extraction_chain_simple.py
```

For full integration tests (requires database and API key):

```bash
# Set environment variables
export DB_HOST=localhost
export DB_NAME=esg_intelligence
export GOOGLE_API_KEY=your_key_here

# Run integration tests
uv run python test_extraction_chain.py
```

## Next Steps

After implementing the extraction chain:

1. **Task 9**: Implement single indicator extraction function
2. **Task 10**: Implement batch extraction for multiple indicators
3. **Task 11**: Add validation and confidence scoring
4. **Task 12-14**: Implement ESG score calculation
5. **Task 15-17**: Create main extraction worker with RabbitMQ

## Performance Considerations

- **Filtered Retrieval**: Always filter by company_name and report_year before vector search
- **Batch Size**: Use k=10 for most indicators, adjust based on document size
- **Temperature**: Keep at 0.1 for consistent extraction results
- **Retries**: 3 retries with exponential backoff handles most transient failures
- **Caching**: Consider caching indicator definitions to reduce database queries

## Troubleshooting

### API Rate Limits

If you encounter rate limits:
- Increase `initial_retry_delay` to 2.0 or higher
- Increase `max_retries` to 5
- Add delays between batch extractions

### Low Confidence Scores

If confidence scores are consistently low:
- Increase k (number of retrieved chunks) to 15-20
- Check if embeddings exist for the company/year
- Verify indicator descriptions are clear and specific

### Empty Retrieval Results

If no documents are retrieved:
- Verify embeddings exist in database for company/year
- Check company_name spelling matches database exactly
- Ensure report_year is correct
