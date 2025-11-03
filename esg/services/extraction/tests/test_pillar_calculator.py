"""
Unit tests for pillar score calculation.

This test file verifies the pillar score calculation logic including:
- Basic score calculation with weighted averages
- Handling of missing indicators
- Different indicator types (percentage, intensity, count)
- Edge cases

Requirements: 15.1, 15.2
"""

import pytest
from src.models.brsr_models import BRSRIndicatorDefinition, Pillar
from src.scoring.pillar_calculator import (
    calculate_pillar_scores,
    get_pillar_breakdown,
    _normalize_indicator_value,
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
    BRSRIndicatorDefinition(
        indicator_code="WATER_INTENSITY_REVENUE",
        attribute_number=2,
        parameter_name="Water consumption intensity",
        measurement_unit="KL per INR",
        description="Water per revenue",
        pillar=Pillar.ENVIRONMENTAL,
        weight=0.8,
        data_assurance_approach="Water meters",
        brsr_reference="Principle 6, Question 3",
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
        indicator_code="SAFETY_FATALITIES",
        attribute_number=5,
        parameter_name="Number of fatalities",
        measurement_unit="count",
        description="Total fatalities",
        pillar=Pillar.SOCIAL,
        weight=1.0,
        data_assurance_approach="Incident reports",
        brsr_reference="Principle 3, Question 11",
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
    BRSRIndicatorDefinition(
        indicator_code="SUPPLIER_PAYMENT_DAYS",
        attribute_number=8,
        parameter_name="Days of accounts payable",
        measurement_unit="days",
        description="Average days to pay suppliers",
        pillar=Pillar.GOVERNANCE,
        weight=1.0,
        data_assurance_approach="Financial statements",
        brsr_reference="Principle 1, Question 8",
    ),
]


def test_calculate_pillar_scores_all_pillars():
    """Test calculation with indicators from all three pillars."""
    extracted_values = {
        "GHG_SCOPE1_TOTAL": 1250.0,
        "ENERGY_RENEWABLE_PERCENT": 45.0,
        "WATER_INTENSITY_REVENUE": 0.5,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 2.5,
        "SAFETY_FATALITIES": 0.0,
        "GENDER_WAGE_PERCENT": 35.0,
        "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
        "SUPPLIER_PAYMENT_DAYS": 60.0,
    }
    
    env_score, soc_score, gov_score = calculate_pillar_scores(
        SAMPLE_INDICATORS,
        extracted_values
    )
    
    # All pillars should have scores
    assert env_score is not None
    assert soc_score is not None
    assert gov_score is not None
    
    # Scores should be in valid range
    assert 0 <= env_score <= 100
    assert 0 <= soc_score <= 100
    assert 0 <= gov_score <= 100
    
    print(f"Environmental: {env_score:.2f}")
    print(f"Social: {soc_score:.2f}")
    print(f"Governance: {gov_score:.2f}")


def test_calculate_pillar_scores_missing_pillar():
    """Test calculation when one pillar has no data."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 45.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 2.5,
        # No governance indicators
    }
    
    env_score, soc_score, gov_score = calculate_pillar_scores(
        SAMPLE_INDICATORS,
        extracted_values
    )
    
    # Environmental and Social should have scores
    assert env_score is not None
    assert soc_score is not None
    
    # Governance should be None (no data)
    assert gov_score is None
    
    print(f"Environmental: {env_score:.2f}")
    print(f"Social: {soc_score:.2f}")
    print(f"Governance: {gov_score}")


def test_calculate_pillar_scores_partial_indicators():
    """Test calculation with only some indicators per pillar."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 45.0,  # Only 1 of 3 environmental
        "GENDER_WAGE_PERCENT": 35.0,  # Only 1 of 3 social
    }
    
    env_score, soc_score, gov_score = calculate_pillar_scores(
        SAMPLE_INDICATORS,
        extracted_values
    )
    
    # Should calculate scores with available data
    assert env_score is not None
    assert soc_score is not None
    assert gov_score is None
    
    # Environmental score should be close to 45 (percentage indicator)
    assert 40 <= env_score <= 50
    
    # Social score should be close to 35 (percentage indicator)
    assert 30 <= soc_score <= 40


def test_normalize_percentage_indicator():
    """Test normalization of percentage indicators."""
    # Percentage indicators should use value directly
    normalized = _normalize_indicator_value(45.0, "ENERGY_RENEWABLE_PERCENT", "%")
    assert normalized == 45.0
    
    # Should cap at 100
    normalized = _normalize_indicator_value(150.0, "SOME_PERCENT", "%")
    assert normalized == 100.0


def test_normalize_intensity_indicator():
    """Test normalization of intensity indicators."""
    # Intensity indicators use inverse scaling (lower is better)
    normalized = _normalize_indicator_value(0.5, "WATER_INTENSITY_REVENUE", "KL per INR")
    assert 0 <= normalized <= 100
    
    # Lower intensity should give higher score
    normalized_low = _normalize_indicator_value(0.1, "WATER_INTENSITY_REVENUE", "KL per INR")
    normalized_high = _normalize_indicator_value(1.0, "WATER_INTENSITY_REVENUE", "KL per INR")
    assert normalized_low > normalized_high


def test_normalize_count_indicator():
    """Test normalization of count indicators."""
    # Count indicators use inverse scaling (lower is better)
    normalized_zero = _normalize_indicator_value(0.0, "SAFETY_FATALITIES", "count")
    normalized_ten = _normalize_indicator_value(10.0, "SAFETY_FATALITIES", "count")
    
    # Zero fatalities should score 100
    assert normalized_zero == 100.0
    
    # More fatalities should score lower
    assert normalized_ten < normalized_zero


def test_normalize_days_indicator():
    """Test normalization of days indicators."""
    # Days indicators use inverse scaling (lower is better for payment days)
    normalized_30 = _normalize_indicator_value(30.0, "SUPPLIER_PAYMENT_DAYS", "days")
    normalized_90 = _normalize_indicator_value(90.0, "SUPPLIER_PAYMENT_DAYS", "days")
    
    # Shorter payment period should score higher
    assert normalized_30 > normalized_90


def test_get_pillar_breakdown():
    """Test detailed breakdown generation."""
    extracted_values = {
        "ENERGY_RENEWABLE_PERCENT": 45.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 2.5,
        "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
    }
    
    breakdown = get_pillar_breakdown(SAMPLE_INDICATORS, extracted_values)
    
    # Should have all three pillars
    assert "E" in breakdown
    assert "S" in breakdown
    assert "G" in breakdown
    
    # Environmental should have score and indicators
    assert breakdown["E"]["score"] is not None
    assert len(breakdown["E"]["indicators"]) == 1
    assert breakdown["E"]["indicators"][0]["code"] == "ENERGY_RENEWABLE_PERCENT"
    
    # Social should have score
    assert breakdown["S"]["score"] is not None
    
    # Governance should have score
    assert breakdown["G"]["score"] is not None
    
    print(f"Breakdown: {breakdown}")


def test_weighted_average_calculation():
    """Test that weighted average is calculated correctly."""
    # Create indicators with different weights
    indicators = [
        BRSRIndicatorDefinition(
            indicator_code="IND1",
            attribute_number=1,
            parameter_name="Indicator 1",
            measurement_unit="%",
            description="Test",
            pillar=Pillar.ENVIRONMENTAL,
            weight=0.5,
            data_assurance_approach="Test",
            brsr_reference="Test",
        ),
        BRSRIndicatorDefinition(
            indicator_code="IND2",
            attribute_number=1,
            parameter_name="Indicator 2",
            measurement_unit="%",
            description="Test",
            pillar=Pillar.ENVIRONMENTAL,
            weight=1.0,
            data_assurance_approach="Test",
            brsr_reference="Test",
        ),
    ]
    
    extracted_values = {
        "IND1": 40.0,  # weight 0.5
        "IND2": 80.0,  # weight 1.0
    }
    
    env_score, _, _ = calculate_pillar_scores(indicators, extracted_values)
    
    # Expected: (40*0.5 + 80*1.0) / (0.5 + 1.0) = 100/1.5 = 66.67
    expected = (40.0 * 0.5 + 80.0 * 1.0) / (0.5 + 1.0)
    assert abs(env_score - expected) < 0.01


def test_empty_extracted_values():
    """Test with no extracted values."""
    extracted_values = {}
    
    env_score, soc_score, gov_score = calculate_pillar_scores(
        SAMPLE_INDICATORS,
        extracted_values
    )
    
    # All scores should be None
    assert env_score is None
    assert soc_score is None
    assert gov_score is None


if __name__ == "__main__":
    # Run tests
    print("Running pillar calculator tests...\n")
    
    print("Test 1: All pillars")
    test_calculate_pillar_scores_all_pillars()
    print()
    
    print("Test 2: Missing pillar")
    test_calculate_pillar_scores_missing_pillar()
    print()
    
    print("Test 3: Partial indicators")
    test_calculate_pillar_scores_partial_indicators()
    print()
    
    print("Test 4: Percentage normalization")
    test_normalize_percentage_indicator()
    print("✓ Percentage normalization works")
    print()
    
    print("Test 5: Intensity normalization")
    test_normalize_intensity_indicator()
    print("✓ Intensity normalization works")
    print()
    
    print("Test 6: Count normalization")
    test_normalize_count_indicator()
    print("✓ Count normalization works")
    print()
    
    print("Test 7: Days normalization")
    test_normalize_days_indicator()
    print("✓ Days normalization works")
    print()
    
    print("Test 8: Pillar breakdown")
    test_get_pillar_breakdown()
    print()
    
    print("Test 9: Weighted average")
    test_weighted_average_calculation()
    print("✓ Weighted average calculation correct")
    print()
    
    print("Test 10: Empty values")
    test_empty_extracted_values()
    print("✓ Empty values handled correctly")
    print()
    
    print("All tests passed! ✓")
