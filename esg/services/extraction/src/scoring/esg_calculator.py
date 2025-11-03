"""
ESG score calculation for ESG Intelligence Platform.

This module calculates the overall ESG score by combining Environmental (E), Social (S),
and Governance (G) pillar scores with configurable weights. It provides full transparency
by storing calculation methodology, indicator contributions, and source citations.

Requirements: 15.3, 15.4, 15.5
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from ..models.brsr_models import BRSRIndicatorDefinition
from .pillar_calculator import calculate_pillar_scores, get_pillar_breakdown

logger = logging.getLogger(__name__)


# Default pillar weights (can be configured)
DEFAULT_PILLAR_WEIGHTS = {
    "E": 0.33,  # Environmental
    "S": 0.33,  # Social
    "G": 0.34,  # Governance (slightly higher to sum to 1.0)
}


def calculate_esg_score(
    indicator_definitions: List[BRSRIndicatorDefinition],
    extracted_values: Dict[str, float],
    pillar_weights: Optional[Dict[str, float]] = None,
) -> Tuple[Optional[float], Dict]:
    """
    Calculate overall ESG score by combining pillar scores with configurable weights.
    
    This function:
    1. Calculates individual pillar scores (E, S, G) using weighted averages
    2. Combines pillar scores using configurable weights (default: E=0.33, S=0.33, G=0.34)
    3. Generates calculation metadata with full transparency
    4. Includes breakdown of which indicators contributed to each pillar
    5. Stores source citations for transparency
    
    The overall ESG score is calculated as:
        ESG Score = (E_score * E_weight) + (S_score * S_weight) + (G_score * G_weight)
    
    If any pillar has no data (score is None), the weights are adjusted proportionally
    to use only available pillars. For example, if Governance has no data:
        ESG Score = (E_score * 0.5) + (S_score * 0.5)
    
    Args:
        indicator_definitions: List of BRSR indicator definitions with pillar and weight info
        extracted_values: Dictionary mapping indicator_code to numeric_value
                         Example: {"GHG_SCOPE1_TOTAL": 1250.0, "WATER_CONSUMPTION_TOTAL": 50000.0}
        pillar_weights: Optional custom weights for pillars (default: E=0.33, S=0.33, G=0.34)
                       Must sum to 1.0 and contain keys 'E', 'S', 'G'
    
    Returns:
        Tuple[Optional[float], Dict]: 
            - overall_score: ESG score (0-100) or None if no data available
            - calculation_metadata: Dictionary with full calculation details including:
                - pillar_scores: Individual E, S, G scores
                - pillar_weights: Weights used (adjusted if pillars missing)
                - pillar_breakdown: Detailed indicator contributions
                - calculation_method: Description of methodology
                - calculated_at: Timestamp
    
    Example:
        >>> definitions = load_brsr_indicators()
        >>> values = {"GHG_SCOPE1_TOTAL": 1250.0, "ENERGY_RENEWABLE_PERCENT": 45.0}
        >>> score, metadata = calculate_esg_score(definitions, values)
        >>> print(f"ESG Score: {score:.2f}")
        ESG Score: 52.5
        >>> print(f"Methodology: {metadata['calculation_method']}")
    
    Requirements: 15.3, 15.4, 15.5
    """
    logger.info(
        f"Calculating overall ESG score from {len(extracted_values)} extracted indicators"
    )
    
    # Use default weights if not provided
    if pillar_weights is None:
        pillar_weights = DEFAULT_PILLAR_WEIGHTS.copy()
    else:
        # Validate custom weights
        _validate_pillar_weights(pillar_weights)
    
    # Calculate individual pillar scores
    env_score, soc_score, gov_score = calculate_pillar_scores(
        indicator_definitions,
        extracted_values
    )
    
    logger.info(
        f"Pillar scores - E: {env_score}, S: {soc_score}, G: {gov_score}"
    )
    
    # Get detailed breakdown for transparency
    pillar_breakdown = get_pillar_breakdown(
        indicator_definitions,
        extracted_values
    )
    
    # Calculate overall ESG score with weight adjustment for missing pillars
    overall_score, adjusted_weights = _calculate_weighted_esg_score(
        env_score,
        soc_score,
        gov_score,
        pillar_weights
    )
    
    # Build calculation metadata for transparency
    calculation_metadata = {
        "pillar_scores": {
            "environmental": round(env_score, 2) if env_score is not None else None,
            "social": round(soc_score, 2) if soc_score is not None else None,
            "governance": round(gov_score, 2) if gov_score is not None else None,
        },
        "pillar_weights": {
            "environmental": adjusted_weights["E"],
            "social": adjusted_weights["S"],
            "governance": adjusted_weights["G"],
        },
        "original_weights": {
            "environmental": pillar_weights["E"],
            "social": pillar_weights["S"],
            "governance": pillar_weights["G"],
        },
        "pillar_breakdown": pillar_breakdown,
        "calculation_method": _get_calculation_method_description(
            env_score, soc_score, gov_score, adjusted_weights
        ),
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "total_indicators_extracted": len(extracted_values),
    }
    
    if overall_score is not None:
        logger.info(f"Overall ESG score calculated: {overall_score:.2f}")
    else:
        logger.warning("Could not calculate overall ESG score - no pillar data available")
    
    return overall_score, calculation_metadata


def _validate_pillar_weights(weights: Dict[str, float]) -> None:
    """
    Validate that pillar weights are valid.
    
    Args:
        weights: Dictionary with keys 'E', 'S', 'G' and float values
    
    Raises:
        ValueError: If weights are invalid
    """
    required_keys = {"E", "S", "G"}
    if set(weights.keys()) != required_keys:
        raise ValueError(
            f"pillar_weights must contain exactly keys {required_keys}, "
            f"got {set(weights.keys())}"
        )
    
    # Check all weights are non-negative
    for pillar, weight in weights.items():
        if weight < 0:
            raise ValueError(
                f"Pillar weight for {pillar} must be non-negative, got {weight}"
            )
    
    # Check weights sum to 1.0 (with small tolerance for floating point)
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(
            f"Pillar weights must sum to 1.0, got {total_weight:.4f}"
        )


def _calculate_weighted_esg_score(
    env_score: Optional[float],
    soc_score: Optional[float],
    gov_score: Optional[float],
    pillar_weights: Dict[str, float],
) -> Tuple[Optional[float], Dict[str, float]]:
    """
    Calculate weighted ESG score with adjustment for missing pillars.
    
    If any pillar has no data (score is None), the weights are adjusted proportionally
    to use only available pillars. This ensures the overall score is still meaningful
    even with partial data.
    
    Args:
        env_score: Environmental pillar score (0-100) or None
        soc_score: Social pillar score (0-100) or None
        gov_score: Governance pillar score (0-100) or None
        pillar_weights: Original weights for E, S, G
    
    Returns:
        Tuple[Optional[float], Dict[str, float]]:
            - overall_score: Weighted ESG score or None if no data
            - adjusted_weights: Weights used (adjusted for missing pillars)
    """
    # Collect available pillar scores
    available_pillars = []
    if env_score is not None:
        available_pillars.append(("E", env_score))
    if soc_score is not None:
        available_pillars.append(("S", soc_score))
    if gov_score is not None:
        available_pillars.append(("G", gov_score))
    
    # If no pillars available, return None
    if not available_pillars:
        logger.warning("No pillar scores available, cannot calculate ESG score")
        return None, {"E": 0.0, "S": 0.0, "G": 0.0}
    
    # Calculate adjusted weights (proportional to original weights)
    total_available_weight = sum(
        pillar_weights[pillar] for pillar, _ in available_pillars
    )
    
    adjusted_weights = {
        "E": 0.0,
        "S": 0.0,
        "G": 0.0,
    }
    
    for pillar, _ in available_pillars:
        adjusted_weights[pillar] = pillar_weights[pillar] / total_available_weight
    
    logger.debug(
        f"Adjusted weights for {len(available_pillars)} available pillars: "
        f"{adjusted_weights}"
    )
    
    # Calculate weighted score
    weighted_sum = 0.0
    for pillar, score in available_pillars:
        contribution = score * adjusted_weights[pillar]
        weighted_sum += contribution
        logger.debug(
            f"  {pillar} pillar: score={score:.2f}, "
            f"weight={adjusted_weights[pillar]:.4f}, "
            f"contribution={contribution:.2f}"
        )
    
    overall_score = weighted_sum
    
    logger.debug(f"Overall ESG score: {overall_score:.2f}")
    
    return overall_score, adjusted_weights


def _get_calculation_method_description(
    env_score: Optional[float],
    soc_score: Optional[float],
    gov_score: Optional[float],
    adjusted_weights: Dict[str, float],
) -> str:
    """
    Generate human-readable description of calculation methodology.
    
    Args:
        env_score: Environmental pillar score or None
        soc_score: Social pillar score or None
        gov_score: Governance pillar score or None
        adjusted_weights: Adjusted weights used in calculation
    
    Returns:
        str: Description of calculation method
    """
    available_pillars = []
    if env_score is not None:
        available_pillars.append(
            f"Environmental ({adjusted_weights['E']:.2%})"
        )
    if soc_score is not None:
        available_pillars.append(
            f"Social ({adjusted_weights['S']:.2%})"
        )
    if gov_score is not None:
        available_pillars.append(
            f"Governance ({adjusted_weights['G']:.2%})"
        )
    
    if not available_pillars:
        return "No pillar data available for ESG score calculation"
    
    pillars_str = ", ".join(available_pillars)
    
    method = (
        f"Overall ESG score calculated as weighted average of {len(available_pillars)} "
        f"pillar scores: {pillars_str}. Each pillar score is calculated from BRSR Core "
        f"indicators using weighted averages based on indicator importance. "
        f"Indicator values are normalized to 0-100 scale before aggregation."
    )
    
    return method


def get_esg_score_with_citations(
    indicator_definitions: List[BRSRIndicatorDefinition],
    extracted_indicators: List[Dict],
    pillar_weights: Optional[Dict[str, float]] = None,
) -> Tuple[Optional[float], Dict]:
    """
    Calculate ESG score with full source citations for transparency.
    
    This function extends calculate_esg_score() by including source citations
    (PDF names, page numbers, chunk IDs) for every indicator that contributed
    to the score. This enables full traceability from the overall score down
    to specific pages in source documents.
    
    Args:
        indicator_definitions: List of BRSR indicator definitions
        extracted_indicators: List of extracted indicator dictionaries with:
            - indicator_code: str
            - numeric_value: float
            - source_pages: List[int]
            - source_chunk_ids: List[int]
            - object_key: str (PDF path)
            - confidence_score: float
        pillar_weights: Optional custom weights for pillars
    
    Returns:
        Tuple[Optional[float], Dict]:
            - overall_score: ESG score (0-100) or None
            - calculation_metadata: Dictionary with calculation details and citations
    
    Example:
        >>> score, metadata = get_esg_score_with_citations(definitions, indicators)
        >>> for pillar, data in metadata['pillar_breakdown'].items():
        ...     for ind in data['indicators']:
        ...         print(f"{ind['code']}: pages {ind['source_pages']}")
    
    Requirements: 15.4, 15.5
    """
    logger.info(
        f"Calculating ESG score with citations from {len(extracted_indicators)} indicators"
    )
    
    # Build extracted values dictionary
    extracted_values = {}
    citations_map = {}
    
    for indicator in extracted_indicators:
        code = indicator["indicator_code"]
        if indicator.get("numeric_value") is not None:
            extracted_values[code] = indicator["numeric_value"]
            
            # Store citation information
            citations_map[code] = {
                "object_key": indicator.get("object_key", ""),
                "source_pages": indicator.get("source_pages", []),
                "source_chunk_ids": indicator.get("source_chunk_ids", []),
                "confidence_score": indicator.get("confidence_score", 0.0),
            }
    
    # Calculate ESG score
    overall_score, calculation_metadata = calculate_esg_score(
        indicator_definitions,
        extracted_values,
        pillar_weights
    )
    
    # Enhance breakdown with citations
    for pillar_key, pillar_data in calculation_metadata["pillar_breakdown"].items():
        for indicator in pillar_data.get("indicators", []):
            code = indicator["code"]
            if code in citations_map:
                indicator["citations"] = citations_map[code]
    
    logger.info("ESG score with citations calculated successfully")
    
    return overall_score, calculation_metadata
