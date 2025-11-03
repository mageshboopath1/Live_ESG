"""
Example usage of extract_indicators_batch function.

This script demonstrates how to use the batch extraction function
to process all BRSR Core indicators for a company's sustainability report.

Note: This is a demonstration script. For actual usage, ensure:
1. PostgreSQL is running with pgvector extension
2. Document embeddings are generated and stored
3. BRSR indicators are seeded in the database
4. Valid Google API key is configured
"""

import logging
from src.config import config
from src.extraction.extractor import extract_indicators_batch
from src.db.repository import store_extracted_indicators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Example: Extract all BRSR indicators for a company report.
    """
    # Document to process
    object_key = "RELIANCE/2024_BRSR.pdf"
    
    logger.info(f"Starting batch extraction for: {object_key}")
    
    try:
        # Extract all indicators in batches
        # The function will:
        # 1. Parse object_key to get company and year
        # 2. Load all BRSR indicator definitions
        # 3. Group indicators by attribute (1-9)
        # 4. Process each attribute batch
        # 5. Handle failures gracefully
        extracted_indicators = extract_indicators_batch(
            object_key=object_key,
            connection_string=config.database_url,
            google_api_key=config.google_api_key,
            k=10,  # Retrieve 10 chunks per indicator
            model_name="gemini-2.5-flash",
            temperature=0.1,
        )
        
        logger.info(f"Extraction complete: {len(extracted_indicators)} indicators extracted")
        
        # Display summary statistics
        high_confidence = [ind for ind in extracted_indicators if ind.confidence_score >= 0.8]
        medium_confidence = [ind for ind in extracted_indicators if 0.5 <= ind.confidence_score < 0.8]
        low_confidence = [ind for ind in extracted_indicators if ind.confidence_score < 0.5]
        
        logger.info(f"Confidence distribution:")
        logger.info(f"  High (≥0.8): {len(high_confidence)} indicators")
        logger.info(f"  Medium (0.5-0.8): {len(medium_confidence)} indicators")
        logger.info(f"  Low (<0.5): {len(low_confidence)} indicators")
        
        # Store extracted indicators in database
        if extracted_indicators:
            logger.info("Storing extracted indicators in database...")
            stored_count = store_extracted_indicators(extracted_indicators)
            logger.info(f"Successfully stored {stored_count} indicators")
        else:
            logger.warning("No indicators extracted - nothing to store")
        
        # Display sample results
        if extracted_indicators:
            logger.info("\nSample extracted indicators:")
            for ind in extracted_indicators[:5]:  # Show first 5
                logger.info(
                    f"  - Indicator ID {ind.indicator_id}: "
                    f"value='{ind.extracted_value}', "
                    f"confidence={ind.confidence_score:.2f}, "
                    f"pages={ind.source_pages}"
                )
        
        return extracted_indicators
        
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}", exc_info=True)
        raise


def extract_specific_attributes():
    """
    Example: Extract indicators for specific BRSR attributes only.
    """
    from src.db.repository import get_indicators_by_attribute
    
    object_key = "RELIANCE/2024_BRSR.pdf"
    
    # Extract only Environmental indicators (attributes 1-3)
    environmental_attributes = [1, 2, 3]  # GHG, Water, Energy
    
    logger.info(f"Extracting environmental indicators for: {object_key}")
    
    # Load indicators for specific attributes
    indicators = []
    for attr_num in environmental_attributes:
        attr_indicators = get_indicators_by_attribute(attr_num)
        indicators.extend(attr_indicators)
        logger.info(f"Loaded {len(attr_indicators)} indicators for attribute {attr_num}")
    
    # Extract only these indicators
    extracted_indicators = extract_indicators_batch(
        object_key=object_key,
        connection_string=config.database_url,
        google_api_key=config.google_api_key,
        indicators=indicators,  # Pass specific indicators
        k=10,
    )
    
    logger.info(
        f"Extracted {len(extracted_indicators)} environmental indicators "
        f"from {len(indicators)} total"
    )
    
    return extracted_indicators


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("BATCH EXTRACTION EXAMPLE")
    print("=" * 80)
    print("\nThis script demonstrates batch extraction usage.")
    print("Ensure database and API are configured before running.")
    print("=" * 80 + "\n")
    
    # Example 1: Extract all indicators
    print("Example 1: Extract all BRSR indicators")
    print("-" * 80)
    # Uncomment to run:
    # results = main()
    print("(Commented out - uncomment main() to run with real database)")
    
    print("\n" + "=" * 80)
    print("Example 2: Extract specific attributes only")
    print("-" * 80)
    # Uncomment to run:
    # results = extract_specific_attributes()
    print("(Commented out - uncomment to run with real database)")
    
    print("\n" + "=" * 80)
    print("USAGE NOTES")
    print("=" * 80)
    print("""
Key features of extract_indicators_batch:

1. Automatic grouping by BRSR attribute (1-9)
   - Processes related indicators together
   - Reduces redundant vector searches

2. Graceful error handling
   - Individual indicator failures don't stop the batch
   - All errors are logged with full details
   - Returns partial results

3. Flexible indicator selection
   - Pass indicators=None to extract all BRSR indicators
   - Pass specific list to extract subset

4. Atomic database storage
   - All indicators stored in single transaction
   - ON CONFLICT handling for idempotency

5. Comprehensive logging
   - Progress tracking per attribute
   - Success/failure statistics
   - Confidence score distribution
    """)
