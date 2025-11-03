# Test Fixtures

This directory contains sample data and fixtures for integration tests.

## Files

### sample_data.py
Contains sample data for testing various components:

- **SAMPLE_COMPANIES**: Basic company data for testing
- **EXTENDED_SAMPLE_COMPANIES**: More realistic company data with additional fields
- **SAMPLE_BRSR_INDICATORS**: Subset of BRSR indicators for testing
- **COMPREHENSIVE_BRSR_INDICATORS**: Complete set of BRSR indicators covering all pillars (E/S/G)
- **SAMPLE_EXTRACTED_INDICATORS**: Sample extracted indicator data
- **REALISTIC_EXTRACTED_INDICATORS**: More realistic extracted indicators with citations
- **SAMPLE_ESG_SCORES**: Sample ESG scores
- **REALISTIC_ESG_SCORES**: More realistic ESG scores with calculation dates
- **SAMPLE_DOCUMENTS**: Sample document metadata
- **SAMPLE_INGESTION_METADATA**: Sample ingestion metadata
- **SAMPLE_EMBEDDINGS**: Sample embedding data
- **SAMPLE_USERS**: Sample user data for authentication tests
- **SAMPLE_API_KEYS**: Sample API keys for authentication tests

### sample_brsr_report.pdf
A minimal valid PDF file containing sample BRSR data for testing document upload and processing.

## Usage

```python
from tests.fixtures.sample_data import (
    get_sample_company,
    get_extended_company,
    get_comprehensive_indicator,
    get_sample_pdf_path,
    get_sample_pdf_content
)

# Get sample company data
company = get_sample_company(0)

# Get path to sample PDF
pdf_path = get_sample_pdf_path()

# Get PDF content as bytes
pdf_content = get_sample_pdf_content()
```

## Notes

- All sample data is designed to be realistic but clearly identifiable as test data
- The sample PDF contains actual BRSR indicator values that can be extracted
- Sample data should not conflict with production data
- Use the helper functions to access data rather than importing constants directly
