# Validation Module

This module provides comprehensive validation for extracted BRSR Core indicators.

## Overview

The validation module ensures data quality and consistency by validating extracted indicators against BRSR schema definitions and business rules. It performs multiple validation checks while preserving raw extracted values for transparency.

## Key Features

1. **Confidence Score Validation**: Ensures confidence scores are between 0.0 and 1.0
2. **Required Field Validation**: Checks that all mandatory fields are present and valid
3. **Data Type Validation**: Verifies numeric values match expected types based on measurement units
4. **Numeric Range Validation**: Validates values against expected ranges for each indicator type
5. **Unit Consistency Validation**: Checks that extracted values mention expected units

## Usage

### Basic Validation

```python
from src.validation import validate_indicator, ValidationResult
from src.models.brsr_models import ExtractedIndicator, BRSRIndicatorDefinition

# Validate an extracted indicator
result: ValidationResult = validate_indicator(
    extracted_indicator=extracted,
    indicator_definition=indicator_def
)

# Check validation status
if result.is_valid:
    print("Indicator is valid!")
else:
    print(f"Validation failed: {result.errors}")

# Check warnings
if result.warnings:
    print(f"Warnings: {result.warnings}")
```

### Integration with Extraction Pipeline

```python
from src.extraction.extractor import extract_indicator
from src.validation import validate_indicator

# Extract indicator
extracted = extract_indicator(
    indicator_definition=indicator_def,
    company_name="RELIANCE",
    report_year=2024,
    object_key="RELIANCE/2024_BRSR.pdf",
    company_id=1,
    connection_string=config.database_url,
    google_api_key=config.google_api_key
)

# Validate extracted indicator
validation_result = validate_indicator(
    extracted_indicator=extracted,
    indicator_definition=indicator_def
)

# Update validation status
extracted.validation_status = validation_result.validation_status

# Store with validation status
store_extracted_indicators([extracted])
```

### Batch Validation

```python
from src.extraction.extractor import extract_indicators_batch
from src.validation import validate_indicator
from src.db.repository import load_brsr_indicators

# Extract all indicators
indicators_def = load_brsr_indicators()
extracted_indicators = extract_indicators_batch(
    object_key="RELIANCE/2024_BRSR.pdf",
    connection_string=config.database_url,
    google_api_key=config.google_api_key
)

# Validate each indicator
for extracted in extracted_indicators:
    # Find corresponding definition
    indicator_def = next(
        ind for ind in indicators_def
        if ind.indicator_code == extracted.indicator_id
    )
    
    # Validate
    result = validate_indicator(extracted, indicator_def)
    
    # Update status
    extracted.validation_status = result.validation_status
    
    # Log issues
    if not result.is_valid:
        logger.warning(f"Validation failed for {indicator_def.indicator_code}: {result.errors}")
```

## Validation Rules

### Confidence Score Validation

- **Rule**: Confidence score must be between 0.0 and 1.0 (inclusive)
- **Error**: Raised if score is outside this range
- **Requirement**: 13.1, 13.4

### Required Fields Validation

- **Fields**: `extracted_value`, `indicator_id`, `company_id`, `report_year`, `object_key`
- **Rule**: All fields must be present and non-empty/positive
- **Error**: Raised if any required field is missing or invalid
- **Requirement**: 13.3

### Data Type Validation

- **Rule**: `numeric_value` should be provided for quantitative indicators (based on measurement unit)
- **Warning**: Issued if numeric value is missing for quantitative indicators
- **Warning**: Issued if numeric value is provided for qualitative indicators
- **Error**: Raised if `numeric_value` is not int or float when present
- **Requirement**: 13.3

### Numeric Range Validation

Validates numeric values against expected ranges for each indicator type:

#### Environmental Indicators
- **GHG Emissions** (MT CO2e): 0 to unlimited, zero allowed
- **Water** (KL): 0 to unlimited, zero allowed
- **Energy** (Joules): 0 to unlimited, zero allowed
- **Energy Renewable %**: 0 to 100, zero allowed
- **Waste** (MT): 0 to unlimited, zero allowed

#### Social Indicators
- **Employee Wellbeing %**: 0 to 100, zero allowed
- **Safety LTIFR**: 0 to unlimited, zero allowed
- **Safety Fatalities/Disabilities**: 0 to unlimited, zero allowed
- **Gender Wage %**: 0 to 100, zero allowed
- **POSH Complaints**: 0 to unlimited, zero allowed
- **Inclusive Sourcing %**: 0 to 100, zero allowed

#### Governance Indicators
- **Data Breach %**: 0 to 100, zero allowed
- **Supplier Payment Days**: 0 to unlimited, zero NOT allowed (must be > 0)
- **Trading House/Dealer %**: 0 to 100, zero allowed
- **RPT %**: 0 to 100, zero allowed

**Requirement**: 13.2

### Unit Consistency Validation

- **Rule**: Extracted value should mention the expected measurement unit
- **Warning**: Issued if unit is not found in extracted value
- **Examples**:
  - "1250 MT CO2e" ✓ (contains "MT CO2e")
  - "1250" ✗ (missing unit)
  - "45%" ✓ (contains "%")
- **Requirement**: 13.2

## Validation Result

The `ValidationResult` dataclass contains:

```python
@dataclass
class ValidationResult:
    is_valid: bool              # Overall validation status
    validation_status: str      # 'valid', 'invalid', or 'pending'
    errors: List[str]           # List of validation errors
    warnings: List[str]         # List of validation warnings
```

### Status Values

- **`valid`**: All validation checks passed (may have warnings)
- **`invalid`**: One or more validation checks failed (has errors)
- **`pending`**: Initial status before validation (not set by validator)

## Error Handling

The validator follows these principles:

1. **Non-Destructive**: Never modifies the extracted indicator values
2. **Transparent**: All validation errors and warnings are logged
3. **Graceful**: Validation failures don't stop the extraction pipeline
4. **Informative**: Error messages include specific details about what failed

### Example Error Messages

```python
# Confidence score error
"Confidence score 1.5 is outside valid range [0.0, 1.0]"

# Required field error
"extracted_value is required and cannot be empty"

# Range validation error
"Value 150 exceeds maximum 100 for ENERGY_RENEWABLE_PERCENT"

# Unit consistency warning
"Expected unit 'MT CO2e' not found in extracted value '1250'. Verify unit consistency."
```

## Extending Validation

### Adding New Indicator Ranges

To add validation ranges for new indicators, update the `NUMERIC_RANGES` dictionary in `validator.py`:

```python
NUMERIC_RANGES: Dict[str, Tuple[Optional[float], Optional[float], bool]] = {
    # ...existing ranges...
    
    # Add new indicator
    "NEW_INDICATOR_CODE": (min_value, max_value, allow_zero),
}
```

### Adding Custom Validation Rules

To add custom validation logic, create a new validation function:

```python
def _validate_custom_rule(
    extracted_indicator: ExtractedIndicator,
    indicator_definition: BRSRIndicatorDefinition,
    errors: List[str],
    warnings: List[str],
) -> bool:
    """Custom validation logic."""
    # Implement validation
    if some_condition:
        errors.append("Custom validation failed")
        return False
    return True
```

Then call it from `validate_indicator()`:

```python
def validate_indicator(...) -> ValidationResult:
    # ...existing validations...
    
    # Add custom validation
    if not _validate_custom_rule(extracted_indicator, indicator_definition, errors, warnings):
        logger.warning(f"Custom validation failed for {indicator_definition.indicator_code}")
    
    # ...rest of function...
```

## Testing

### Unit Tests

```python
import pytest
from src.validation import validate_indicator, ValidationResult
from src.models.brsr_models import ExtractedIndicator, BRSRIndicatorDefinition

def test_valid_indicator():
    """Test validation of a valid indicator."""
    indicator_def = BRSRIndicatorDefinition(
        indicator_code="GHG_SCOPE1_TOTAL",
        attribute_number=1,
        parameter_name="Total Scope 1 emissions",
        measurement_unit="MT CO2e",
        description="Direct GHG emissions",
        pillar="E",
        weight=1.0,
        data_assurance_approach="Fossil fuel consumption",
        brsr_reference="Principle 6, Question 7"
    )
    
    extracted = ExtractedIndicator(
        object_key="RELIANCE/2024_BRSR.pdf",
        company_id=1,
        report_year=2024,
        indicator_id=1,
        extracted_value="1250 MT CO2e",
        numeric_value=1250.0,
        confidence_score=0.95,
        validation_status="pending",
        source_pages=[45],
        source_chunk_ids=[123]
    )
    
    result = validate_indicator(extracted, indicator_def)
    
    assert result.is_valid
    assert result.validation_status == "valid"
    assert len(result.errors) == 0

def test_invalid_confidence_score():
    """Test validation fails for invalid confidence score."""
    # ...setup...
    extracted.confidence_score = 1.5  # Invalid
    
    result = validate_indicator(extracted, indicator_def)
    
    assert not result.is_valid
    assert result.validation_status == "invalid"
    assert any("confidence score" in err.lower() for err in result.errors)
```

## Requirements Mapping

- **Requirement 13.1**: Confidence scoring - Implemented in `_validate_confidence_score()`
- **Requirement 13.2**: Numeric range validation - Implemented in `_validate_numeric_range()` and `_validate_unit_consistency()`
- **Requirement 13.3**: Required fields and data types - Implemented in `_validate_required_fields()` and `_validate_data_types()`
- **Requirement 13.4**: Confidence score range - Enforced in `_validate_confidence_score()` and Pydantic model validators

## Performance Considerations

- Validation is performed in-memory with no database queries
- Regex operations are minimal and optimized
- Validation typically takes < 1ms per indicator
- Can validate 1000+ indicators per second

## Logging

The validator uses Python's standard logging module:

```python
import logging

logger = logging.getLogger(__name__)

# Configure logging level
logging.basicConfig(level=logging.INFO)

# Validation logs
logger.debug("Validating indicator...")  # Detailed validation steps
logger.info("Indicator is valid")        # Successful validation
logger.warning("Validation failed...")   # Validation errors
```
