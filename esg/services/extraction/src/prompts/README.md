# Extraction Prompts Module

This module provides LangChain prompt templates and output parsers for extracting BRSR Core indicators from company sustainability reports using Google GenAI.

## Overview

The prompts are designed to:
- Extract specific BRSR indicators with high accuracy
- Include confidence scoring (0.0-1.0) for each extraction
- Identify source page numbers for transparency and traceability
- Handle both quantitative and qualitative indicators
- Provide structured output using Pydantic models

## Components

### 1. `create_extraction_prompt()`

Creates a prompt template for extracting a single BRSR indicator.

**Parameters:**
- `company_name`: Name of the company (e.g., "RELIANCE")
- `report_year`: Year of the report (e.g., 2024)
- `indicator_code`: BRSR indicator code (e.g., "GHG_SCOPE1")
- `indicator_name`: Human-readable indicator name
- `indicator_description`: Detailed description of what to extract
- `expected_unit`: Expected unit of measurement (e.g., "MT CO2e")
- `pillar`: ESG pillar - "E", "S", or "G"

**Returns:** `PromptTemplate` configured for single indicator extraction

**Example:**
```python
from src.prompts import create_extraction_prompt

prompt = create_extraction_prompt(
    company_name="RELIANCE",
    report_year=2024,
    indicator_code="GHG_SCOPE1",
    indicator_name="Total Scope 1 emissions",
    indicator_description="Total direct GHG emissions from owned or controlled sources",
    expected_unit="MT CO2e",
    pillar="E"
)

# Use with LangChain
formatted_prompt = prompt.format(context=retrieved_context)
```

### 2. `get_output_parser()`

Returns a `PydanticOutputParser` configured for `BRSRIndicatorOutput` model.

**Returns:** `PydanticOutputParser` for structured output validation

**Example:**
```python
from src.prompts import get_output_parser

parser = get_output_parser()
result = parser.parse(llm_output)

print(result.indicator_code)  # "GHG_SCOPE1"
print(result.confidence)      # 0.95
print(result.source_pages)    # [45, 46]
```

### 3. `create_batch_extraction_prompt()`

Creates a prompt template for extracting multiple indicators in a single pass.

**Parameters:**
- `company_name`: Name of the company
- `report_year`: Year of the report
- `indicators`: List of indicator dictionaries with keys:
  - `indicator_code`
  - `indicator_name`
  - `indicator_description`
  - `expected_unit`
  - `pillar`

**Returns:** `PromptTemplate` configured for batch extraction

**Example:**
```python
from src.prompts import create_batch_extraction_prompt

indicators = [
    {
        "indicator_code": "GHG_SCOPE1",
        "indicator_name": "Total Scope 1 emissions",
        "indicator_description": "Direct GHG emissions",
        "expected_unit": "MT CO2e",
        "pillar": "E"
    },
    # ... more indicators
]

prompt = create_batch_extraction_prompt(
    company_name="RELIANCE",
    report_year=2024,
    indicators=indicators
)
```

### 4. `format_context_from_documents()`

Helper function to format retrieved LangChain documents into a context string.

**Parameters:**
- `documents`: List of LangChain Document objects

**Returns:** Formatted context string with page numbers

**Example:**
```python
from src.prompts import format_context_from_documents

docs = retriever.get_relevant_documents(query)
context = format_context_from_documents(docs)
```

## Prompt Template Structure

The extraction prompt includes:

1. **Company Context**: Company name, report year, report type
2. **Indicator Details**: Code, name, description, expected unit, pillar
3. **Extraction Instructions**: Guidelines for accuracy and confidence scoring
4. **Context**: Retrieved text chunks from the document
5. **Format Instructions**: Pydantic schema for structured output

## Confidence Scoring Guidelines

The prompt instructs the LLM to use the following confidence scale:

- **1.0**: Value explicitly stated with clear labeling
- **0.8-0.9**: Value clearly stated but requires minor interpretation
- **0.6-0.7**: Value found but requires moderate interpretation or calculation
- **0.4-0.5**: Value inferred from related information
- **0.0-0.3**: Value not found or highly uncertain

## Output Schema

The structured output follows the `BRSRIndicatorOutput` Pydantic model:

```python
{
    "indicator_code": "GHG_SCOPE1",
    "value": "1250 MT CO2e",
    "numeric_value": 1250.0,
    "unit": "MT CO2e",
    "confidence": 0.95,
    "source_pages": [45, 46]
}
```

## Integration with LangChain

### Basic Usage

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from src.prompts import create_extraction_prompt, get_output_parser
from src.retrieval import FilteredPGVectorRetriever

# Initialize components
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
retriever = FilteredPGVectorRetriever(
    connection_string=DB_CONNECTION,
    company_name="RELIANCE",
    report_year=2024
)
prompt = create_extraction_prompt(
    company_name="RELIANCE",
    report_year=2024,
    indicator_code="GHG_SCOPE1",
    indicator_name="Total Scope 1 emissions",
    indicator_description="Total direct GHG emissions",
    expected_unit="MT CO2e",
    pillar="E"
)
parser = get_output_parser()

# Retrieve relevant documents
docs = retriever.get_relevant_documents("Total Scope 1 emissions", k=5)
context = format_context_from_documents(docs)

# Build and execute chain
chain = prompt | llm | parser
result = chain.invoke({"context": context})

print(f"Extracted: {result.value}")
print(f"Confidence: {result.confidence}")
print(f"Pages: {result.source_pages}")
```

### With RetrievalQA Chain

```python
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt}
)

result = qa_chain.run("Extract Total Scope 1 emissions")
```

## Testing

Run the test suite to verify the prompts:

```bash
cd services/extraction
uv run python test_extraction_prompts.py
```

## Requirements Mapping

This module satisfies the following requirements:

- **6.2**: LangChain integration for indicator extraction
- **6.3**: Structured output using Pydantic models
- **11.3**: Prompt templates for BRSR Core indicator extraction

## Next Steps

1. Integrate with `FilteredPGVectorRetriever` (Task 6)
2. Build extraction chain with Google GenAI (Task 8)
3. Implement single indicator extraction function (Task 9)
4. Implement batch extraction for multiple indicators (Task 10)
