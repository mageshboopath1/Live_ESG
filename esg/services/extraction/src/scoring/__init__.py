"""
Scoring module for ESG pillar and overall score calculation.

This module provides functions for:
- Calculating pillar scores (Environmental, Social, Governance) from extracted indicators
- Calculating overall ESG score by combining pillar scores with configurable weights
- Aggregating indicator values using weighted averages
- Handling missing indicators gracefully
- Preparing score calculation metadata for transparency
- Including source citations for full traceability

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
"""

from .esg_calculator import (
    calculate_esg_score,
    get_esg_score_with_citations,
    DEFAULT_PILLAR_WEIGHTS,
)
from .pillar_calculator import calculate_pillar_scores, get_pillar_breakdown

__all__ = [
    "calculate_pillar_scores",
    "get_pillar_breakdown",
    "calculate_esg_score",
    "get_esg_score_with_citations",
    "DEFAULT_PILLAR_WEIGHTS",
]
