"""Structural validation test for FilteredPGVectorRetriever."""

import sys
import logging
from src.retrieval.filtered_retriever import FilteredPGVectorRetriever

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_class_structure():
    """Test that the FilteredPGVectorRetriever class has the required structure."""
    
    logger.info("Testing FilteredPGVectorRetriever class structure...")
    
    # Check class exists
    assert FilteredPGVectorRetriever is not None, "Class should exist"
    logger.info("✓ Class exists")
    
    # Check __init__ method
    assert hasattr(FilteredPGVectorRetriever, '__init__'), "__init__ method should exist"
    logger.info("✓ __init__ method exists")
    
    # Check get_relevant_documents method
    assert hasattr(FilteredPGVectorRetriever, 'get_relevant_documents'), \
        "get_relevant_documents method should exist"
    logger.info("✓ get_relevant_documents method exists")
    
    # Check get_relevant_documents_with_scores method
    assert hasattr(FilteredPGVectorRetriever, 'get_relevant_documents_with_scores'), \
        "get_relevant_documents_with_scores method should exist"
    logger.info("✓ get_relevant_documents_with_scores method exists")
    
    # Check method signatures
    import inspect
    
    # Check __init__ signature
    init_sig = inspect.signature(FilteredPGVectorRetriever.__init__)
    init_params = list(init_sig.parameters.keys())
    assert 'connection_string' in init_params, "connection_string parameter should exist"
    assert 'company_name' in init_params, "company_name parameter should exist"
    assert 'report_year' in init_params, "report_year parameter should exist"
    logger.info("✓ __init__ has correct parameters")
    
    # Check get_relevant_documents signature
    get_docs_sig = inspect.signature(FilteredPGVectorRetriever.get_relevant_documents)
    get_docs_params = list(get_docs_sig.parameters.keys())
    assert 'query' in get_docs_params, "query parameter should exist"
    assert 'k' in get_docs_params, "k parameter should exist"
    logger.info("✓ get_relevant_documents has correct parameters")
    
    # Check return type annotations
    get_docs_return = get_docs_sig.return_annotation
    assert 'List' in str(get_docs_return), "Should return List type"
    logger.info("✓ get_relevant_documents has correct return type annotation")
    
    logger.info("\n✓ All structural tests passed!")
    return True


def test_imports():
    """Test that all required imports are available."""
    
    logger.info("Testing imports...")
    
    try:
        from langchain_core.documents import Document
        logger.info("✓ langchain_core.documents.Document imported")
        
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        logger.info("✓ langchain_google_genai.GoogleGenerativeAIEmbeddings imported")
        
        import psycopg2
        from psycopg2.extras import RealDictCursor
        logger.info("✓ psycopg2 and RealDictCursor imported")
        
        logger.info("\n✓ All imports successful!")
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


if __name__ == "__main__":
    try:
        imports_ok = test_imports()
        structure_ok = test_class_structure()
        
        if imports_ok and structure_ok:
            logger.info("\n" + "="*50)
            logger.info("ALL TESTS PASSED ✓")
            logger.info("="*50)
            sys.exit(0)
        else:
            logger.error("\n" + "="*50)
            logger.error("SOME TESTS FAILED ✗")
            logger.error("="*50)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)
