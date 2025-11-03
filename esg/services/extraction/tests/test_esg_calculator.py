"""
Unit tests for overall ESG score calculation.

This test file verifies the ESG score calculation logic including:
- Overall score calculation with configurable weights
- Weight adjustment for missing pillars
- Calculation metadata generation
- Source citation integration

Requirements: 15.3, 15.4, 15.5
"""

import pytest
from src.models.brsr_models import BRSRIndicatorDefinition, Pillar
from src.scoring.esg_calculator import (
    calculate_esg_score,
    get_esg_score_with_citations,
    _validate_pillar_weights,
    _calculate_weighted_esg_score,
    DEFAULT_PILLAR_WEIGHTS,
)


# Sample indicator definitions for testing
SAMPLE_INDICATORS = [
    # Environmental indicators
    BRSRIndicatorDefinition(
        indicator_code="GHG_SCOPE1_TOTAL",
        attribute_number=1,
        parameter_name="Total Scope 1 emissions",
        measurement_unit="MT CO2e",
        description="Direct GHG emissions",
        pillar=Pillar.ENVIRONMENTAL,
        weight=1.0,
        data_assurance_approach="Fossil fuel consumption",
        brsr_reference="Principle 6, Question 7",
    ),
    BRSRIndicatorDefinition(
        indicator_code="ENERGY_RENEWABLE_PERCENT",
        attribute_number=3,
        parameter_name="Energy from renewable sources",
        measurement_unit="%",
        description="Percentage of renewable energy",
        pillar=Pillar.ENVIRONMENTAL,
        weight=1.0,
        data_assurance_approach="Energy consumption records",
        brsr_reference="Principle 6, Question 1",
    ),
    # Social indicators
    BRSRIndicatorDefinition(
        indicator_code="EMPLOYEE_WELLBEING_SPEND_PERCENT",
        attribute_number=5,
        parameter_name="Spending on employee wellbeing",
        measurement_unit="%",
        description="Wellbeing spend as % of revenue",
        pillar=Pillar.SOCIAL,
        weight=1.0,
        data_assurance_approach="Financial records",
        brsr_reference="Principle 3, Question 1(c)",
    ),
    BRSRIndicatorDefinition(
        indicator_code="GENDER_WAGE_PERCENT",
        attribute_number=6,
        parameter_name="Gross wages paid to females",
        measurement_unit="%",
        description="Female wages as % of total",
        pillar=Pillar.SOCIAL,
        weight=1.0,
        data_assurance_approach="Payroll data",
        brsr_reference="Principle 5, Question 3(b)",
    ),
    # Governance indicators
    BRSRIndicatorDefinition(
        indicator_code="CUSTOMER_DATA_BREACH_PERCENT",
        attribute_number=8,
        parameter_name="Customer data breach incidents",
        measurement_unit="%",
        description="Data breaches as % of cyber events",
        pillar=Pillar.GOVERNANCE,
        weight=1.0,
        data_assurance_approach="Security reports",
        brsr_reference="Principle 9, Question 7",
    ),
]


def test_calculate_esg_score_all_pillars():
    """Test ESG score calculation with all three pillars."""
    extracted_values = {
        "GHG_SCOPE1_TOTAL": 1250.0,
        "ENERGY_RENEWABLE_PERCENT": 60.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.0,
        "GENDER_WAGE_PERCENT": 40.0,
        "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
    }
    
    score, metadata = calculate_esg_score(SAMPLE_INDICATORS, extracted_values)
    
    # Should have a score
    assert score is not None
    assert 0 <= score <= 100
    
    # Metadata should have pillar scores
    assert metadata["pillar_scores"]["environmental"] is not None
    assert metadata["pillar_scores"]["social"] is not None
    assert metadata["pillar_scores"]["governance"] is not None
    
    # Weights should be default
    assert metadata["pillar_weights"]["environmental"] == 0.33
    assert metadata["pillar_weights"]["social"] == 0.33
    assert metadata["pillar_weights"]["governance"] == 0.34
    
    # Should have calculation method
    assert "calculation_method" in metadata
    assert "weighted average" in metadata["calculation_method"].lower()
    
    # Should have timestamp
    assert "calculated_at" in metadata
    
    print(f"ESG Score: {score:.2f}")
    print(f"Environmental: {metadata['pillar_scores']['environmental']:.2f}")
    print(f"Social: {metadata['pillar_scores']['social']:.2f}")
    print(f"Governance: {metadata['pillar_scores']['governance']:.2f}")


def test_calculate_esg_score_custom_weights():
    """Test ESG score calculation with custom pillar weights."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 60.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.0,
        "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
    }
    
    # Custom weights favoring environmental
    custom_weights = {
        "E": 0.5,
        "S": 0.3,
        "G": 0.2,
    }
    
    score, metadata = calculate_esg_score(
        SAMPLE_INDICATORS,
        extracted_values,
        pillar_weights=custom_weights
    )
    
    # Should use custom weights
    assert metadata["original_weights"]["environmental"] == 0.5
    assert metadata["original_weights"]["social"] == 0.3
    assert metadata["original_weights"]["governance"] == 0.2
    
    print(f"ESG Score with custom weights: {score:.2f}")


def test_calculate_esg_score_missing_pillar():
    """Test ESG score calculation when one pillar has no data."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 60.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.0,
        # No governance indicators
    }
    
    score, metadata = calculate_esg_score(SAMPLE_INDICATORS, extracted_values)
    
    # Should still have a score
    assert score is not None
    
    # Governance should be None
    assert metadata["pillar_scores"]["governance"] is None
    
    # Weights should be adjusted (E and S should sum to 1.0)
    adjusted_e = metadata["pillar_weights"]["environmental"]
    adjusted_s = metadata["pillar_weights"]["social"]
    adjusted_g = metadata["pillar_weights"]["governance"]
    
    assert adjusted_g == 0.0
    assert abs((adjusted_e + adjusted_s) - 1.0) < 0.01
    
    # Adjusted weights should be proportional to original
    # Original: E=0.33, S=0.33, G=0.34
    # Adjusted: E=0.5, S=0.5, G=0.0 (since E and S were equal)
    assert abs(adjusted_e - 0.5) < 0.01
    assert abs(adjusted_s - 0.5) < 0.01
    
    print(f"ESG Score with missing pillar: {score:.2f}")
    print(f"Adjusted weights: E={adjusted_e:.2f}, S={adjusted_s:.2f}, G={adjusted_g:.2f}")


def test_calculate_esg_score_only_one_pillar():
    """Test ESG score calculation with only one pillar."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 60.0,
    }
    
    score, metadata = calculate_esg_score(SAMPLE_INDICATORS, extracted_values)
    
    # Should have a score equal to the environmental score
    assert score is not None
    assert score == metadata["pillar_scores"]["environmental"]
    
    # Only environmental weight should be 1.0
    assert metadata["pillar_weights"]["environmental"] == 1.0
    assert metadata["pillar_weights"]["social"] == 0.0
    assert metadata["pillar_weights"]["governance"] == 0.0
    
    print(f"ESG Score with one pillar: {score:.2f}")


def test_calculate_esg_score_no_data():
    """Test ESG score calculation with no data."""
    extracted_values = {}
    
    score, metadata = calculate_esg_score(SAMPLE_INDICATORS, extracted_values)
    
    # Should have no score
    assert score is None
    
    # All pillar scores should be None
    assert metadata["pillar_scores"]["environmental"] is None
    assert metadata["pillar_scores"]["social"] is None
    assert metadata["pillar_scores"]["governance"] is None
    
    print("ESG Score with no data: None (as expected)")


def test_validate_pillar_weights_valid():
    """Test validation of valid pillar weights."""
    valid_weights = {"E": 0.33, "S": 0.33, "G": 0.34}
    
    # Should not raise
    _validate_pillar_weights(valid_weights)
    
    print("✓ Valid weights accepted")


def test_validate_pillar_weights_invalid_sum():
    """Test validation rejects weights that don't sum to 1.0."""
    invalid_weights = {"E": 0.5, "S": 0.3, "G": 0.3}  # Sums to 1.1
    
    with pytest.raises(ValueError, match="must sum to 1.0"):
        _validate_pillar_weights(invalid_weights)
    
    print("✓ Invalid sum rejected")


def test_validate_pillar_weights_missing_key():
    """Test validation rejects weights with missing keys."""
    invalid_weights = {"E": 0.5, "S": 0.5}  # Missing G
    
    with pytest.raises(ValueError, match="must contain exactly keys"):
        _validate_pillar_weights(invalid_weights)
    
    print("✓ Missing key rejected")


def test_validate_pillar_weights_negative():
    """Test validation rejects negative weights."""
    invalid_weights = {"E": 0.5, "S": 0.6, "G": -0.1}
    
    with pytest.raises(ValueError, match="must be non-negative"):
        _validate_pillar_weights(invalid_weights)
    
    print("✓ Negative weight rejected")


def test_calculate_weighted_esg_score():
    """Test weighted ESG score calculation."""
    env_score = 60.0
    soc_score = 70.0
    gov_score = 80.0
    weights = {"E": 0.33, "S": 0.33, "G": 0.34}
    
    overall, adjusted = _calculate_weighted_esg_score(
        env_score, soc_score, gov_score, weights
    )
    
    # Calculate expected score
    expected = (60.0 * 0.33) + (70.0 * 0.33) + (80.0 * 0.34)
    
    assert abs(overall - expected) < 0.01
    assert adjusted == weights  # No adjustment needed
    
    print(f"Weighted score: {overall:.2f} (expected: {expected:.2f})")


def test_pillar_breakdown_in_metadata():
    """Test that pillar breakdown is included in metadata."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 60.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.0,
    }
    
    score, metadata = calculate_esg_score(SAMPLE_INDICATORS, extracted_values)
    
    # Should have pillar breakdown
    assert "pillar_breakdown" in metadata
    assert "E" in metadata["pillar_breakdown"]
    assert "S" in metadata["pillar_breakdown"]
    assert "G" in metadata["pillar_breakdown"]
    
    # Environmental breakdown should have indicators
    env_breakdown = metadata["pillar_breakdown"]["E"]
    assert len(env_breakdown["indicators"]) > 0
    assert env_breakdown["indicators"][0]["code"] == "ENERGY_RENEWABLE_PERCENT"
    
    print("✓ Pillar breakdown included in metadata")


def test_get_esg_score_with_citations():
    """Test ESG score calculation with source citations."""
    extracted_indicators = [
        {
            "indicator_code": "ENERGY_RENEWABLE_PERCENT",
            "numeric_value": 60.0,
            "object_key": "RELIANCE/2024_BRSR.pdf",
            "source_pages": [45, 46],
            "source_chunk_ids": [123, 124],
            "confidence_score": 0.95,
        },
        {
            "indicator_code": "EMPLOYEE_WELLBEING_SPEND_PERCENT",
            "numeric_value": 3.0,
            "object_key": "RELIANCE/2024_BRSR.pdf",
            "source_pages": [78],
            "source_chunk_ids": [234],
            "confidence_score": 0.88,
        },
    ]
    
    score, metadata = get_esg_score_with_citations(
        SAMPLE_INDICATORS,
        extracted_indicators
    )
    
    # Should have a score
    assert score is not None
    
    # Should have citations in breakdown
    env_breakdown = metadata["pillar_breakdown"]["E"]
    assert len(env_breakdown["indicators"]) > 0
    
    # First indicator should have citations
    first_indicator = env_breakdown["indicators"][0]
    assert "citations" in first_indicator
    assert first_indicator["citations"]["object_key"] == "RELIANCE/2024_BRSR.pdf"
    assert first_indicator["citations"]["source_pages"] == [45, 46]
    assert first_indicator["citations"]["confidence_score"] == 0.95
    
    print(f"ESG Score with citations: {score:.2f}")
    print(f"Citations: {first_indicator['citations']}")


def test_calculation_method_description():
    """Test that calculation method description is generated."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 60.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.0,
    }
    
    score, metadata = calculate_esg_score(SAMPLE_INDICATORS, extracted_values)
    
    method = metadata["calculation_method"]
    
    # Should mention key concepts
    assert "weighted average" in method.lower()
    assert "pillar" in method.lower()
    assert "brsr core" in method.lower()
    
    # Should mention which pillars were used
    assert "environmental" in method.lower()
    assert "social" in method.lower()
    
    print(f"Calculation method: {method}")


def test_total_indicators_in_metadata():
    """Test that total indicators count is in metadata."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 60.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.0,
        "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
    }
    
    score, metadata = calculate_esg_score(SAMPLE_INDICATORS, extracted_values)
    
    assert metadata["total_indicators_extracted"] == 3
    
    print(f"Total indicators: {metadata['total_indicators_extracted']}")


if __name__ == "__main__":
    # Run tests
    print("Running ESG calculator tests...\n")
    
    print("Test 1: All pillars")
    test_calculate_esg_score_all_pillars()
    print()
    
    print("Test 2: Custom weights")
    test_calculate_esg_score_custom_weights()
    print()
    
    print("Test 3: Missing pillar")
    test_calculate_esg_score_missing_pillar()
    print()
    
    print("Test 4: Only one pillar")
    test_calculate_esg_score_only_one_pillar()
    print()
    
    print("Test 5: No data")
    test_calculate_esg_score_no_data()
    print()
    
    print("Test 6: Valid weights")
    test_validate_pillar_weights_valid()
    print()
    
    print("Test 7: Invalid sum")
    test_validate_pillar_weights_invalid_sum()
    print()
    
    print("Test 8: Missing key")
    test_validate_pillar_weights_missing_key()
    print()
    
    print("Test 9: Negative weight")
    test_validate_pillar_weights_negative()
    print()
    
    print("Test 10: Weighted score")
    test_calculate_weighted_esg_score()
    print()
    
    print("Test 11: Pillar breakdown")
    test_pillar_breakdown_in_metadata()
    print()
    
    print("Test 12: Citations")
    test_get_esg_score_with_citations()
    print()
    
    print("Test 13: Calculation method")
    test_calculation_method_description()
    print()
    
    print("Test 14: Total indicators")
    test_total_indicators_in_metadata()
    print()
    
    print("All tests passed! ✓")
