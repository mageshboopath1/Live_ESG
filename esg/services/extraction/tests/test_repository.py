"""
Test script for database repository functions.

This script tests the core repository functions to ensure they work correctly
with the database schema.
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.db.repository import (
    load_brsr_indicators,
    parse_object_key,
    check_document_processed,
    get_company_id_by_name,
    get_indicator_id_by_code,
    get_indicators_by_attribute,
    store_esg_score,
    get_score_breakdown,
    get_scores_by_company_and_year,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_parse_object_key():
    """Test object key parsing."""
    logger.info("Testing parse_object_key...")
    
    # Valid cases
    test_cases = [
        ("RELIANCE/2024_BRSR.pdf", ("RELIANCE", 2024)),
        ("TCS/2023_Annual_Report.pdf", ("TCS", 2023)),
        ("HDFC_BANK/2022_Sustainability.pdf", ("HDFC_BANK", 2022)),
    ]
    
    for object_key, expected in test_cases:
        try:
            result = parse_object_key(object_key)
            assert result == expected, f"Expected {expected}, got {result}"
            logger.info(f"✓ Parsed '{object_key}' -> {result}")
        except Exception as e:
            logger.error(f"✗ Failed to parse '{object_key}': {e}")
            return False
    
    # Invalid cases
    invalid_cases = [
        "invalid_format.pdf",
        "RELIANCE/BRSR.pdf",
        "2024_BRSR.pdf",
    ]
    
    for object_key in invalid_cases:
        try:
            result = parse_object_key(object_key)
            logger.error(f"✗ Should have failed for '{object_key}' but got {result}")
            return False
        except ValueError:
            logger.info(f"✓ Correctly rejected invalid format: '{object_key}'")
    
    return True


def test_load_brsr_indicators():
    """Test loading BRSR indicators from database."""
    logger.info("Testing load_brsr_indicators...")
    
    try:
        indicators = load_brsr_indicators()
        
        if not indicators:
            logger.warning("⚠ No indicators found in database (may be expected if not seeded)")
            return True
        
        logger.info(f"✓ Loaded {len(indicators)} indicators")
        
        # Verify structure of first indicator
        first = indicators[0]
        logger.info(f"  Sample: {first.indicator_code} - {first.parameter_name}")
        logger.info(f"  Attribute: {first.attribute_number}, Pillar: {first.pillar}")
        
        # Verify all have required fields
        for ind in indicators:
            assert ind.indicator_code, "Missing indicator_code"
            assert 1 <= ind.attribute_number <= 9, "Invalid attribute_number"
            assert ind.pillar in ["E", "S", "G"], "Invalid pillar"
            assert 0.0 <= ind.weight <= 1.0, "Invalid weight"
        
        logger.info("✓ All indicators have valid structure")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to load indicators: {e}")
        return False


def test_get_indicators_by_attribute():
    """Test loading indicators by attribute number."""
    logger.info("Testing get_indicators_by_attribute...")
    
    try:
        # Test valid attribute
        indicators = get_indicators_by_attribute(1)
        logger.info(f"✓ Loaded {len(indicators)} indicators for attribute 1")
        
        # Verify all have correct attribute
        for ind in indicators:
            assert ind.attribute_number == 1, f"Wrong attribute: {ind.attribute_number}"
        
        logger.info("✓ All indicators have correct attribute number")
        
        # Test invalid attribute
        try:
            get_indicators_by_attribute(10)
            logger.error("✗ Should have failed for invalid attribute 10")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected invalid attribute number")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to load indicators by attribute: {e}")
        return False


def test_check_document_processed():
    """Test checking if document is processed."""
    logger.info("Testing check_document_processed...")
    
    try:
        # Test with a document that likely doesn't exist
        test_key = "TEST_COMPANY/2024_TEST.pdf"
        is_processed = check_document_processed(test_key)
        logger.info(f"✓ Document '{test_key}' processed: {is_processed}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to check document status: {e}")
        return False


def test_get_company_id():
    """Test getting company ID by name."""
    logger.info("Testing get_company_id_by_name...")
    
    try:
        # Try to get a company (may not exist if catalog not populated)
        company_id = get_company_id_by_name("RELIANCE")
        
        if company_id:
            logger.info(f"✓ Found company ID for RELIANCE: {company_id}")
        else:
            logger.warning("⚠ Company RELIANCE not found (may be expected if catalog not populated)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to get company ID: {e}")
        return False


def test_store_esg_score():
    """Test storing ESG scores."""
    logger.info("Testing store_esg_score...")
    
    try:
        # Get a company ID (use 1 as test, or skip if not available)
        company_id = get_company_id_by_name("RELIANCE")
        if not company_id:
            logger.warning("⚠ Skipping test - no company found in catalog")
            return True
        
        # Create test calculation metadata
        calculation_metadata = {
            "pillar_scores": {
                "environmental": 65.5,
                "social": 72.3,
                "governance": 68.9,
            },
            "pillar_weights": {
                "environmental": 0.33,
                "social": 0.33,
                "governance": 0.34,
            },
            "pillar_breakdown": {
                "E": {
                    "score": 65.5,
                    "indicators": [
                        {
                            "code": "GHG_SCOPE1_TOTAL",
                            "name": "Total Scope 1 emissions",
                            "value": 1250.0,
                            "unit": "MT CO2e",
                            "normalized": 60.0,
                            "weight": 1.0,
                            "contribution": 60.0,
                        }
                    ],
                    "total_weight": 1.0,
                }
            },
            "calculation_method": "Test calculation",
            "calculated_at": "2024-01-01T00:00:00Z",
            "total_indicators_extracted": 10,
        }
        
        # Store score
        score_id = store_esg_score(
            company_id=company_id,
            report_year=2024,
            environmental_score=65.5,
            social_score=72.3,
            governance_score=68.9,
            overall_score=68.9,
            calculation_metadata=calculation_metadata,
        )
        
        logger.info(f"✓ Stored ESG score with ID: {score_id}")
        
        # Verify we can retrieve it
        breakdown = get_score_breakdown(company_id, 2024)
        if breakdown:
            logger.info(f"✓ Retrieved score breakdown: overall={breakdown['overall_score']}")
            assert breakdown['overall_score'] == 68.9, "Score mismatch"
            assert breakdown['environmental_score'] == 65.5, "Environmental score mismatch"
            logger.info("✓ Score values match")
        else:
            logger.error("✗ Failed to retrieve stored score")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to store ESG score: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_score_breakdown():
    """Test retrieving score breakdown."""
    logger.info("Testing get_score_breakdown...")
    
    try:
        # Get a company ID
        company_id = get_company_id_by_name("RELIANCE")
        if not company_id:
            logger.warning("⚠ Skipping test - no company found in catalog")
            return True
        
        # Try to get breakdown (may not exist)
        breakdown = get_score_breakdown(company_id, 2024)
        
        if breakdown:
            logger.info(f"✓ Retrieved breakdown for company {company_id}, year 2024")
            logger.info(f"  Overall score: {breakdown['overall_score']}")
            logger.info(f"  Environmental: {breakdown['environmental_score']}")
            logger.info(f"  Social: {breakdown['social_score']}")
            logger.info(f"  Governance: {breakdown['governance_score']}")
            
            # Verify structure
            assert 'calculation_metadata' in breakdown, "Missing calculation_metadata"
            assert 'calculated_at' in breakdown, "Missing calculated_at"
            logger.info("✓ Breakdown has correct structure")
        else:
            logger.warning("⚠ No score found for company (may be expected)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to get score breakdown: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_scores_by_company_and_year():
    """Test retrieving scores by company and year."""
    logger.info("Testing get_scores_by_company_and_year...")
    
    try:
        # Get a company ID
        company_id = get_company_id_by_name("RELIANCE")
        if not company_id:
            logger.warning("⚠ Skipping test - no company found in catalog")
            return True
        
        # Get all scores for company
        all_scores = get_scores_by_company_and_year(company_id)
        logger.info(f"✓ Retrieved {len(all_scores)} score(s) for company {company_id}")
        
        if all_scores:
            for score in all_scores:
                logger.info(
                    f"  Year {score['report_year']}: "
                    f"Overall={score['overall_score']}"
                )
        
        # Get score for specific year
        year_scores = get_scores_by_company_and_year(company_id, 2024)
        logger.info(f"✓ Retrieved {len(year_scores)} score(s) for year 2024")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to get scores by company and year: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Testing Database Repository Functions")
    logger.info("=" * 60)
    
    tests = [
        ("Parse Object Key", test_parse_object_key),
        ("Load BRSR Indicators", test_load_brsr_indicators),
        ("Get Indicators by Attribute", test_get_indicators_by_attribute),
        ("Check Document Processed", test_check_document_processed),
        ("Get Company ID", test_get_company_id),
        ("Store ESG Score", test_store_esg_score),
        ("Get Score Breakdown", test_get_score_breakdown),
        ("Get Scores by Company and Year", test_get_scores_by_company_and_year),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info("")
        logger.info(f"Running: {name}")
        logger.info("-" * 60)
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
