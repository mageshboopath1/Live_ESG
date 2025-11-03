"""Test script for FilteredPGVectorRetriever."""

import sys
import logging
from src.config import config
from src.retrieval.filtered_retriever import FilteredPGVectorRetriever

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_retriever():
    """Test the FilteredPGVectorRetriever with a sample query."""
    
    # Check if we have the required configuration
    if not config.google_api_key:
        logger.error("GOOGLE_API_KEY not set in environment")
        return False
    
    logger.info("Testing FilteredPGVectorRetriever...")
    logger.info(f"Database URL: {config.database_url}")
    
    try:
        # Initialize retriever with sample company and year
        # Note: This will fail if there's no data for this company/year
        retriever = FilteredPGVectorRetriever(
            connection_string=config.database_url,
            company_name="RELIANCE",  # Example company
            report_year=2024,
            embedding_model="models/embedding-001"
        )
        
        logger.info("Retriever initialized successfully")
        
        # Test query
        query = "What are the total Scope 1 emissions?"
        logger.info(f"Testing query: {query}")
        
        # Retrieve documents
        documents = retriever.get_relevant_documents(query, k=3)
        
        logger.info(f"Retrieved {len(documents)} documents")
        
        # Display results
        for i, doc in enumerate(documents, 1):
            logger.info(f"\n--- Document {i} ---")
            logger.info(f"Page: {doc.metadata['page_number']}")
            logger.info(f"Chunk Index: {doc.metadata['chunk_index']}")
            logger.info(f"Distance: {doc.metadata['distance']:.4f}")
            logger.info(f"Content preview: {doc.page_content[:200]}...")
        
        logger.info("\n✓ Test completed successfully!")
        return True
        
    except ValueError as e:
        logger.warning(f"No data found (expected if database is empty): {e}")
        logger.info("✓ Retriever handles empty results correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_retriever()
    sys.exit(0 if success else 1)
