"""
Batch extractor for BRSR indicators - processes multiple documents without queue.
Used by Airflow DAG instead of queue-based consumer.
"""

import os
import sys
import logging
from typing import List

# Import from main.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import process_extraction_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for batch extraction.
    Reads DOCUMENTS env var (comma-separated list of object keys).
    """
    # Get documents from environment variable
    documents_str = os.getenv('DOCUMENTS', '')
    
    if not documents_str:
        logger.error("No DOCUMENTS environment variable provided")
        sys.exit(1)
    
    # Parse comma-separated list
    documents = [doc.strip() for doc in documents_str.split(',') if doc.strip()]
    
    if not documents:
        logger.error("DOCUMENTS environment variable is empty")
        sys.exit(1)
    
    logger.info(f"Starting batch extraction for {len(documents)} documents")
    
    # Process each document
    success_count = 0
    failed_count = 0
    
    for doc in documents:
        logger.info(f"Processing document {success_count + failed_count + 1}/{len(documents)}: {doc}")
        
        if process_extraction_task(doc):
            success_count += 1
            logger.info(f"✓ Successfully processed {doc}")
        else:
            failed_count += 1
            logger.error(f"✗ Failed to process {doc}")
    
    # Summary
    logger.info(f"Batch extraction complete: {success_count} succeeded, {failed_count} failed")
    
    # Exit with error if any failed
    if failed_count > 0:
        logger.error(f"Batch extraction had {failed_count} failures")
        sys.exit(1)
    
    logger.info("✓ All documents processed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
