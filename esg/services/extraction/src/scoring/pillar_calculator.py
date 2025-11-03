"""
Pillar score calculation for ESG Intelligence Platform.

This module calculates Environmental (E), Social (S), and Governance (G) pillar scores
from extracted BRSR Core indicators using weighted averages. It handles missing indicators
gracefully by using only available data.

Requirements: 15.1, 15.2
"""

import logging
from typing import Dict, List, Optional, Tuple

from ..models.brsr_models import BRSRIndicatorDefinition, Pillar

logger = logging.getLogger(__name__)


def calculate_pillar_scores(
    indicator_definitions: List[BRSRIndicatorDefinition],
    extracted_values: Dict[str, float],
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Calculate pillar scores for Environmental, Social, and Governance dimensions.
    
    This function aggregates extracted indicator values using weighted averages based on
    indicator importance (weight). It maps BRSR attributes to E, S, G pillars and handles
    missing indicators gracefully by using only available data.
    
    Pillar Mapping:
    - Environmental (E): Attributes 1-4 (GHG, Water, Energy, Waste)
    - Social (S): Attributes 5-7 (Employee Wellbeing, Gender Diversity, Inclusive Development)
    - Governance (G): Attributes 8-9 (Customer/Supplier Fairness, Business Openness)
    
    Score Calculation:
    - For each pillar, calculate weighted average of normalized indicator values
    - Normalization: Convert all values to 0-100 scale based on indicator type
    - Weighted Average: Sum(indicator_value * weight) / Sum(weights)
    - Missing indicators: Use only available indicators, adjust weight sum accordingly
    
    Args:
        indicator_definitions: List of BRSR indicator definitions with pillar and weight info
        extracted_values: Dictionary mapping indicator_code to numeric_value
                         Example: {"GHG_SCOPE1_TOTAL": 1250.0, "WATER_CONSUMPTION_TOTAL": 50000.0}
    
    Returns:
        Tuple[Optional[float], Optional[float], Optional[float]]: 
            (environmental_score, social_score, governance_score)
            Each score is in range 0-100, or None if no indicators available for that pillar
    
    Example:
        >>> definitions = load_brsr_indicators()
        >>> values = {"GHG_SCOPE1_TOTAL": 1250.0, "ENERGY_RENEWABLE_PERCENT": 45.0}
        >>> env_score, soc_score, gov_score = calculate_pillar_scores(definitions, values)
        >>> print(f"Environmental: {env_score}, Social: {soc_score}, Governance: {gov_score}")
        Environmental: 62.5, Social: None, Governance: None
    
    Requirements: 15.1, 15.2
    """
    logger.info(
        f"Calculating pillar scores from {len(extracted_values)} extracted indicators"
    )
    
    # Group indicators by pillar
    pillar_indicators: Dict[Pillar, List[BRSRIndicatorDefinition]] = {
        Pillar.ENVIRONMENTAL: [],
        Pillar.SOCIAL: [],
        Pillar.GOVERNANCE: [],
    }
    
    for indicator in indicator_definitions:
        pillar_indicators[indicator.pillar].append(indicator)
    
    logger.debug(
        f"Indicator distribution - E: {len(pillar_indicators[Pillar.ENVIRONMENTAL])}, "
        f"S: {len(pillar_indicators[Pillar.SOCIAL])}, "
        f"G: {len(pillar_indicators[Pillar.GOVERNANCE])}"
    )
    
    # Calculate score for each pillar
    environmental_score = _calculate_single_pillar_score(
        pillar_indicators[Pillar.ENVIRONMENTAL],
        extracted_values,
        Pillar.ENVIRONMENTAL
    )
    
    social_score = _calculate_single_pillar_score(
        pillar_indicators[Pillar.SOCIAL],
        extracted_values,
        Pillar.SOCIAL
    )
    
    governance_score = _calculate_single_pillar_score(
        pillar_indicators[Pillar.GOVERNANCE],
        extracted_values,
        Pillar.GOVERNANCE
    )
    
    logger.info(
        f"Pillar scores calculated - E: {environmental_score}, "
        f"S: {social_score}, G: {governance_score}"
    )
    
    return environmental_score, social_score, governance_score


def _calculate_single_pillar_score(
    indicators: List[BRSRIndicatorDefinition],
    extracted_values: Dict[str, float],
    pillar: Pillar,
) -> Optional[float]:
    """
    Calculate score for a single pillar using weighted average.
    
    This internal function:
    1. Filters indicators that have extracted values
    2. Normalizes each indicator value to 0-100 scale
    3. Calculates weighted average: Sum(normalized_value * weight) / Sum(weights)
    4. Returns None if no indicators are available
    
    Args:
        indicators: List of indicator definitions for this pillar
        extracted_values: Dictionary of extracted numeric values
        pillar: Pillar enum (E, S, or G) for logging
    
    Returns:
        Optional[float]: Pillar score (0-100) or None if no data available
    """
    # Filter indicators that have extracted values
    available_indicators = [
        ind for ind in indicators
        if ind.indicator_code in extracted_values
    ]
    
    if not available_indicators:
        logger.warning(
            f"No extracted values available for {pillar.value} pillar "
            f"({len(indicators)} indicators defined)"
        )
        return None
    
    logger.debug(
        f"Calculating {pillar.value} pillar score from "
        f"{len(available_indicators)}/{len(indicators)} available indicators"
    )
    
    # Calculate weighted average
    weighted_sum = 0.0
    total_weight = 0.0
    
    for indicator in available_indicators:
        value = extracted_values[indicator.indicator_code]
        
        # Normalize value to 0-100 scale
        normalized_value = _normalize_indicator_value(
            value,
            indicator.indicator_code,
            indicator.measurement_unit
        )
        
        # Apply weight
        weighted_sum += normalized_value * indicator.weight
        total_weight += indicator.weight
        
        logger.debug(
            f"  {indicator.indicator_code}: value={value}, "
            f"normalized={normalized_value:.2f}, weight={indicator.weight}"
        )
    
    # Calculate weighted average
    if total_weight == 0:
        logger.warning(
            f"Total weight is zero for {pillar.value} pillar, cannot calculate score"
        )
        return None
    
    pillar_score = weighted_sum / total_weight
    
    logger.debug(
        f"{pillar.value} pillar: weighted_sum={weighted_sum:.2f}, "
        f"total_weight={total_weight:.2f}, score={pillar_score:.2f}"
    )
    
    return pillar_score


def _normalize_indicator_value(
    value: float,
    indicator_code: str,
    measurement_unit: Optional[str],
) -> float:
    """
    Normalize indicator value to 0-100 scale.
    
    Normalization strategy depends on indicator type:
    - Percentage indicators (unit='%'): Use value directly (already 0-100)
    - Intensity indicators (per unit/revenue): Use inverse scaling (lower is better)
    - Absolute indicators: Use logarithmic scaling for large ranges
    - Count indicators: Use linear scaling with reasonable max values
    
    For this initial implementation, we use a simplified approach:
    - Percentage indicators: Use value directly (capped at 100)
    - Other indicators: Use a placeholder normalization (50.0)
    
    Future enhancement: Implement industry-specific normalization with benchmarks
    
    Args:
        value: Raw extracted numeric value
        indicator_code: Indicator code for context
        measurement_unit: Unit of measurement (e.g., '%', 'MT CO2e')
    
    Returns:
        float: Normalized value in range 0-100
    """
    # Handle percentage indicators
    if measurement_unit == '%':
        # For percentage indicators, use value directly (already 0-100 scale)
        # Cap at 100 to handle edge cases
        normalized = min(value, 100.0)
        logger.debug(f"Normalized {indicator_code} (%) from {value} to {normalized}")
        return normalized
    
    # Handle intensity indicators (lower is better)
    if measurement_unit and ('per' in measurement_unit.lower() or '/' in measurement_unit):
        # For intensity indicators, we want lower values to score higher
        # Use inverse scaling: score = 100 / (1 + value/baseline)
        # For now, use a placeholder baseline of 1.0
        # Future: Use industry-specific baselines
        baseline = 1.0
        normalized = 100.0 / (1.0 + value / baseline)
        logger.debug(
            f"Normalized {indicator_code} (intensity) from {value} to {normalized:.2f}"
        )
        return normalized
    
    # Handle count indicators (fatalities, complaints, etc.)
    if measurement_unit == 'count':
        # For count indicators, lower is better (especially for negative events)
        # Use inverse scaling with a reasonable max
        max_count = 100.0
        normalized = max(0.0, 100.0 - (value / max_count) * 100.0)
        logger.debug(
            f"Normalized {indicator_code} (count) from {value} to {normalized:.2f}"
        )
        return normalized
    
    # Handle days indicators (e.g., payment days)
    if measurement_unit == 'days':
        # For payment days, lower is generally better (faster payment)
        # Use inverse scaling with 90 days as baseline
        baseline_days = 90.0
        normalized = max(0.0, 100.0 - (value / baseline_days) * 100.0)
        logger.debug(
            f"Normalized {indicator_code} (days) from {value} to {normalized:.2f}"
        )
        return normalized
    
    # For other absolute indicators, use placeholder normalization
    # Future enhancement: Implement proper normalization with industry benchmarks
    logger.debug(
        f"Using placeholder normalization for {indicator_code} "
        f"(unit: {measurement_unit})"
    )
    return 50.0  # Neutral score for now


def get_pillar_breakdown(
    indicator_definitions: List[BRSRIndicatorDefinition],
    extracted_values: Dict[str, float],
) -> Dict[str, Dict]:
    """
    Get detailed breakdown of pillar score calculations for transparency.
    
    This function provides full transparency into how pillar scores are calculated,
    including which indicators contributed, their weights, and normalized values.
    
    Args:
        indicator_definitions: List of BRSR indicator definitions
        extracted_values: Dictionary of extracted numeric values
    
    Returns:
        Dict[str, Dict]: Breakdown by pillar with indicator contributions
        
    Example:
        {
            "E": {
                "score": 62.5,
                "indicators": [
                    {
                        "code": "GHG_SCOPE1_TOTAL",
                        "value": 1250.0,
                        "normalized": 45.0,
                        "weight": 1.0,
                        "contribution": 45.0
                    },
                    ...
                ],
                "total_weight": 3.5
            },
            "S": {...},
            "G": {...}
        }
    
    Requirements: 15.4, 15.5
    """
    logger.info("Generating pillar score breakdown for transparency")
    
    # Group indicators by pillar
    pillar_indicators: Dict[Pillar, List[BRSRIndicatorDefinition]] = {
        Pillar.ENVIRONMENTAL: [],
        Pillar.SOCIAL: [],
        Pillar.GOVERNANCE: [],
    }
    
    for indicator in indicator_definitions:
        pillar_indicators[indicator.pillar].append(indicator)
    
    # Build breakdown for each pillar
    breakdown = {}
    
    for pillar, indicators in pillar_indicators.items():
        pillar_key = pillar.value
        
        # Filter available indicators
        available_indicators = [
            ind for ind in indicators
            if ind.indicator_code in extracted_values
        ]
        
        if not available_indicators:
            breakdown[pillar_key] = {
                "score": None,
                "indicators": [],
                "total_weight": 0.0,
                "message": "No indicators available"
            }
            continue
        
        # Calculate contributions
        indicator_contributions = []
        weighted_sum = 0.0
        total_weight = 0.0
        
        for indicator in available_indicators:
            value = extracted_values[indicator.indicator_code]
            normalized = _normalize_indicator_value(
                value,
                indicator.indicator_code,
                indicator.measurement_unit
            )
            contribution = normalized * indicator.weight
            
            indicator_contributions.append({
                "code": indicator.indicator_code,
                "name": indicator.parameter_name,
                "value": value,
                "unit": indicator.measurement_unit,
                "normalized": round(normalized, 2),
                "weight": indicator.weight,
                "contribution": round(contribution, 2)
            })
            
            weighted_sum += contribution
            total_weight += indicator.weight
        
        pillar_score = weighted_sum / total_weight if total_weight > 0 else None
        
        breakdown[pillar_key] = {
            "score": round(pillar_score, 2) if pillar_score is not None else None,
            "indicators": indicator_contributions,
            "total_weight": round(total_weight, 2),
            "weighted_sum": round(weighted_sum, 2)
        }
    
    logger.info("Pillar breakdown generated successfully")
    return breakdown
