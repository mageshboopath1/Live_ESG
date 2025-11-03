"""
Prompt templates for LangChain-based indicator extraction.

This module provides prompt templates and output parsers for extracting
BRSR Core indicators from company sustainability reports using LLMs.
"""

from .extraction_prompts import (
    create_extraction_prompt,
    get_output_parser,
    EXTRACTION_TEMPLATE,
)

__all__ = [
    "create_extraction_prompt",
    "get_output_parser",
    "EXTRACTION_TEMPLATE",
]
