"""
Unit tests for the validation module.

Tests cover:
1. Confidence score validation
2. Required field validation
3. Data type validation
4. Numeric range validation
5. Unit consistency validation
6. Integration with ExtractedIndicator model

Requirements: 13.1, 13.2, 13.3, 13.4
"""

import pytest
from src.models.brsr_models import (
    BRSRIndicatorDefinition,
    ExtractedIndicator,
    Pillar,
)
from src.validation import validate_indicator, ValidationResult


# Fixtures for common test data
@pytest.fixture
def ghg_indicator_definition():
    """BRSR indicator definition for GHG Scope 1 emissions."""
    return BRSRIndicatorDefinition(
        indicator_code="GHG_SCOPE1_TOTAL",
        attribute_number=1,
        parameter_name="Total Scope 1 emissions",
        measurement_unit="MT CO2e",
        description="Direct GHG emissions from owned or controlled sources",
        pillar=Pillar.ENVIRONMENTAL,
        weight=1.0,
        data_assurance_approach="Fossil fuel consumption, emission factors",
        brsr_reference="Principle 6, Question 7 of Essential Indicators",
    )


@pytest.fixture
def percentage_indicator_definition():
    """BRSR indicator definition for a percentage-based indicator."""
    return BRSRIndicatorDefinition(
        indicator_code="ENERGY_RENEWABLE_PERCENT",
        attribute_number=3,
        parameter_name="Energy from renewable sources",
        measurement_unit="%",
        description="Percentage of energy consumed from renewable sources",
        pillar=Pillar.ENVIRONMENTAL,
        weight=1.0,
        data_assurance_approach="Renewable energy consumed / total energy consumed",
        brsr_reference="Principle 6, Question 1 of Essential Indicators",
    )


@pytest.fixture
def valid_extracted_indicator():
    """Valid extracted indicator for testing."""
    return ExtractedIndicator(
        object_key="RELIANCE/2024_BRSR.pdf",
        company_id=1,
        report_year=2024,
        indicator_id=1,
        extracted_value="1250 MT CO2e",
        numeric_value=1250.0,
        confidence_score=0.95,
        validation_status="pending",
        source_pages=[45, 46],
        source_chunk_ids=[123, 124, 125],
    )


# Test: Valid indicator passes all validations
def test_valid_indicator_passes_validation(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that a valid indicator passes all validation checks."""
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert result.is_valid
    assert result.validation_status == "valid"
    assert len(result.errors) == 0


# Test: Confidence score validation
def test_confidence_score_below_zero_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that confidence score below 0.0 fails validation."""
    valid_extracted_indicator.confidence_score = -0.1
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert result.validation_status == "invalid"
    assert any("confidence score" in err.lower() for err in result.errors)


def test_confidence_score_above_one_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that confidence score above 1.0 fails validation."""
    valid_extracted_indicator.confidence_score = 1.5
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert result.validation_status == "invalid"
    assert any("confidence score" in err.lower() for err in result.errors)


def test_confidence_score_at_boundaries_passes(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that confidence scores at 0.0 and 1.0 pass validation."""
    # Test 0.0
    valid_extracted_indicator.confidence_score = 0.0
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    assert result.is_valid
    
    # Test 1.0
    valid_extracted_indicator.confidence_score = 1.0
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    assert result.is_valid


# Test: Required field validation
def test_empty_extracted_value_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that empty extracted_value fails validation."""
    valid_extracted_indicator.extracted_value = ""
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert any("extracted_value" in err.lower() for err in result.errors)


def test_invalid_indicator_id_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that invalid indicator_id fails validation."""
    valid_extracted_indicator.indicator_id = 0
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert any("indicator_id" in err.lower() for err in result.errors)


def test_invalid_company_id_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that invalid company_id fails validation."""
    valid_extracted_indicator.company_id = -1
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert any("company_id" in err.lower() for err in result.errors)


def test_invalid_report_year_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that invalid report_year fails validation."""
    valid_extracted_indicator.report_year = 1999
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert any("report_year" in err.lower() for err in result.errors)


def test_empty_object_key_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that empty object_key fails validation."""
    valid_extracted_indicator.object_key = ""
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert any("object_key" in err.lower() for err in result.errors)


# Test: Data type validation
def test_missing_numeric_value_for_quantitative_indicator_warns(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that missing numeric_value for quantitative indicator produces warning."""
    valid_extracted_indicator.numeric_value = None
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    # Should still be valid but with warnings
    assert result.is_valid
    assert len(result.warnings) > 0
    assert any("numeric value" in warn.lower() for warn in result.warnings)


def test_numeric_value_with_qualitative_indicator_warns():
    """Test that numeric_value with qualitative indicator produces warning."""
    qualitative_def = BRSRIndicatorDefinition(
        indicator_code="QUALITATIVE_TEST",
        attribute_number=1,
        parameter_name="Qualitative Parameter",
        measurement_unit="N/A",
        description="A qualitative indicator",
        pillar=Pillar.GOVERNANCE,
        weight=1.0,
        data_assurance_approach="Manual review",
        brsr_reference="Test",
    )
    
    extracted = ExtractedIndicator(
        object_key="TEST/2024_BRSR.pdf",
        company_id=1,
        report_year=2024,
        indicator_id=1,
        extracted_value="Yes",
        numeric_value=1.0,  # Numeric value for qualitative indicator
        confidence_score=0.9,
        validation_status="pending",
        source_pages=[1],
        source_chunk_ids=[1],
    )
    
    result = validate_indicator(extracted, qualitative_def)
    
    assert result.is_valid
    assert len(result.warnings) > 0


# Test: Numeric range validation
def test_negative_value_for_ghg_fails(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that negative value for GHG emissions fails validation."""
    valid_extracted_indicator.numeric_value = -100.0
    valid_extracted_indicator.extracted_value = "-100 MT CO2e"
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert any("below minimum" in err.lower() for err in result.errors)


def test_percentage_above_100_fails(
    valid_extracted_indicator, percentage_indicator_definition
):
    """Test that percentage value above 100 fails validation."""
    valid_extracted_indicator.numeric_value = 150.0
    valid_extracted_indicator.extracted_value = "150%"
    
    result = validate_indicator(
        valid_extracted_indicator, percentage_indicator_definition
    )
    
    assert not result.is_valid
    assert any("exceeds maximum" in err.lower() for err in result.errors)


def test_zero_value_allowed_for_ghg(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that zero value is allowed for GHG emissions."""
    valid_extracted_indicator.numeric_value = 0.0
    valid_extracted_indicator.extracted_value = "0 MT CO2e"
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert result.is_valid


def test_extremely_large_value_warns(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that extremely large values produce warnings."""
    valid_extracted_indicator.numeric_value = 1e16  # 10 quadrillion
    valid_extracted_indicator.extracted_value = "10000000000000000 MT CO2e"
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    # Should be valid but with warning
    assert result.is_valid
    assert len(result.warnings) > 0
    assert any("extremely large" in warn.lower() for warn in result.warnings)


# Test: Unit consistency validation
def test_missing_unit_in_extracted_value_warns(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that missing unit in extracted value produces warning."""
    valid_extracted_indicator.extracted_value = "1250"  # No unit
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    # Should be valid but with warning
    assert result.is_valid
    assert len(result.warnings) > 0
    assert any("unit" in warn.lower() for warn in result.warnings)


def test_unit_variations_recognized(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that unit variations are recognized."""
    # Test various unit formats
    unit_formats = [
        "1250 MT CO2e",
        "1250 MT CO2",
        "1250 metric tons CO2e",
        "1250 tonnes CO2e",
    ]
    
    for unit_format in unit_formats:
        valid_extracted_indicator.extracted_value = unit_format
        result = validate_indicator(
            valid_extracted_indicator, ghg_indicator_definition
        )
        assert result.is_valid


def test_percentage_unit_recognized(
    valid_extracted_indicator, percentage_indicator_definition
):
    """Test that percentage unit variations are recognized."""
    percentage_formats = [
        "45%",
        "45 percent",
        "45 percentage",
        "45 pct",
    ]
    
    for pct_format in percentage_formats:
        valid_extracted_indicator.extracted_value = pct_format
        valid_extracted_indicator.numeric_value = 45.0
        result = validate_indicator(
            valid_extracted_indicator, percentage_indicator_definition
        )
        assert result.is_valid


# Test: Multiple validation errors
def test_multiple_validation_errors_reported(
    valid_extracted_indicator, ghg_indicator_definition
):
    """Test that multiple validation errors are all reported."""
    # Create multiple errors
    valid_extracted_indicator.confidence_score = 1.5  # Invalid
    valid_extracted_indicator.extracted_value = ""  # Empty
    valid_extracted_indicator.numeric_value = -100.0  # Negative
    
    result = validate_indicator(valid_extracted_indicator, ghg_indicator_definition)
    
    assert not result.is_valid
    assert len(result.errors) >= 3  # At least 3 errors


# Test: ValidationResult dataclass
def test_validation_result_structure():
    """Test that ValidationResult has correct structure."""
    result = ValidationResult(
        is_valid=True,
        validation_status="valid",
        errors=[],
        warnings=["Test warning"],
    )
    
    assert result.is_valid
    assert result.validation_status == "valid"
    assert len(result.errors) == 0
    assert len(result.warnings) == 1


def test_validation_result_auto_corrects_status():
    """Test that ValidationResult auto-corrects inconsistent status."""
    # Create with inconsistent status
    result = ValidationResult(
        is_valid=True,
        validation_status="invalid",  # Inconsistent
        errors=[],
        warnings=[],
    )
    
    # Should auto-correct to "valid"
    assert result.validation_status == "valid"


# Test: Edge cases
def test_validation_with_no_numeric_value_and_no_unit():
    """Test validation when both numeric_value and unit are None."""
    qualitative_def = BRSRIndicatorDefinition(
        indicator_code="QUALITATIVE_TEST",
        attribute_number=9,
        parameter_name="Qualitative Parameter",
        measurement_unit=None,
        description="A qualitative indicator",
        pillar=Pillar.GOVERNANCE,
        weight=1.0,
        data_assurance_approach="Manual review",
        brsr_reference="Test",
    )
    
    extracted = ExtractedIndicator(
        object_key="TEST/2024_BRSR.pdf",
        company_id=1,
        report_year=2024,
        indicator_id=1,
        extracted_value="Yes, implemented",
        numeric_value=None,
        confidence_score=0.8,
        validation_status="pending",
        source_pages=[1],
        source_chunk_ids=[1],
    )
    
    result = validate_indicator(extracted, qualitative_def)
    
    # Should be valid for qualitative indicators
    assert result.is_valid


def test_validation_with_empty_source_pages():
    """Test validation with empty source_pages list."""
    extracted = ExtractedIndicator(
        object_key="TEST/2024_BRSR.pdf",
        company_id=1,
        report_year=2024,
        indicator_id=1,
        extracted_value="1250 MT CO2e",
        numeric_value=1250.0,
        confidence_score=0.95,
        validation_status="pending",
        source_pages=[],  # Empty
        source_chunk_ids=[],
    )
    
    indicator_def = BRSRIndicatorDefinition(
        indicator_code="GHG_SCOPE1_TOTAL",
        attribute_number=1,
        parameter_name="Total Scope 1 emissions",
        measurement_unit="MT CO2e",
        description="Direct GHG emissions",
        pillar=Pillar.ENVIRONMENTAL,
        weight=1.0,
        data_assurance_approach="Fossil fuel consumption",
        brsr_reference="Principle 6, Question 7",
    )
    
    result = validate_indicator(extracted, indicator_def)
    
    # Should still be valid (source_pages is not validated here)
    assert result.is_valid


# Test: Specific indicator types
def test_supplier_payment_days_zero_not_allowed():
    """Test that SUPPLIER_PAYMENT_DAYS does not allow zero."""
    payment_days_def = BRSRIndicatorDefinition(
        indicator_code="SUPPLIER_PAYMENT_DAYS",
        attribute_number=8,
        parameter_name="Days of accounts payable",
        measurement_unit="days",
        description="Average number of days to pay suppliers",
        pillar=Pillar.GOVERNANCE,
        weight=1.0,
        data_assurance_approach="Financial statements",
        brsr_reference="Principle 1, Question 8",
    )
    
    extracted = ExtractedIndicator(
        object_key="TEST/2024_BRSR.pdf",
        company_id=1,
        report_year=2024,
        indicator_id=1,
        extracted_value="0 days",
        numeric_value=0.0,
        confidence_score=0.9,
        validation_status="pending",
        source_pages=[1],
        source_chunk_ids=[1],
    )
    
    result = validate_indicator(extracted, payment_days_def)
    
    # Should produce warning for zero value
    assert result.is_valid  # Still valid
    assert len(result.warnings) > 0
    assert any("zero" in warn.lower() for warn in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
