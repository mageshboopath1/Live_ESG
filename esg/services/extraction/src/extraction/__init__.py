"""
Extraction module for BRSR Core indicator extraction.

This module provides high-level functions for extracting BRSR indicators
from company sustainability reports using LangChain and Google GenAI.
"""

from .extractor import extract_indicator, extract_indicators_batch

__all__ = ["extract_indicator", "extract_indicators_batch"]
