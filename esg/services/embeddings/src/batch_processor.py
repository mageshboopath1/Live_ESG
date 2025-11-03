"""
Batch processor for embeddings - processes multiple documents without queue.
Used by Airflow DAG instead of queue-based consumer.
"""

import os
import sys
import logging
from typing import List

from extractor import process_download
from splitter import pages_to_chunks
from embedder import generate_embeddings
from db import store_embeddings
from config import logger

def process_document(object_key: str) -> bool:
    """
    Process a single document: extract, chunk, embed, store.
    
    Args:
        object_key: MinIO object key (e.g., "RELIANCE/2024_BRSR.pdf")
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Processing document: {object_key}")
        
        # Step 1: Extract text from PDF
        logger.info(f"Extracting text from {object_key}")
        pages = process_download(object_key)
        
        if not pages:
            logger.error(f"No pages extracted from {object_key}")
            return False
        
        logger.info(f"Extracted {len(pages)} pages from {object_key}")
        
        # Step 2: Split into chunks
        logger.info(f"Splitting {object_key} into chunks")
        chunks = pages_to_chunks(pages, object_key)
        
        if not chunks:
            logger.error(f"No chunks created from {object_key}")
            return False
        
        logger.info(f"Created {len(chunks)} chunks from {object_key}")
        
        # Step 3: Generate embeddings
        logger.info(f"Generating embeddings for {object_key}")
        embeddings = generate_embeddings(chunks)
        
        if not embeddings:
            logger.error(f"No embeddings generated for {object_key}")
            return False
        
        logger.info(f"Generated {len(embeddings)} embeddings for {object_key}")
        
        # Step 4: Store in database
        logger.info(f"Storing embeddings for {object_key}")
        store_embeddings(embeddings)
        
        logger.info(f"✓ Successfully processed {object_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {object_key}: {e}", exc_info=True)
        return False


def main():
    """
    Main entry point for batch processing.
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
    
    logger.info(f"Starting batch processing for {len(documents)} documents")
    
    # Process each document
    success_count = 0
    failed_count = 0
    
    for doc in documents:
        if process_document(doc):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    logger.info(f"Batch processing complete: {success_count} succeeded, {failed_count} failed")
    
    # Exit with error if any failed
    if failed_count > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
