#!/usr/bin/env python3
"""
Trigger extraction for existing documents in the database.
This sends extraction tasks to RabbitMQ for documents that have embeddings but no extractions.
"""

import os
import sys
import json
import time
import argparse
import pika
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "moz"),
    "user": os.getenv("DB_USER", "drfitz"),
    "password": os.getenv("DB_PASSWORD", "h4i1hydr4")
}

RABBITMQ_CONFIG = {
    "host": os.getenv("RABBITMQ_HOST", "localhost"),
    "port": int(os.getenv("RABBITMQ_PORT", "5672")),
    "user": os.getenv("RABBITMQ_USER", "esg_rabbitmq"),
    "password": os.getenv("RABBITMQ_PASSWORD", "esg_secret"),
}

EXTRACTION_QUEUE = os.getenv("EXTRACTION_QUEUE_NAME", "extraction-tasks")


def get_documents_needing_extraction(conn, limit=10):
    """
    Get documents that have embeddings but no extractions.
    
    Args:
        conn: Database connection
        limit: Maximum number of documents to return
        
    Returns:
        List of document records with object_key, company_id, etc.
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get documents with embeddings but no extractions
    cur.execute("""
        SELECT DISTINCT 
            de.object_key,
            cc.id as company_id,
            cc.company_name,
            cc.symbol,
            de.report_year,
            COUNT(DISTINCT de.id) as embedding_count
        FROM document_embeddings de
        JOIN company_catalog cc ON de.company_name = cc.symbol
        WHERE NOT EXISTS (
            SELECT 1 FROM extracted_indicators ei 
            WHERE ei.object_key = de.object_key
        )
        GROUP BY de.object_key, cc.id, cc.company_name, cc.symbol, de.report_year
        ORDER BY cc.company_name, de.report_year
        LIMIT %s
    """, (limit,))
    
    documents = cur.fetchall()
    cur.close()
    return documents


def send_extraction_task(channel, document, max_retries=3):
    """
    Send an extraction task to RabbitMQ.
    
    Args:
        channel: RabbitMQ channel
        document: Document record with object_key, company_id, etc.
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if message was published successfully, False otherwise
    """
    task = {
        "object_key": document['object_key'],
        "company_id": document['company_id'],
        "company_name": document['company_name'],
        "report_year": document['report_year']
    }
    
    for attempt in range(max_retries):
        try:
            channel.basic_publish(
                exchange='',
                routing_key=EXTRACTION_QUEUE,
                body=json.dumps(task),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    ⚠️  Retry {attempt + 1}/{max_retries - 1} after error: {e}")
                time.sleep(1)  # Wait before retry
            else:
                print(f"    ✗ Failed to publish after {max_retries} attempts: {e}")
                return False
    
    return False


def print_document_table(documents):
    """Print a formatted table of documents."""
    print("\n" + "=" * 90)
    print(f"{'#':<4} {'Symbol':<12} {'Company':<25} {'Year':<6} {'Embeddings':<12} {'Object Key':<20}")
    print("=" * 90)
    for i, doc in enumerate(documents, 1):
        symbol = doc['symbol'][:11] if len(doc['symbol']) > 11 else doc['symbol']
        company = doc['company_name'][:24] if len(doc['company_name']) > 24 else doc['company_name']
        object_key = doc['object_key'][:19] if len(doc['object_key']) > 19 else doc['object_key']
        print(f"{i:<4} {symbol:<12} {company:<25} {doc['report_year']:<6} {doc['embedding_count']:<12} {object_key:<20}")
    print("=" * 90)


def validate_queue_exists(channel, queue_name):
    """
    Validate that a queue exists.
    
    Args:
        channel: RabbitMQ channel
        queue_name: Name of the queue to check
        
    Returns:
        True if queue exists, False otherwise
    """
    try:
        # Passive declare - checks if queue exists without creating it
        channel.queue_declare(queue=queue_name, passive=True)
        return True
    except Exception as e:
        print(f"✗ Queue '{queue_name}' does not exist or is not accessible: {e}")
        return False


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Trigger extraction for documents with embeddings but no extractions.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Queue 10 documents (default)
  python trigger_extraction.py
  
  # Queue 5 documents
  python trigger_extraction.py --limit 5
  
  # Preview without queuing
  python trigger_extraction.py --dry-run
  
  # Preview 20 documents
  python trigger_extraction.py --limit 20 --dry-run
        """
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of documents to queue (default: 10)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview documents without queuing them'
    )
    
    return parser.parse_args()


def main():
    """Main execution."""
    args = parse_arguments()
    
    print("=" * 70)
    print("Triggering Extraction for Existing Documents")
    print("=" * 70)
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No messages will be queued")
    
    try:
        # Connect to database
        print("\n📊 Connecting to database...")
        db_conn = psycopg2.connect(**DB_CONFIG)
        print(f"✓ Connected to database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
        
        # Get documents needing extraction
        print(f"\n🔍 Finding documents needing extraction (limit: {args.limit})...")
        documents = get_documents_needing_extraction(db_conn, limit=args.limit)
        
        if not documents:
            print("✓ No documents need extraction (all documents already processed)")
            db_conn.close()
            return
        
        print(f"✓ Found {len(documents)} documents needing extraction")
        
        # Display document table
        print_document_table(documents)
        
        if args.dry_run:
            print("\n🔍 DRY RUN - These documents would be queued for extraction")
            print("Run without --dry-run to actually queue them")
            db_conn.close()
            return
        
        # Connect to RabbitMQ
        print("\n🐰 Connecting to RabbitMQ...")
        try:
            credentials = pika.PlainCredentials(
                RABBITMQ_CONFIG['user'],
                RABBITMQ_CONFIG['password']
            )
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_CONFIG['host'],
                port=RABBITMQ_CONFIG['port'],
                credentials=credentials,
                connection_attempts=3,
                retry_delay=2
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            print(f"✓ Connected to RabbitMQ: {RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}")
        except Exception as e:
            print(f"✗ Failed to connect to RabbitMQ: {e}")
            print("\nTroubleshooting:")
            print("  1. Check RabbitMQ is running: docker ps | grep rabbitmq")
            print("  2. Check connection settings in environment variables")
            print("  3. Verify credentials are correct")
            db_conn.close()
            sys.exit(1)
        
        # Validate queue exists
        print(f"\n🔍 Validating queue '{EXTRACTION_QUEUE}'...")
        if not validate_queue_exists(channel, EXTRACTION_QUEUE):
            print("\nTroubleshooting:")
            print("  1. Check extraction service is running: docker ps | grep extraction")
            print("  2. Check extraction service logs: docker logs esg-extraction")
            print("  3. Verify queue name in environment variables")
            connection.close()
            db_conn.close()
            sys.exit(1)
        print(f"✓ Queue '{EXTRACTION_QUEUE}' exists and is accessible")
        
        # Send extraction tasks
        print(f"\n📤 Sending {len(documents)} extraction tasks...")
        successful = 0
        failed = 0
        
        for i, doc in enumerate(documents, 1):
            print(f"  {i}. {doc['symbol']} ({doc['report_year']}) - {doc['embedding_count']} embeddings")
            if send_extraction_task(channel, doc):
                print(f"     ✓ Queued: {doc['object_key']}")
                successful += 1
            else:
                print(f"     ✗ Failed: {doc['object_key']}")
                failed += 1
        
        connection.close()
        db_conn.close()
        
        print("\n" + "=" * 70)
        print(f"✓ Successfully queued {successful} extraction tasks!")
        if failed > 0:
            print(f"⚠️  Failed to queue {failed} tasks")
        print("=" * 70)
        print("\nThe extraction service will now process these documents.")
        print("Monitor progress with:")
        print("  docker logs -f esg-extraction")
        print("\nCheck queue status with:")
        print("  docker exec rabbitmq rabbitmqctl list_queues name messages consumers")
        
    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check database is running: docker ps | grep postgres")
        print("  2. Check connection settings in environment variables")
        print("  3. Verify database credentials are correct")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
