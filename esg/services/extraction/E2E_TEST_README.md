# End-to-End Extraction Test

## Overview

The `test_e2e_extraction.py` file provides comprehensive end-to-end testing of the extraction service pipeline. It validates the complete workflow from document retrieval through indicator extraction, validation, score calculation, and citation storage.

## Test Coverage

### Task 48 Requirements

This test implements all requirements from task 48:

1. **End-to-end extraction for sample document** ✓
   - Tests complete extraction pipeline from start to finish
   - Validates data flow through all components

2. **Filtered vector retrieval with company/year** ✓
   - Tests `FilteredPGVectorRetriever` with company and year filtering
   - Verifies correct document filtering and metadata
   - Requirements: 6.1, 11.1, 11.2

3. **Indicator extraction and validation** ✓
   - Tests LangChain-based extraction with Google GenAI
   - Validates extracted indicator structure and confidence scores
   - Tests validation logic for numeric ranges and data types
   - Requirements: 6.2, 6.3, 13.1, 13.2, 13.3, 13.4

4. **Score calculation accuracy** ✓
   - Tests pillar score calculation (E, S, G)
   - Tests overall ESG score calculation with weighted aggregation
   - Validates score ranges and metadata
   - Requirements: 15.1, 15.2, 15.3, 15.4, 15.5

5. **Source citation storage** ✓
   - Tests storage of extracted indicators with citations
   - Verifies source pages and chunk IDs are preserved
   - Tests ESG score storage with calculation metadata
   - Requirements: 14.1, 14.2, 14.3, 14.4, 15.5

## Test Structure

### E2ETestResult Class

Container for test results with the following attributes:
- `retrieval_passed`: Boolean indicating if retrieval test passed
- `extraction_passed`: Boolean indicating if extraction test passed
- `validation_passed`: Boolean indicating if validation test passed
- `score_calculation_passed`: Boolean indicating if score calculation test passed
- `citation_storage_passed`: Boolean indicating if citation storage test passed
- `errors`: List of error messages
- `warnings`: List of warning messages
- `extracted_indicators`: List of extracted indicators
- `esg_score`: Calculated ESG score
- `metadata`: Score calculation metadata

Methods:
- `all_passed()`: Returns True if all tests passed
- `summary()`: Generates formatted test summary

### Test Functions

#### 1. test_filtered_retrieval()
Tests the filtered vector retrieval functionality:
- Initializes `FilteredPGVectorRetriever` with company/year
- Executes semantic search query
- Verifies filtering by company_name and report_year
- Validates document metadata (page numbers, chunk IDs)

#### 2. test_indicator_extraction()
Tests the indicator extraction pipeline:
- Extracts multiple BRSR Core indicators
- Uses LangChain with Google GenAI
- Validates structured output
- Verifies confidence scores and source citations

#### 3. test_validation()
Tests indicator validation logic:
- Validates confidence scores (0.0-1.0 range)
- Checks numeric value ranges
- Validates required fields
- Tests data type consistency

#### 4. test_score_calculation()
Tests ESG score calculation:
- Calculates pillar scores (E, S, G)
- Calculates overall ESG score
- Validates weighted aggregation
- Verifies calculation metadata

#### 5. test_citation_storage()
Tests data persistence:
- Stores extracted indicators in database
- Stores ESG scores with metadata
- Verifies data retrieval
- Validates citation preservation

### Main Test Runner

`run_e2e_test()` orchestrates the complete test workflow:
1. Checks prerequisites (API key, database)
2. Loads BRSR indicators
3. Gets company ID
4. Runs all 5 test functions in sequence
5. Generates comprehensive summary

## Prerequisites

Before running the E2E test, ensure:

1. **PostgreSQL with pgvector** is running
   ```bash
   docker-compose up -d postgres
   ```

2. **Document embeddings** are in the database
   - Run the embeddings service to generate embeddings
   - Verify embeddings exist for the test company/year

3. **GOOGLE_API_KEY** environment variable is set
   ```bash
   export GOOGLE_API_KEY="your-api-key"
   ```

4. **BRSR indicators** are seeded in database
   ```bash
   # Run database migrations
   psql -U esg_user -d esg_platform -f infra/db-init/02_brsr_indicators.sql
   ```

5. **Company catalog** is populated
   - Run the company-catalog service to sync companies

## Running the Tests

### Structure Test (No Infrastructure Required)

Validates test structure without requiring database or API:

```bash
cd services/extraction
uv run python tests/test_e2e_structure.py
```

This test verifies:
- All imports work correctly
- Test functions have correct signatures
- Requirements are covered
- Workflow is documented

### Full E2E Test (Requires Infrastructure)

Runs the complete end-to-end test:

```bash
cd services/extraction
uv run python tests/test_e2e_extraction.py
```

Options:
- `--company COMPANY`: Company name to test (default: RELIANCE)
- `--year YEAR`: Report year to test (default: 2024)
- `--max-indicators N`: Maximum indicators to extract (default: 3)

Example:
```bash
uv run python tests/test_e2e_extraction.py --company TCS --year 2023 --max-indicators 5
```

## Test Output

The test generates detailed output for each phase:

```
================================================================================
TEST 1: Filtered Vector Retrieval
================================================================================
Initializing retriever for RELIANCE 2024
Querying: 'What are the total Scope 1 emissions?'
✓ Retrieved 5 documents

Document 1:
  Company: RELIANCE
  Year: 2024
  Page: 45
  Chunk Index: 123
  Distance: 0.1234
  Content: Our total Scope 1 emissions...

✓ Filtered retrieval test PASSED

================================================================================
TEST 2: Indicator Extraction
================================================================================
Testing extraction for 3 indicators

Extracting indicator 1/3:
  Code: GHG_SCOPE1_TOTAL
  Name: Total Scope 1 emissions
  Unit: MT CO2e
  ✓ Extracted value: 1250 MT CO2e
  ✓ Numeric value: 1250.0
  ✓ Confidence: 0.95
  ✓ Source pages: [45, 46]
  ✓ Source chunks: 3 chunks

✓ Extraction test PASSED: 3 indicators extracted

[... additional test output ...]

================================================================================
END-TO-END TEST SUMMARY
================================================================================
✓ Filtered Retrieval: PASS
✓ Indicator Extraction: PASS
✓ Validation: PASS
✓ Score Calculation: PASS
✓ Citation Storage: PASS

Extracted Indicators: 3
ESG Score: 68.50

================================================================================
OVERALL: ✓ ALL TESTS PASSED
================================================================================
```

## Troubleshooting

### No documents retrieved
- Verify embeddings exist for the company/year
- Check database connection
- Ensure pgvector extension is installed

### Extraction fails
- Verify GOOGLE_API_KEY is valid
- Check API rate limits
- Ensure embeddings are properly filtered

### Validation errors
- Review indicator definitions
- Check numeric value ranges
- Verify confidence scores

### Score calculation fails
- Ensure at least one indicator has numeric value
- Check pillar assignments
- Verify weight values

### Storage fails
- Check database permissions
- Verify table schemas exist
- Review foreign key constraints

## Integration with CI/CD

The E2E test can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run E2E Tests
  run: |
    cd services/extraction
    uv run python tests/test_e2e_structure.py
    # Full E2E test requires infrastructure
    # uv run python tests/test_e2e_extraction.py
```

For full E2E testing in CI/CD:
1. Start PostgreSQL with pgvector in Docker
2. Seed test data (companies, indicators, embeddings)
3. Set GOOGLE_API_KEY secret
4. Run test with timeout

## Performance Considerations

- **Test Duration**: 2-5 minutes depending on number of indicators
- **API Calls**: ~3-5 calls to Google GenAI per indicator
- **Database Queries**: ~10-20 queries per test run
- **Memory Usage**: ~200-500 MB

To reduce test time:
- Use `--max-indicators 1` for quick validation
- Cache embeddings between test runs
- Use test-specific company with minimal data

## Future Enhancements

Potential improvements to the E2E test:

1. **Mock Mode**: Add option to mock LLM responses for faster testing
2. **Parallel Extraction**: Test concurrent indicator extraction
3. **Error Injection**: Test error handling and recovery
4. **Performance Benchmarks**: Track extraction speed and accuracy
5. **Comparison Tests**: Compare results across different models
6. **Regression Tests**: Validate against known good results

## Related Files

- `tests/test_e2e_extraction.py`: Main E2E test implementation
- `tests/test_e2e_structure.py`: Structure validation test
- `tests/test_extractor.py`: Unit tests for extractor
- `tests/test_filtered_retriever.py`: Unit tests for retriever
- `tests/test_validator.py`: Unit tests for validator
- `tests/test_esg_calculator.py`: Unit tests for score calculator

## References

- Requirements: `.kiro/specs/esg-intelligence-platform/requirements.md`
- Design: `.kiro/specs/esg-intelligence-platform/design.md`
- Tasks: `.kiro/specs/esg-intelligence-platform/tasks.md` (Task 48)
