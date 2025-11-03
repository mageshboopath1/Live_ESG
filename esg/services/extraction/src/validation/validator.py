"""
Validation functions for extracted BRSR Core indicators.

This module provides comprehensive validation for extracted indicator values:
1. Confidence score validation (0.0-1.0 range)
2. Required field validation (extracted_value, indicator_id, etc.)
3. Data type validation (numeric_value matches expected type)
4. Numeric range validation based on BRSR indicator schema
5. Unit consistency validation

The validator flags indicators with validation errors but stores raw values
for transparency and manual review. This ensures data is never lost even if
validation fails.

Requirements: 13.1, 13.2, 13.3, 13.4
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..models.brsr_models import (
    BRSRIndicatorDefinition,
    ExtractedIndicator,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Result of indicator validation.
    
    Attributes:
        is_valid: Whether the indicator passed all validation checks
        validation_status: Status string ('valid', 'invalid', 'pending')
        errors: List of validation error messages
        warnings: List of validation warning messages
    """
    is_valid: bool
    validation_status: str
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        """Ensure validation_status matches is_valid."""
        if self.is_valid and self.validation_status != "valid":
            self.validation_status = "valid"
        elif not self.is_valid and self.validation_status == "valid":
            self.validation_status = "invalid"


# Expected ranges for numeric indicators
# Format: indicator_code -> (min_value, max_value, allow_zero)
# None means no limit, True/False for allow_zero
NUMERIC_RANGES: Dict[str, Tuple[Optional[float], Optional[float], bool]] = {
    # GHG emissions (MT CO2e) - typically 0 to millions
    "GHG_SCOPE1_TOTAL": (0, None, True),
    "GHG_SCOPE1_CO2": (0, None, True),
    "GHG_SCOPE2_TOTAL": (0, None, True),
    "GHG_INTENSITY_REVENUE": (0, None, True),
    "GHG_INTENSITY_OUTPUT": (0, None, True),
    
    # Water (KL) - typically 0 to millions
    "WATER_CONSUMPTION_TOTAL": (0, None, True),
    "WATER_INTENSITY_REVENUE": (0, None, True),
    "WATER_INTENSITY_OUTPUT": (0, None, True),
    "WATER_DISCHARGE_UNTREATED": (0, None, True),
    "WATER_DISCHARGE_PRIMARY": (0, None, True),
    "WATER_DISCHARGE_SECONDARY": (0, None, True),
    "WATER_DISCHARGE_TERTIARY": (0, None, True),
    
    # Energy (Joules) - typically 0 to very large numbers
    "ENERGY_CONSUMPTION_TOTAL": (0, None, True),
    "ENERGY_RENEWABLE_PERCENT": (0, 100, True),  # Percentage
    "ENERGY_INTENSITY_REVENUE": (0, None, True),
    "ENERGY_INTENSITY_OUTPUT": (0, None, True),
    
    # Waste (MT) - typically 0 to thousands
    "WASTE_PLASTIC": (0, None, True),
    "WASTE_EWASTE": (0, None, True),
    "WASTE_BIOMEDICAL": (0, None, True),
    "WASTE_CONSTRUCTION": (0, None, True),
    "WASTE_BATTERY": (0, None, True),
    "WASTE_RADIOACTIVE": (0, None, True),
    "WASTE_HAZARDOUS_OTHER": (0, None, True),
    "WASTE_NON_HAZARDOUS": (0, None, True),
    "WASTE_TOTAL": (0, None, True),
    "WASTE_INTENSITY_REVENUE": (0, None, True),
    "WASTE_INTENSITY_OUTPUT": (0, None, True),
    "WASTE_RECYCLED_PLASTIC": (0, None, True),
    "WASTE_RECYCLED_EWASTE": (0, None, True),
    "WASTE_DISPOSED_LANDFILL": (0, None, True),
    "WASTE_DISPOSED_INCINERATION": (0, None, True),
    
    # Employee wellbeing - percentages and rates
    "EMPLOYEE_WELLBEING_SPEND_PERCENT": (0, 100, True),
    "SAFETY_LTIFR": (0, None, True),  # Per million hours
    "SAFETY_FATALITIES": (0, None, True),  # Count
    "SAFETY_PERMANENT_DISABILITIES": (0, None, True),  # Count
    
    # Gender diversity - percentages and counts
    "GENDER_WAGE_PERCENT": (0, 100, True),
    "GENDER_POSH_COMPLAINTS_TOTAL": (0, None, True),
    "GENDER_POSH_COMPLAINTS_PERCENT": (0, 100, True),
    "GENDER_POSH_UPHELD": (0, None, True),
    
    # Inclusive development - percentages
    "INCLUSIVE_MSME_SOURCING_PERCENT": (0, 100, True),
    "INCLUSIVE_INDIA_SOURCING_PERCENT": (0, 100, True),
    "INCLUSIVE_SMALLER_TOWNS_WAGE_PERCENT": (0, 100, True),
    
    # Customer and supplier fairness
    "CUSTOMER_DATA_BREACH_PERCENT": (0, 100, True),
    "SUPPLIER_PAYMENT_DAYS": (0, None, False),  # Days should be > 0
    
    # Business openness - percentages and counts
    "OPENNESS_TRADING_HOUSE_PURCHASES_PERCENT": (0, 100, True),
    "OPENNESS_TRADING_HOUSE_COUNT": (0, None, True),
    "OPENNESS_TOP10_TRADING_HOUSE_PERCENT": (0, 100, True),
    "OPENNESS_DEALER_SALES_PERCENT": (0, 100, True),
    "OPENNESS_DEALER_COUNT": (0, None, True),
    "OPENNESS_TOP10_DEALER_PERCENT": (0, 100, True),
    "OPENNESS_RPT_PURCHASES_PERCENT": (0, 100, True),
    "OPENNESS_RPT_SALES_PERCENT": (0, 100, True),
    "OPENNESS_RPT_LOANS_PERCENT": (0, 100, True),
    "OPENNESS_RPT_INVESTMENTS_PERCENT": (0, 100, True),
}


def validate_indicator(
    extracted_indicator: ExtractedIndicator,
    indicator_definition: BRSRIndicatorDefinition,
) -> ValidationResult:
    """
    Validate an extracted indicator against BRSR schema and business rules.
    
    This function performs comprehensive validation including:
    1. Confidence score validation (must be 0.0-1.0)
    2. Required field validation (extracted_value, indicator_id, etc.)
    3. Data type validation (numeric_value matches expected type)
    4. Numeric range validation based on indicator type
    5. Unit consistency validation
    
    The function flags indicators with validation errors but does NOT modify
    the extracted values. This ensures transparency and allows manual review
    of flagged indicators.
    
    Args:
        extracted_indicator: The extracted indicator to validate
        indicator_definition: The BRSR indicator definition with schema
        
    Returns:
        ValidationResult: Object containing validation status, errors, and warnings
        
    Requirements: 13.1, 13.2, 13.3, 13.4
    
    Example:
        >>> from src.models.brsr_models import ExtractedIndicator, BRSRIndicatorDefinition
        >>> 
        >>> indicator_def = BRSRIndicatorDefinition(
        ...     indicator_code="GHG_SCOPE1_TOTAL",
        ...     attribute_number=1,
        ...     parameter_name="Total Scope 1 emissions",
        ...     measurement_unit="MT CO2e",
        ...     description="Direct GHG emissions",
        ...     pillar="E",
        ...     weight=1.0,
        ...     data_assurance_approach="Fossil fuel consumption",
        ...     brsr_reference="Principle 6, Question 7"
        ... )
        >>> 
        >>> extracted = ExtractedIndicator(
        ...     object_key="RELIANCE/2024_BRSR.pdf",
        ...     company_id=1,
        ...     report_year=2024,
        ...     indicator_id=1,
        ...     extracted_value="1250 MT CO2e",
        ...     numeric_value=1250.0,
        ...     confidence_score=0.95,
        ...     validation_status="pending",
        ...     source_pages=[45],
        ...     source_chunk_ids=[123]
        ... )
        >>> 
        >>> result = validate_indicator(extracted, indicator_def)
        >>> print(result.is_valid)  # True
        >>> print(result.validation_status)  # "valid"
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    logger.debug(
        f"Validating indicator {indicator_definition.indicator_code} "
        f"with value '{extracted_indicator.extracted_value}'"
    )
    
    # 1. Validate confidence score (CRITICAL - Requirements 13.1, 13.4)
    if not _validate_confidence_score(extracted_indicator, errors):
        logger.warning(
            f"Confidence score validation failed for {indicator_definition.indicator_code}"
        )
    
    # 2. Validate required fields (Requirements 13.3)
    if not _validate_required_fields(extracted_indicator, errors):
        logger.warning(
            f"Required field validation failed for {indicator_definition.indicator_code}"
        )
    
    # 3. Validate data types (Requirements 13.3)
    if not _validate_data_types(extracted_indicator, indicator_definition, errors, warnings):
        logger.warning(
            f"Data type validation failed for {indicator_definition.indicator_code}"
        )
    
    # 4. Validate numeric ranges (Requirements 13.2)
    if extracted_indicator.numeric_value is not None:
        if not _validate_numeric_range(
            extracted_indicator,
            indicator_definition,
            errors,
            warnings
        ):
            logger.warning(
                f"Numeric range validation failed for {indicator_definition.indicator_code}"
            )
    
    # 5. Validate unit consistency (Requirements 13.2)
    if not _validate_unit_consistency(
        extracted_indicator,
        indicator_definition,
        warnings
    ):
        logger.debug(
            f"Unit consistency check produced warnings for {indicator_definition.indicator_code}"
        )
    
    # Determine overall validation status
    is_valid = len(errors) == 0
    validation_status = "valid" if is_valid else "invalid"
    
    if is_valid and len(warnings) > 0:
        logger.info(
            f"Indicator {indicator_definition.indicator_code} is valid with {len(warnings)} warnings"
        )
    elif not is_valid:
        logger.warning(
            f"Indicator {indicator_definition.indicator_code} is invalid: {errors}"
        )
    else:
        logger.info(
            f"Indicator {indicator_definition.indicator_code} is valid"
        )
    
    return ValidationResult(
        is_valid=is_valid,
        validation_status=validation_status,
        errors=errors,
        warnings=warnings,
    )


def _validate_confidence_score(
    extracted_indicator: ExtractedIndicator,
    errors: List[str],
) -> bool:
    """
    Validate that confidence score is between 0.0 and 1.0.
    
    Requirements: 13.1, 13.4
    """
    confidence = extracted_indicator.confidence_score
    
    if confidence < 0.0 or confidence > 1.0:
        errors.append(
            f"Confidence score {confidence} is outside valid range [0.0, 1.0]"
        )
        return False
    
    return True


def _validate_required_fields(
    extracted_indicator: ExtractedIndicator,
    errors: List[str],
) -> bool:
    """
    Validate that all required fields are present and non-empty.
    
    Requirements: 13.3
    """
    is_valid = True
    
    # Check extracted_value (required)
    if not extracted_indicator.extracted_value or not extracted_indicator.extracted_value.strip():
        errors.append("extracted_value is required and cannot be empty")
        is_valid = False
    
    # Check indicator_id (required)
    if extracted_indicator.indicator_id is None or extracted_indicator.indicator_id <= 0:
        errors.append("indicator_id is required and must be positive")
        is_valid = False
    
    # Check company_id (required)
    if extracted_indicator.company_id is None or extracted_indicator.company_id <= 0:
        errors.append("company_id is required and must be positive")
        is_valid = False
    
    # Check report_year (required)
    if extracted_indicator.report_year is None or extracted_indicator.report_year < 2000:
        errors.append("report_year is required and must be >= 2000")
        is_valid = False
    
    # Check object_key (required)
    if not extracted_indicator.object_key or not extracted_indicator.object_key.strip():
        errors.append("object_key is required and cannot be empty")
        is_valid = False
    
    return is_valid


def _validate_data_types(
    extracted_indicator: ExtractedIndicator,
    indicator_definition: BRSRIndicatorDefinition,
    errors: List[str],
    warnings: List[str],
) -> bool:
    """
    Validate that data types match expected types based on measurement unit.
    
    Requirements: 13.3
    """
    is_valid = True
    
    # Determine if indicator should have numeric value based on unit
    unit = indicator_definition.measurement_unit
    should_be_numeric = unit is not None and unit.lower() not in ["n/a", "na", "text", "qualitative"]
    
    # Check if numeric_value is provided when expected
    if should_be_numeric and extracted_indicator.numeric_value is None:
        # Try to extract numeric value from extracted_value
        numeric_match = _extract_numeric_from_text(extracted_indicator.extracted_value)
        if numeric_match is None:
            warnings.append(
                f"Expected numeric value for unit '{unit}' but numeric_value is None. "
                f"Could not extract number from '{extracted_indicator.extracted_value}'"
            )
        else:
            warnings.append(
                f"numeric_value is None but found numeric value {numeric_match} in text. "
                f"Consider updating numeric_value field."
            )
    
    # Check if numeric_value is provided when not expected
    if not should_be_numeric and extracted_indicator.numeric_value is not None:
        warnings.append(
            f"numeric_value provided for qualitative indicator (unit: '{unit}'). "
            f"This may be acceptable if the indicator has quantitative aspects."
        )
    
    # Validate numeric_value type if present
    if extracted_indicator.numeric_value is not None:
        if not isinstance(extracted_indicator.numeric_value, (int, float)):
            errors.append(
                f"numeric_value must be int or float, got {type(extracted_indicator.numeric_value)}"
            )
            is_valid = False
    
    return is_valid


def _validate_numeric_range(
    extracted_indicator: ExtractedIndicator,
    indicator_definition: BRSRIndicatorDefinition,
    errors: List[str],
    warnings: List[str],
) -> bool:
    """
    Validate that numeric values fall within expected ranges for the indicator type.
    
    Requirements: 13.2
    """
    is_valid = True
    indicator_code = indicator_definition.indicator_code
    numeric_value = extracted_indicator.numeric_value
    
    # Get expected range for this indicator
    if indicator_code not in NUMERIC_RANGES:
        # No specific range defined, skip validation
        logger.debug(f"No range validation defined for {indicator_code}")
        return True
    
    min_val, max_val, allow_zero = NUMERIC_RANGES[indicator_code]
    
    # Check minimum value
    if min_val is not None and numeric_value < min_val:
        errors.append(
            f"Value {numeric_value} is below minimum {min_val} for {indicator_code}"
        )
        is_valid = False
    
    # Check maximum value
    if max_val is not None and numeric_value > max_val:
        errors.append(
            f"Value {numeric_value} exceeds maximum {max_val} for {indicator_code}"
        )
        is_valid = False
    
    # Check zero value
    if not allow_zero and numeric_value == 0:
        warnings.append(
            f"Value is zero for {indicator_code}, which typically should be > 0. "
            f"Verify this is correct."
        )
    
    # Additional sanity checks for specific indicator types
    if indicator_code.endswith("_PERCENT") and numeric_value > 100:
        errors.append(
            f"Percentage value {numeric_value} exceeds 100% for {indicator_code}"
        )
        is_valid = False
    
    # Check for unreasonably large values (potential extraction errors)
    if numeric_value > 1e15:  # 1 quadrillion
        warnings.append(
            f"Value {numeric_value} is extremely large for {indicator_code}. "
            f"Verify this is not an extraction error."
        )
    
    return is_valid


def _validate_unit_consistency(
    extracted_indicator: ExtractedIndicator,
    indicator_definition: BRSRIndicatorDefinition,
    warnings: List[str],
) -> bool:
    """
    Validate that the extracted value mentions the expected unit.
    
    This is a soft validation that produces warnings, not errors.
    
    Requirements: 13.2
    """
    expected_unit = indicator_definition.measurement_unit
    extracted_value = extracted_indicator.extracted_value
    
    if not expected_unit or expected_unit.lower() in ["n/a", "na"]:
        # No unit expected, skip validation
        return True
    
    # Check if unit appears in extracted value
    # Normalize for comparison
    extracted_lower = extracted_value.lower()
    unit_lower = expected_unit.lower()
    
    # Handle common unit variations
    unit_variations = _get_unit_variations(unit_lower)
    
    unit_found = any(var in extracted_lower for var in unit_variations)
    
    if not unit_found:
        warnings.append(
            f"Expected unit '{expected_unit}' not found in extracted value '{extracted_value}'. "
            f"Verify unit consistency."
        )
        return False
    
    return True


def _extract_numeric_from_text(text: str) -> Optional[float]:
    """
    Extract numeric value from text string.
    
    Handles formats like:
    - "1250 MT CO2e" -> 1250.0
    - "45%" -> 45.0
    - "1,250.50" -> 1250.5
    - "Yes" -> None
    """
    # Remove commas from numbers
    text = text.replace(",", "")
    
    # Try to find a number (integer or decimal)
    match = re.search(r"-?\d+\.?\d*", text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    
    return None


def _get_unit_variations(unit: str) -> List[str]:
    """
    Get common variations of a unit for matching.
    
    Examples:
    - "MT CO2e" -> ["mt co2e", "mt co2", "mtco2e", "metric ton"]
    - "%" -> ["%", "percent", "percentage"]
    - "KL" -> ["kl", "kiloliter", "kilolitre"]
    """
    variations = [unit]
    
    # Percentage variations
    if "%" in unit or "percent" in unit.lower():
        variations.extend(["%", "percent", "percentage", "pct"])
    
    # Weight variations
    if "mt" in unit.lower():
        variations.extend(["mt", "metric ton", "metric tons", "tonne", "tonnes"])
    
    # Volume variations
    if "kl" in unit.lower():
        variations.extend(["kl", "kiloliter", "kilolitre", "kiloliters", "kilolitres"])
    
    # Energy variations
    if "joule" in unit.lower():
        variations.extend(["joule", "joules", "j", "mwh", "kwh", "gwh"])
    
    # CO2 variations
    if "co2" in unit.lower():
        variations.extend(["co2", "co2e", "co2eq", "carbon dioxide"])
    
    # Count variations
    if "count" in unit.lower():
        variations.extend(["count", "number", "total", "#"])
    
    # Days variations
    if "day" in unit.lower():
        variations.extend(["day", "days", "d"])
    
    # Rate variations
    if "per million" in unit.lower():
        variations.extend(["per million", "per 1000000", "/million", "/1000000"])
    
    return variations
