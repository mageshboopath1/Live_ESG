#!/usr/bin/env python3
"""
Example script demonstrating validation integration with extraction pipeline.

This script shows how to:
1. Extract indicators from a document
2. Validate each extracted indicator
3. Update validation status
4. Store indicators with validation results

Requirements: 13.1, 13.2, 13.3, 13.4
"""

import logging
from typing import List

from src.config import config
from src.db.repository import (
    load_brsr_indicators,
    store_extracted_indicators,
    get_company_id_by_name,
    parse_object_key,
)
from src.extraction.extractor import extract_indicator
from src.models.brsr_models import (
    BRSRIndicatorDefinition,
    ExtractedIndicator,
)
from src.validation import validate_indicator, ValidationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def extract_and_validate_indicator(
    indicator_definition: BRSRIndicatorDefinition,
    object_key: str,
    company_name: str,
    report_year: int,
    company_id: int,
) -> tuple[ExtractedIndicator, ValidationResult]:
    """
    Extract and validate a single indicator.
    
    Args:
        indicator_definition: BRSR indicator definition
        object_key: MinIO object key for the document
        company_name: Name of the company
        report_year: Year of the report
        company_id: Database ID of the company
        
    Returns:
        Tuple of (extracted_indicator, validation_result)
    """
    logger.info(f"Extracting indicator: {indicator_definition.indicator_code}")
    
    # Step 1: Extract indicator
    extracted = extract_indicator(
        indicator_definition=indicator_definition,
        company_name=company_name,
        report_year=report_year,
        object_key=object_key,
        company_id=company_id,
        connection_string=config.database_url,
        google_api_key=config.google_api_key,
        k=10,
    )
    
    logger.info(
        f"Extracted value: {extracted.extracted_value} "
        f"(confidence: {extracted.confidence_score:.2f})"
    )
    
    # Step 2: Validate extracted indicator
    validation_result = validate_indicator(
        extracted_indicator=extracted,
        indicator_definition=indicator_definition,
    )
    
    # Step 3: Update validation status based on result
    extracted.validation_status = validation_result.validation_status
    
    # Log validation results
    if validation_result.is_valid:
        logger.info(
            f"✓ Indicator {indicator_definition.indicator_code} is valid"
        )
        if validation_result.warnings:
            logger.warning(
                f"  Warnings: {', '.join(validation_result.warnings)}"
            )
    else:
        logger.error(
            f"✗ Indicator {indicator_definition.indicator_code} is invalid"
        )
        logger.error(f"  Errors: {', '.join(validation_result.errors)}")
    
    return extracted, validation_result


def extract_and_validate_batch(
    object_key: str,
    indicator_codes: List[str] = None,
) -> tuple[List[ExtractedIndicator], dict]:
    """
    Extract and validate multiple indicators for a document.
    
    Args:
        object_key: MinIO object key (e.g., "RELIANCE/2024_BRSR.pdf")
        indicator_codes: Optional list of specific indicator codes to extract.
                        If None, extracts all indicators.
        
    Returns:
        Tuple of (extracted_indicators, validation_summary)
    """
    logger.info(f"Starting batch extraction and validation for: {object_key}")
    
    # Parse object key
    company_name, report_year = parse_object_key(object_key)
    company_id = get_company_id_by_name(company_name)
    
    if company_id is None:
        raise ValueError(f"Company '{company_name}' not found in database")
    
    logger.info(f"Company: {company_name} (ID: {company_id}), Year: {report_year}")
    
    # Load indicator definitions
    all_indicators = load_brsr_indicators()
    
    # Filter indicators if specific codes provided
    if indicator_codes:
        indicators_to_extract = [
            ind for ind in all_indicators
            if ind.indicator_code in indicator_codes
        ]
        logger.info(
            f"Extracting {len(indicators_to_extract)} specific indicators"
        )
    else:
        indicators_to_extract = all_indicators
        logger.info(f"Extracting all {len(indicators_to_extract)} indicators")
    
    # Extract and validate each indicator
    extracted_indicators = []
    validation_summary = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "with_warnings": 0,
        "failed_extraction": 0,
    }
    
    for indicator_def in indicators_to_extract:
        try:
            extracted, validation_result = extract_and_validate_indicator(
                indicator_definition=indicator_def,
                object_key=object_key,
                company_name=company_name,
                report_year=report_year,
                company_id=company_id,
            )
            
            extracted_indicators.append(extracted)
            validation_summary["total"] += 1
            
            if validation_result.is_valid:
                validation_summary["valid"] += 1
                if validation_result.warnings:
                    validation_summary["with_warnings"] += 1
            else:
                validation_summary["invalid"] += 1
                
        except Exception as e:
            logger.error(
                f"Failed to extract indicator {indicator_def.indicator_code}: {e}",
                exc_info=True,
            )
            validation_summary["failed_extraction"] += 1
    
    # Log summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total indicators processed: {validation_summary['total']}")
    logger.info(f"Valid indicators: {validation_summary['valid']}")
    logger.info(f"Invalid indicators: {validation_summary['invalid']}")
    logger.info(f"Indicators with warnings: {validation_summary['with_warnings']}")
    logger.info(f"Failed extractions: {validation_summary['failed_extraction']}")
    logger.info("=" * 60)
    
    return extracted_indicators, validation_summary


def store_validated_indicators(
    extracted_indicators: List[ExtractedIndicator],
) -> int:
    """
    Store validated indicators in the database.
    
    Args:
        extracted_indicators: List of extracted and validated indicators
        
    Returns:
        Number of indicators stored
    """
    if not extracted_indicators:
        logger.warning("No indicators to store")
        return 0
    
    logger.info(f"Storing {len(extracted_indicators)} validated indicators...")
    
    # Store indicators (includes validation_status)
    count = store_extracted_indicators(extracted_indicators)
    
    logger.info(f"Successfully stored {count} indicators")
    
    # Log validation status breakdown
    valid_count = sum(
        1 for ind in extracted_indicators
        if ind.validation_status == "valid"
    )
    invalid_count = sum(
        1 for ind in extracted_indicators
        if ind.validation_status == "invalid"
    )
    
    logger.info(f"  Valid: {valid_count}")
    logger.info(f"  Invalid: {invalid_count}")
    
    return count


def main():
    """Main entry point for example script."""
    # Example 1: Extract and validate a single indicator
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 1: Single Indicator Extraction and Validation")
    logger.info("=" * 60 + "\n")
    
    # Load a specific indicator
    indicators = load_brsr_indicators()
    ghg_indicator = next(
        ind for ind in indicators
        if ind.indicator_code == "GHG_SCOPE1_TOTAL"
    )
    
    # Extract and validate
    try:
        extracted, validation_result = extract_and_validate_indicator(
            indicator_definition=ghg_indicator,
            object_key="RELIANCE/2024_BRSR.pdf",
            company_name="RELIANCE",
            report_year=2024,
            company_id=1,
        )
        
        print(f"\nExtracted Value: {extracted.extracted_value}")
        print(f"Numeric Value: {extracted.numeric_value}")
        print(f"Confidence Score: {extracted.confidence_score}")
        print(f"Validation Status: {extracted.validation_status}")
        
        if validation_result.errors:
            print(f"Errors: {validation_result.errors}")
        if validation_result.warnings:
            print(f"Warnings: {validation_result.warnings}")
            
    except Exception as e:
        logger.error(f"Example 1 failed: {e}", exc_info=True)
    
    # Example 2: Batch extraction and validation
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 2: Batch Extraction and Validation")
    logger.info("=" * 60 + "\n")
    
    try:
        # Extract specific indicators
        indicator_codes = [
            "GHG_SCOPE1_TOTAL",
            "WATER_CONSUMPTION_TOTAL",
            "ENERGY_RENEWABLE_PERCENT",
        ]
        
        extracted_indicators, summary = extract_and_validate_batch(
            object_key="RELIANCE/2024_BRSR.pdf",
            indicator_codes=indicator_codes,
        )
        
        # Store validated indicators
        if extracted_indicators:
            store_validated_indicators(extracted_indicators)
            
    except Exception as e:
        logger.error(f"Example 2 failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
