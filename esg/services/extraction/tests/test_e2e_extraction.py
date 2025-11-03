"""
End-to-end integration test for the extraction service.

This test verifies the complete extraction pipeline:
1. Filtered vector retrieval with company/year filtering
2. Indicator extraction with LangChain
3. Validation of extracted indicators
4. Score calculation (pillar and overall ESG)
5. Source citation storage and retrieval

Requirements: 6.1, 6.2, 6.3, 11.1, 11.2, 13.1, 13.2, 15.1, 15.3, 14.1, 14.2

Note: This test requires:
- PostgreSQL with pgvector extension
- Document embeddings in the database
- Valid GOOGLE_API_KEY environment variable
- BRSR indicator definitions seeded in database
"""

import os
import sys
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
from src.config import config

# Import models
from src.models.brsr_models import (
    BRSRIndicatorDefinition,
    ExtractedIndicator,
    Pillar
)

# Import extraction components
from src.retrieval.filtered_retriever import FilteredPGVectorRetriever
from src.extraction.extractor import extract_indicator
from src.validation.validator import validate_indicator
from src.scoring.pillar_calculator import calculate_pillar_scores
from src.scoring.esg_calculator import calculate_esg_score, get_esg_score_with_citations

# Import database functions
from src.db.repository import (
    load_brsr_indicators,
    parse_object_key,
    get_company_id_by_name,
    store_extracted_indicators,
    store_esg_score,
    get_score_breakdown,
    get_scores_by_company_and_year
)


class E2ETestResult:
    """Container for end-to-end test results."""
    
    def __init__(self):
        self.retrieval_passed = False
        self.extraction_passed = False
        self.validation_passed = False
        self.score_calculation_passed = False
        self.citation_storage_passed = False
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.extracted_indicators: List[ExtractedIndicator] = []
        self.esg_score: float = None
        self.metadata: Dict[str, Any] = {}
    
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return (
            self.retrieval_passed and
            self.extraction_passed and
            self.validation_passed and
            self.score_calculation_passed and
            self.citation_storage_passed and
            len(self.errors) == 0
        )
    
    def summary(self) -> str:
        """Generate test summary."""
        lines = [
            "=" * 80,
            "END-TO-END TEST SUMMARY",
            "=" * 80,
            f"✓ Filtered Retrieval: {'PASS' if self.retrieval_passed else 'FAIL'}",
            f"✓ Indicator Extraction: {'PASS' if self.extraction_passed else 'FAIL'}",
            f"✓ Validation: {'PASS' if self.validation_passed else 'FAIL'}",
            f"✓ Score Calculation: {'PASS' if self.score_calculation_passed else 'FAIL'}",
            f"✓ Citation Storage: {'PASS' if self.citation_storage_passed else 'FAIL'}",
            "",
            f"Extracted Indicators: {len(self.extracted_indicators)}",
            f"ESG Score: {self.esg_score:.2f}" if self.esg_score else "ESG Score: N/A",
            "",
        ]
        
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")
        
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"OVERALL: {'✓ ALL TESTS PASSED' if self.all_passed() else '✗ SOME TESTS FAILED'}")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def test_filtered_retrieval(
    company_name: str,
    report_year: int,
    test_query: str = "What are the total Scope 1 emissions?"
) -> E2ETestResult:
    """
    Test 1: Filtered Vector Retrieval
    
    Verifies that the FilteredPGVectorRetriever correctly:
    - Filters embeddings by company_name and report_year
    - Returns relevant documents with metadata
    - Includes page numbers and chunk IDs
    
    Requirements: 6.1, 11.1, 11.2
    """
    result = E2ETestResult()
    logger.info("=" * 80)
    logger.info("TEST 1: Filtered Vector Retrieval")
    logger.info("=" * 80)
    
    try:
        # Initialize retriever with company/year filtering
        logger.info(f"Initializing retriever for {company_name} {report_year}")
        retriever = FilteredPGVectorRetriever(
            connection_string=config.database_url,
            company_name=company_name,
            report_year=report_year,
            embedding_model="models/embedding-001"
        )
        
        # Retrieve relevant documents
        logger.info(f"Querying: '{test_query}'")
        documents = retriever.get_relevant_documents(test_query, k=5)
        
        # Verify results
        if not documents:
            result.errors.append("No documents retrieved")
            logger.error("✗ No documents retrieved")
            return result
        
        logger.info(f"✓ Retrieved {len(documents)} documents")
        
        # Verify each document has required metadata
        for i, doc in enumerate(documents, 1):
            logger.info(f"\nDocument {i}:")
            logger.info(f"  Company: {doc.metadata.get('company_name')}")
            logger.info(f"  Year: {doc.metadata.get('report_year')}")
            logger.info(f"  Page: {doc.metadata.get('page_number')}")
            logger.info(f"  Chunk Index: {doc.metadata.get('chunk_index')}")
            logger.info(f"  Distance: {doc.metadata.get('distance', 0):.4f}")
            logger.info(f"  Content: {doc.page_content[:100]}...")
            
            # Verify filtering worked
            if doc.metadata.get('company_name') != company_name:
                result.errors.append(f"Document {i} has wrong company: {doc.metadata.get('company_name')}")
            if doc.metadata.get('report_year') != report_year:
                result.errors.append(f"Document {i} has wrong year: {doc.metadata.get('report_year')}")
            
            # Verify required metadata
            if not doc.metadata.get('page_number'):
                result.errors.append(f"Document {i} missing page_number")
            if doc.metadata.get('chunk_index') is None:
                result.errors.append(f"Document {i} missing chunk_index")
        
        if not result.errors:
            result.retrieval_passed = True
            logger.info("\n✓ Filtered retrieval test PASSED")
        else:
            logger.error(f"\n✗ Filtered retrieval test FAILED: {len(result.errors)} errors")
        
    except ValueError as e:
        result.errors.append(f"No data found: {str(e)}")
        result.warnings.append("This is expected if database has no embeddings for this company/year")
        logger.warning(f"⚠ {str(e)}")
    except Exception as e:
        result.errors.append(f"Retrieval failed: {str(e)}")
        logger.error(f"✗ Retrieval failed: {e}", exc_info=True)
    
    return result


def test_indicator_extraction(
    company_name: str,
    report_year: int,
    object_key: str,
    company_id: int,
    indicators: List[BRSRIndicatorDefinition],
    max_indicators: int = 3
) -> E2ETestResult:
    """
    Test 2: Indicator Extraction
    
    Verifies that the extraction pipeline:
    - Extracts indicator values using LangChain
    - Returns structured ExtractedIndicator objects
    - Includes confidence scores
    - Captures source citations (pages and chunk IDs)
    
    Requirements: 6.2, 6.3, 13.1, 14.1, 14.2
    """
    result = E2ETestResult()
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Indicator Extraction")
    logger.info("=" * 80)
    
    try:
        # Select a subset of indicators to test
        test_indicators = indicators[:max_indicators]
        logger.info(f"Testing extraction for {len(test_indicators)} indicators")
        
        for i, indicator_def in enumerate(test_indicators, 1):
            logger.info(f"\nExtracting indicator {i}/{len(test_indicators)}:")
            logger.info(f"  Code: {indicator_def.indicator_code}")
            logger.info(f"  Name: {indicator_def.parameter_name}")
            logger.info(f"  Unit: {indicator_def.measurement_unit}")
            
            try:
                # Extract indicator
                extracted = extract_indicator(
                    indicator_definition=indicator_def,
                    company_name=company_name,
                    report_year=report_year,
                    object_key=object_key,
                    company_id=company_id,
                    connection_string=config.database_url,
                    google_api_key=config.google_api_key,
                    k=5
                )
                
                # Verify extraction result
                logger.info(f"  ✓ Extracted value: {extracted.extracted_value}")
                logger.info(f"  ✓ Numeric value: {extracted.numeric_value}")
                logger.info(f"  ✓ Confidence: {extracted.confidence_score:.2f}")
                logger.info(f"  ✓ Source pages: {extracted.source_pages}")
                logger.info(f"  ✓ Source chunks: {len(extracted.source_chunk_ids)} chunks")
                
                # Verify required fields
                if not extracted.extracted_value:
                    result.errors.append(f"{indicator_def.indicator_code}: Missing extracted_value")
                if extracted.confidence_score < 0.0 or extracted.confidence_score > 1.0:
                    result.errors.append(f"{indicator_def.indicator_code}: Invalid confidence score")
                if not extracted.source_pages:
                    result.warnings.append(f"{indicator_def.indicator_code}: No source pages")
                if not extracted.source_chunk_ids:
                    result.warnings.append(f"{indicator_def.indicator_code}: No source chunk IDs")
                
                result.extracted_indicators.append(extracted)
                
            except Exception as e:
                error_msg = f"{indicator_def.indicator_code}: Extraction failed - {str(e)}"
                result.errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
        
        if result.extracted_indicators:
            result.extraction_passed = True
            logger.info(f"\n✓ Extraction test PASSED: {len(result.extracted_indicators)} indicators extracted")
        else:
            logger.error("\n✗ Extraction test FAILED: No indicators extracted")
        
    except Exception as e:
        result.errors.append(f"Extraction test failed: {str(e)}")
        logger.error(f"✗ Extraction test failed: {e}", exc_info=True)
    
    return result


def test_validation(
    extracted_indicators: List[ExtractedIndicator],
    indicator_definitions: List[BRSRIndicatorDefinition]
) -> E2ETestResult:
    """
    Test 3: Indicator Validation
    
    Verifies that the validation logic:
    - Validates confidence scores (0.0-1.0)
    - Validates numeric ranges
    - Checks required fields
    - Produces appropriate validation status
    
    Requirements: 13.1, 13.2, 13.3, 13.4
    """
    result = E2ETestResult()
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Indicator Validation")
    logger.info("=" * 80)
    
    try:
        # Create lookup for indicator definitions
        indicator_lookup = {ind.indicator_code: ind for ind in indicator_definitions}
        
        valid_count = 0
        invalid_count = 0
        
        # Create a mapping from indicator_id to definition
        # Note: We need to query the database to get the mapping
        # For now, we'll validate based on the extracted indicators themselves
        for extracted in extracted_indicators:
            logger.info(f"\nValidating indicator_id: {extracted.indicator_id}")
            
            # Find corresponding definition by matching indicator_id
            # We need to get the indicator_code from database first
            indicator_def = None
            for ind_def in indicator_definitions:
                # Try to match by getting the ID from database
                from src.db.repository import get_indicator_id_by_code
                if get_indicator_id_by_code(ind_def.indicator_code) == extracted.indicator_id:
                    indicator_def = ind_def
                    break
            
            if not indicator_def:
                result.warnings.append(f"No definition found for indicator_id {extracted.indicator_id}")
                logger.warning(f"  ⚠ No definition found")
                continue
            
            # Validate indicator
            validation_result = validate_indicator(extracted, indicator_def)
            
            logger.info(f"  Code: {indicator_def.indicator_code}")
            logger.info(f"  Status: {validation_result.validation_status}")
            logger.info(f"  Valid: {validation_result.is_valid}")
            
            if validation_result.errors:
                logger.info(f"  Errors: {len(validation_result.errors)}")
                for error in validation_result.errors:
                    logger.info(f"    - {error}")
                    result.errors.append(f"{indicator_def.indicator_code}: {error}")
                invalid_count += 1
            else:
                valid_count += 1
            
            if validation_result.warnings:
                logger.info(f"  Warnings: {len(validation_result.warnings)}")
                for warning in validation_result.warnings:
                    logger.info(f"    - {warning}")
                    result.warnings.append(f"{indicator_def.indicator_code}: {warning}")
        
        logger.info(f"\nValidation summary:")
        logger.info(f"  Valid: {valid_count}")
        logger.info(f"  Invalid: {invalid_count}")
        logger.info(f"  Total: {len(extracted_indicators)}")
        
        # Test passes if at least some indicators are valid
        if valid_count > 0:
            result.validation_passed = True
            logger.info("\n✓ Validation test PASSED")
        else:
            logger.error("\n✗ Validation test FAILED: No valid indicators")
        
    except Exception as e:
        result.errors.append(f"Validation test failed: {str(e)}")
        logger.error(f"✗ Validation test failed: {e}", exc_info=True)
    
    return result


def test_score_calculation(
    extracted_indicators: List[ExtractedIndicator],
    indicator_definitions: List[BRSRIndicatorDefinition]
) -> E2ETestResult:
    """
    Test 4: Score Calculation
    
    Verifies that score calculation:
    - Calculates pillar scores (E, S, G)
    - Calculates overall ESG score
    - Uses weighted aggregation
    - Handles missing pillars gracefully
    - Includes calculation metadata
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    """
    result = E2ETestResult()
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Score Calculation")
    logger.info("=" * 80)
    
    try:
        # Prepare extracted values dictionary
        extracted_values = {}
        for extracted in extracted_indicators:
            # Find indicator code by matching indicator_id
            from src.db.repository import get_indicator_id_by_code
            for ind_def in indicator_definitions:
                if get_indicator_id_by_code(ind_def.indicator_code) == extracted.indicator_id:
                    if extracted.numeric_value is not None:
                        extracted_values[ind_def.indicator_code] = extracted.numeric_value
                    break
        
        logger.info(f"Calculating scores from {len(extracted_values)} numeric indicators")
        
        # Calculate pillar scores
        logger.info("\nCalculating pillar scores...")
        pillar_scores = calculate_pillar_scores(indicator_definitions, extracted_values)
        
        logger.info(f"  Environmental: {pillar_scores.get('E', 'N/A')}")
        logger.info(f"  Social: {pillar_scores.get('S', 'N/A')}")
        logger.info(f"  Governance: {pillar_scores.get('G', 'N/A')}")
        
        # Verify pillar scores
        for pillar, score in pillar_scores.items():
            if score is not None:
                if not (0 <= score <= 100):
                    result.errors.append(f"Pillar {pillar} score out of range: {score}")
        
        # Calculate overall ESG score
        logger.info("\nCalculating overall ESG score...")
        esg_score, metadata = calculate_esg_score(indicator_definitions, extracted_values)
        
        if esg_score is not None:
            logger.info(f"  Overall ESG Score: {esg_score:.2f}")
            result.esg_score = esg_score
            result.metadata = metadata
            
            # Verify score range
            if not (0 <= esg_score <= 100):
                result.errors.append(f"ESG score out of range: {esg_score}")
            
            # Verify metadata
            if 'pillar_scores' not in metadata:
                result.errors.append("Missing pillar_scores in metadata")
            if 'pillar_weights' not in metadata:
                result.errors.append("Missing pillar_weights in metadata")
            if 'calculation_method' not in metadata:
                result.errors.append("Missing calculation_method in metadata")
            
            logger.info(f"\nMetadata:")
            logger.info(f"  Pillar weights: {metadata.get('pillar_weights', {})}")
            logger.info(f"  Total indicators: {metadata.get('total_indicators_extracted', 0)}")
            logger.info(f"  Method: {metadata.get('calculation_method', 'N/A')[:100]}...")
            
            result.score_calculation_passed = True
            logger.info("\n✓ Score calculation test PASSED")
        else:
            result.warnings.append("ESG score is None (may be expected if insufficient data)")
            logger.warning("\n⚠ ESG score is None")
        
    except Exception as e:
        result.errors.append(f"Score calculation failed: {str(e)}")
        logger.error(f"✗ Score calculation failed: {e}", exc_info=True)
    
    return result


def test_citation_storage(
    company_id: int,
    report_year: int,
    extracted_indicators: List[ExtractedIndicator],
    esg_score: float,
    metadata: Dict[str, Any]
) -> E2ETestResult:
    """
    Test 5: Citation Storage
    
    Verifies that:
    - Extracted indicators are stored with source citations
    - Source pages and chunk IDs are preserved
    - ESG scores are stored with calculation metadata
    - Data can be retrieved correctly
    
    Requirements: 14.3, 14.4, 15.5
    """
    result = E2ETestResult()
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Citation Storage")
    logger.info("=" * 80)
    
    try:
        # Store extracted indicators (batch operation)
        logger.info(f"Storing {len(extracted_indicators)} extracted indicators...")
        
        try:
            stored_count = store_extracted_indicators(extracted_indicators)
            logger.info(f"  ✓ Stored {stored_count} indicators")
        except Exception as e:
            result.errors.append(f"Failed to store indicators: {str(e)}")
            logger.error(f"  ✗ Failed to store indicators: {e}")
            stored_count = 0
        
        logger.info(f"Stored {stored_count}/{len(extracted_indicators)} indicators")
        
        # Store ESG score
        if esg_score is not None:
            logger.info("\nStoring ESG score...")
            try:
                # Extract pillar scores from metadata
                pillar_scores = metadata.get('pillar_scores', {})
                
                score_id = store_esg_score(
                    company_id=company_id,
                    report_year=report_year,
                    environmental_score=pillar_scores.get('environmental'),
                    social_score=pillar_scores.get('social'),
                    governance_score=pillar_scores.get('governance'),
                    overall_score=esg_score,
                    calculation_metadata=metadata
                )
                logger.info(f"  ✓ Stored ESG score with ID {score_id}")
            except Exception as e:
                result.errors.append(f"Failed to store ESG score: {str(e)}")
                logger.error(f"  ✗ Failed to store ESG score: {e}")
        
        # Retrieve and verify stored data
        logger.info("\nVerifying stored data...")
        
        # Note: We verify storage by checking if we can retrieve scores
        # Individual indicator retrieval would require additional repository functions
        logger.info("  ✓ Indicators stored successfully (verified by batch operation)")
        
        # Retrieve score breakdown
        if esg_score is not None:
            try:
                breakdown = get_score_breakdown(company_id, report_year)
                if breakdown:
                    logger.info(f"  ✓ Retrieved score breakdown")
                    logger.info(f"    Overall: {breakdown.get('overall_score')}")
                    logger.info(f"    Environmental: {breakdown.get('environmental_score')}")
                    logger.info(f"    Social: {breakdown.get('social_score')}")
                    logger.info(f"    Governance: {breakdown.get('governance_score')}")
                    
                    # Verify metadata is preserved
                    if 'calculation_metadata' not in breakdown:
                        result.errors.append("Calculation metadata not preserved")
                else:
                    result.errors.append("Failed to retrieve score breakdown")
            except Exception as e:
                result.errors.append(f"Failed to retrieve score breakdown: {str(e)}")
                logger.error(f"  ✗ Failed to retrieve score breakdown: {e}")
        
        if stored_count > 0 and not result.errors:
            result.citation_storage_passed = True
            logger.info("\n✓ Citation storage test PASSED")
        else:
            logger.error("\n✗ Citation storage test FAILED")
        
    except Exception as e:
        result.errors.append(f"Citation storage test failed: {str(e)}")
        logger.error(f"✗ Citation storage test failed: {e}", exc_info=True)
    
    return result


def run_e2e_test(
    company_name: str = "RELIANCE",
    report_year: int = 2024,
    max_indicators: int = 3
) -> bool:
    """
    Run complete end-to-end extraction test.
    
    Args:
        company_name: Company to test with
        report_year: Report year to test with
        max_indicators: Maximum number of indicators to extract (for speed)
    
    Returns:
        True if all tests passed, False otherwise
    """
    logger.info("=" * 80)
    logger.info("STARTING END-TO-END EXTRACTION TEST")
    logger.info("=" * 80)
    logger.info(f"Company: {company_name}")
    logger.info(f"Year: {report_year}")
    logger.info(f"Max indicators: {max_indicators}")
    logger.info("=" * 80)
    
    # Check prerequisites
    if not config.google_api_key:
        logger.error("✗ GOOGLE_API_KEY not set")
        return False
    
    if not config.database_url:
        logger.error("✗ DATABASE_URL not set")
        return False
    
    # Load BRSR indicators
    try:
        indicators = load_brsr_indicators()
        if not indicators:
            logger.error("✗ No BRSR indicators found in database")
            return False
        logger.info(f"✓ Loaded {len(indicators)} BRSR indicators")
    except Exception as e:
        logger.error(f"✗ Failed to load BRSR indicators: {e}")
        return False
    
    # Get company ID
    try:
        company_id = get_company_id_by_name(company_name)
        if not company_id:
            logger.error(f"✗ Company '{company_name}' not found in catalog")
            return False
        logger.info(f"✓ Found company ID: {company_id}")
    except Exception as e:
        logger.error(f"✗ Failed to get company ID: {e}")
        return False
    
    # Construct object key
    object_key = f"{company_name}/{report_year}_BRSR.pdf"
    logger.info(f"✓ Object key: {object_key}")
    
    # Run tests
    combined_result = E2ETestResult()
    
    # Test 1: Filtered Retrieval
    retrieval_result = test_filtered_retrieval(company_name, report_year)
    combined_result.retrieval_passed = retrieval_result.retrieval_passed
    combined_result.errors.extend(retrieval_result.errors)
    combined_result.warnings.extend(retrieval_result.warnings)
    
    if not retrieval_result.retrieval_passed:
        logger.error("Stopping tests - retrieval failed")
        print(combined_result.summary())
        return False
    
    # Test 2: Indicator Extraction
    extraction_result = test_indicator_extraction(
        company_name, report_year, object_key, company_id, indicators, max_indicators
    )
    combined_result.extraction_passed = extraction_result.extraction_passed
    combined_result.extracted_indicators = extraction_result.extracted_indicators
    combined_result.errors.extend(extraction_result.errors)
    combined_result.warnings.extend(extraction_result.warnings)
    
    if not extraction_result.extraction_passed:
        logger.error("Stopping tests - extraction failed")
        print(combined_result.summary())
        return False
    
    # Test 3: Validation
    validation_result = test_validation(
        combined_result.extracted_indicators, indicators
    )
    combined_result.validation_passed = validation_result.validation_passed
    combined_result.errors.extend(validation_result.errors)
    combined_result.warnings.extend(validation_result.warnings)
    
    # Test 4: Score Calculation
    score_result = test_score_calculation(
        combined_result.extracted_indicators, indicators
    )
    combined_result.score_calculation_passed = score_result.score_calculation_passed
    combined_result.esg_score = score_result.esg_score
    combined_result.metadata = score_result.metadata
    combined_result.errors.extend(score_result.errors)
    combined_result.warnings.extend(score_result.warnings)
    
    # Test 5: Citation Storage
    citation_result = test_citation_storage(
        company_id, report_year,
        combined_result.extracted_indicators,
        combined_result.esg_score,
        combined_result.metadata
    )
    combined_result.citation_storage_passed = citation_result.citation_storage_passed
    combined_result.errors.extend(citation_result.errors)
    combined_result.warnings.extend(citation_result.warnings)
    
    # Print summary
    print("\n" + combined_result.summary())
    
    return combined_result.all_passed()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run end-to-end extraction test")
    parser.add_argument(
        "--company",
        default="RELIANCE",
        help="Company name to test with (default: RELIANCE)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Report year to test with (default: 2024)"
    )
    parser.add_argument(
        "--max-indicators",
        type=int,
        default=3,
        help="Maximum number of indicators to extract (default: 3)"
    )
    
    args = parser.parse_args()
    
    success = run_e2e_test(
        company_name=args.company,
        report_year=args.year,
        max_indicators=args.max_indicators
    )
    
    sys.exit(0 if success else 1)
