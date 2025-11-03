# Extraction Module

This module provides high-level functions for extracting BRSR Core indicators from company sustainability reports using LangChain and Google GenAI.

## Overview

The extraction module implements the single indicator extraction function that orchestrates the complete RAG (Retrieval-Augmented Generation) pipeline for BRSR indicator extraction.

## Main Function: `extract_indicator()`

### Purpose

Extracts a single BRSR Core indicator from a company's sustainability report with full transparency through source citations.

### Workflow

1. **Parameter Validation**: Validates the `k` parameter (5-10 range for chunk retrieval)
2. **Indicator ID Lookup**: Retrieves the indicator ID from the database using the indicator code
3. **Chain Creation**: Creates a filtered extraction chain for the specific company and year
4. **Extraction**: Executes the LangChain chain to extract the indicator value
5. **Citation Retrieval**: Gets chunk IDs from page numbers for source citations
6. **Model Conversion**: Converts LLM output to ExtractedIndicator model
7. **Return**: Returns complete ExtractedIndicator with confidence and citations

### Key Features

- **Filtered Retrieval**: Uses company and year filtering to reduce search space from 40k+ to ~200-500 embeddings
- **Structured Output**: Uses Pydantic models for validated, structured extraction
- **Confidence Scoring**: Includes LLM confidence scores (0.0-1.0) for each extraction
- **Source Citations**: Tracks page numbers and chunk IDs for full transparency
- **Error Handling**: Includes retry logic with exponential backoff for API failures
- **Validation**: Validates k parameter and handles missing indicators gracefully

### Parameters

- `indicator_definition`: BRSR indicator definition with schema details
- `company_name`: Name of the company (e.g., "RELIANCE")
- `report_year`: Year of the report (e.g., 2024)
- `object_key`: MinIO object key for the source document
- `company_id`: Database ID of the company
- `connection_string`: PostgreSQL connection string
- `google_api_key`: Google GenAI API key
- `k`: Number of chunks to retrieve (default: 10, range: 5-10)
- `model_name`: Google GenAI model (default: "gemini-2.5-flash")
- `temperature`: LLM temperature (default: 0.1 for consistency)

### Returns

`ExtractedIndicator` object containing:
- `extracted_value`: Raw text value from the document
- `numeric_value`: Numeric representation if applicable
- `confidence_score`: LLM confidence (0.0-1.0)
- `source_pages`: List of PDF page numbers
- `source_chunk_ids`: List of embedding IDs used
- `validation_status`: Initial status ("pending")

### Example Usage

```python
from src.config import config
from src.db.repository import load_brsr_indicators
from src.extraction.extractor import extract_indicator

# Load indicator definitions
indicators = load_brsr_indicators()
ghg_indicator = next(
    ind for ind in indicators 
    if ind.indicator_code == "GHG_SCOPE1"
)

# Extract indicator
result = extract_indicator(
    indicator_definition=ghg_indicator,
    company_name="RELIANCE",
    report_year=2024,
    object_key="RELIANCE/2024_BRSR.pdf",
    company_id=1,
    connection_string=config.database_url,
    google_api_key=config.google_api_key,
    k=10
)

print(f"Extracted: {result.extracted_value}")
print(f"Confidence: {result.confidence_score}")
print(f"Pages: {result.source_pages}")
```

## Helper Functions

### `_get_chunk_ids_from_pages()`

Retrieves chunk IDs for given page numbers from the database. This enables full source citation tracking by linking extracted values to specific document chunks.

## Requirements Coverage

This module satisfies the following requirements:

- **6.1**: Retrieve relevant context chunks using Vector Similarity Search with pgvector
- **6.2**: Construct a LangChain retrieval chain with Google GenAI
- **6.3**: Use LangChain structured output to extract numeric, textual, and qualitative values
- **13.1**: Request confidence scores from the LLM for each extracted value

## Testing

Run the structure tests:

```bash
uv run python test_extractor.py
```

For integration tests with real data:

1. Set up PostgreSQL with pgvector and embeddings
2. Configure valid Google API key in `.env`
3. Run integration tests (to be implemented)

## Main Function: `extract_indicators_batch()`

### Purpose

Extracts multiple BRSR Core indicators in batches for efficient processing. Groups indicators by BRSR attribute (1-9) and processes them sequentially with graceful error handling.

### Workflow

1. **Parse Object Key**: Extracts company name and report year from object key
2. **Company Lookup**: Retrieves company ID from database
3. **Load Indicators**: Loads all BRSR indicators if not provided
4. **Group by Attribute**: Groups indicators by BRSR attribute (1-9)
5. **Batch Processing**: Processes each attribute batch sequentially
6. **Individual Extraction**: Calls `extract_indicator()` for each indicator
7. **Error Handling**: Logs failures but continues processing
8. **Collection**: Collects all successfully extracted indicators
9. **Return**: Returns list of ExtractedIndicator objects

### Key Features

- **Efficient Batching**: Groups related indicators by attribute to reduce redundant processing
- **Graceful Failures**: Individual indicator failures don't stop the batch
- **Comprehensive Logging**: Tracks progress, success/failure statistics, and confidence distribution
- **Flexible Input**: Can process all indicators or a specific subset
- **Partial Results**: Returns all successful extractions even if some fail

### Parameters

- `object_key`: MinIO object key (e.g., "RELIANCE/2024_BRSR.pdf")
- `connection_string`: PostgreSQL connection string
- `google_api_key`: Google GenAI API key
- `indicators`: Optional list of indicators (default: None loads all)
- `k`: Number of chunks to retrieve per indicator (default: 10)
- `model_name`: Google GenAI model (default: "gemini-2.5-flash")
- `temperature`: LLM temperature (default: 0.1)

### Returns

`list[ExtractedIndicator]`: List of successfully extracted indicators (may be less than total if some fail)

### Example Usage

```python
from src.config import config
from src.extraction.extractor import extract_indicators_batch
from src.db.repository import store_extracted_indicators

# Extract all indicators for a document
results = extract_indicators_batch(
    object_key="RELIANCE/2024_BRSR.pdf",
    connection_string=config.database_url,
    google_api_key=config.google_api_key,
    k=10
)

print(f"Extracted {len(results)} indicators")

# Store in database
if results:
    stored_count = store_extracted_indicators(results)
    print(f"Stored {stored_count} indicators")
```

### Extract Specific Attributes

```python
from src.db.repository import get_indicators_by_attribute

# Extract only Environmental indicators (attributes 1-3)
indicators = []
for attr_num in [1, 2, 3]:  # GHG, Water, Energy
    indicators.extend(get_indicators_by_attribute(attr_num))

results = extract_indicators_batch(
    object_key="RELIANCE/2024_BRSR.pdf",
    connection_string=config.database_url,
    google_api_key=config.google_api_key,
    indicators=indicators,  # Pass specific indicators
    k=10
)
```

## Requirements Coverage

This module satisfies the following requirements:

- **6.1**: Retrieve relevant context chunks using Vector Similarity Search with pgvector
- **6.2**: Construct a LangChain retrieval chain with Google GenAI
- **6.3**: Use LangChain structured output to extract numeric, textual, and qualitative values
- **12.1**: Group related BRSR Core indicators by attribute for batch extraction
- **12.2**: Use LangChain structured output with nested Pydantic models for multiple indicators
- **12.3**: Process all 9 BRSR Core attributes in separate extraction batches
- **12.5**: Log failure but continue processing remaining indicators
- **13.1**: Request confidence scores from the LLM for each extracted value

## Testing

Run the structure tests:

```bash
# Test single indicator extraction
uv run python test_extractor.py

# Test batch extraction
uv run python test_extractor_batch.py
```

View example usage:

```bash
uv run python example_batch_usage.py
```

For integration tests with real data:

1. Set up PostgreSQL with pgvector and embeddings
2. Configure valid Google API key in `.env`
3. Run integration tests (to be implemented)

## Next Steps

- Task 11: Add validation and confidence scoring
- Task 15: Create main extraction worker with RabbitMQ integration
