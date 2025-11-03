"""
Validation module for extracted BRSR indicators.

This module provides validation functions for extracted indicator values:
- validate_indicator(): Validates extracted values against BRSR schema
- Numeric range validation based on indicator type
- Required field validation
- Data type validation
- Confidence score validation

Requirements: 13.1, 13.2, 13.3, 13.4
"""

from .validator import validate_indicator, ValidationResult

__all__ = ["validate_indicator", "ValidationResult"]
