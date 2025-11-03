#!/usr/bin/env python3
"""
Comprehensive cleanup script for ESG pipeline data.
Removes all data from MinIO, PostgreSQL, and RabbitMQ to enable fresh pipeline testing.
"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Tuple

# Import centralized configuration
try:
    from pipeline_config import get_config
    USE_CENTRALIZED_CONFIG = True
except ImportError:
    USE_CENTRALIZED_CONFIG = False
    print("Warning: pipeline_config not found, using legacy configuration")


# ============================================================================
# Configuration
# ============================================================================

if USE_CENTRALIZED_CONFIG:
    _config = get_config()
    DB_CONFIG = _config.database.connection_dict
    MINIO_CONFIG = {
        "endpoint": _config.minio.endpoint,
        "access_key": _config.minio.access_key,
        "secret_key": _config.minio.secret_key,
        "bucket": _config.minio.bucket,
        "secure": _config.minio.secure
    }
    RABBITMQ_CONFIG = {
        "host": _config.rabbitmq.host,
        "port": _config.rabbitmq.port,
        "user": _config.rabbitmq.user,
        "password": _config.rabbitmq.password,
        "embedding_queue": _config.rabbitmq.embedding_queue,
        "extraction_queue": _config.rabbitmq.extraction_queue
    }
else:
    # Legacy configuration fallback
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "moz"),
        "user": os.getenv("DB_USER", "drfitz"),
        "password": os.getenv("DB_PASSWORD", "h4i1hydr4")
    }

    MINIO_CONFIG = {
        "endpoint": os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "esg_minio"),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "esg_secret"),
        "bucket": os.getenv("BUCKET_NAME", "esg-reports"),
        "secure": os.getenv("MINIO_SECURE", "false").lower() == "true"
    }

    RABBITMQ_CONFIG = {
        "host": os.getenv("RABBITMQ_HOST", "localhost"),
        "port": int(os.getenv("RABBITMQ_PORT", "5672")),
        "user": os.getenv("RABBITMQ_DEFAULT_USER", "esg_rabbitmq"),
        "password": os.getenv("RABBITMQ_DEFAULT_PASS", "esg_secret"),
        "embedding_queue": os.getenv("QUEUE_NAME", "embedding-tasks"),
        "extraction_queue": os.getenv("EXTRACTION_QUEUE_NAME", "extraction-tasks")
    }


# ============================================================================
# MinIO Cleanup Functions (Task 4.1)
# ============================================================================

def cleanup_minio_storage() -> int:
    """
    Delete all objects from MinIO esg-reports bucket.
    
    Returns:
        int: Count of deleted objects
    
    Raises:
        Exception: If MinIO connection or deletion fails
    """
    try:
        # Parse endpoint URL
        endpoint_url = MINIO_CONFIG["endpoint"]
        
        # Create boto3 S3 client for MinIO
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=MINIO_CONFIG["access_key"],
            aws_secret_access_key=MINIO_CONFIG["secret_key"],
            use_ssl=MINIO_CONFIG["secure"]
        )
        
        bucket_name = MINIO_CONFIG["bucket"]
        deleted_count = 0
        
        # List all objects in the bucket
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                # Prepare objects for deletion
                objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                
                # Delete objects in batch
                if objects_to_delete:
                    response = s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                    deleted_count += len(response.get('Deleted', []))
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                print(f"  ⚠️  Bucket '{bucket_name}' does not exist")
                return 0
            raise
        
        return deleted_count
    
    except Exception as e:
        raise Exception(f"MinIO cleanup failed: {e}")


# ============================================================================
# Database Cleanup Functions (Task 4.2)
# ============================================================================

def cleanup_database_tables(conn) -> Dict[str, int]:
    """
    Delete all records from pipeline tables in correct order.
    Respects foreign key constraints by deleting in dependency order.
    
    Args:
        conn: psycopg2 database connection
    
    Returns:
        dict: Counts of deleted records per table
    
    Raises:
        Exception: If database operations fail
    """
    cur = conn.cursor()
    deleted_counts = {}
    
    try:
        # Start transaction
        cur.execute("BEGIN")
        
        # Delete in order to respect foreign key constraints:
        # 1. esg_scores (references company_catalog)
        # 2. extracted_indicators (references company_catalog, brsr_indicators)
        # 3. document_embeddings (no foreign keys)
        # 4. ingestion_metadata (references company_catalog)
        # 5. company_catalog (referenced by others, delete last if needed)
        
        # Delete esg_scores
        cur.execute("DELETE FROM esg_scores")
        deleted_counts['esg_scores'] = cur.rowcount
        
        # Delete extracted_indicators
        cur.execute("DELETE FROM extracted_indicators")
        deleted_counts['extracted_indicators'] = cur.rowcount
        
        # Delete document_embeddings
        cur.execute("DELETE FROM document_embeddings")
        deleted_counts['document_embeddings'] = cur.rowcount
        
        # Delete ingestion_metadata
        cur.execute("DELETE FROM ingestion_metadata")
        deleted_counts['ingestion_metadata'] = cur.rowcount
        
        # Optionally delete company_catalog (commented out to preserve company data)
        # cur.execute("DELETE FROM company_catalog")
        # deleted_counts['company_catalog'] = cur.rowcount
        
        # Commit transaction
        cur.execute("COMMIT")
        
        cur.close()
        return deleted_counts
    
    except Exception as e:
        # Rollback on error
        try:
            cur.execute("ROLLBACK")
        except:
            pass
        cur.close()
        raise Exception(f"Database cleanup failed: {e}")


# ============================================================================
# RabbitMQ Cleanup Functions (Task 4.3)
# ============================================================================

def cleanup_rabbitmq_queues() -> Dict[str, int]:
    """
    Purge all messages from RabbitMQ queues.
    
    Returns:
        dict: Count of purged messages per queue
    
    Raises:
        Exception: If RabbitMQ connection or purge fails
    """
    try:
        # Create connection credentials
        credentials = pika.PlainCredentials(
            RABBITMQ_CONFIG["user"],
            RABBITMQ_CONFIG["password"]
        )
        
        # Create connection parameters
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_CONFIG["host"],
            port=RABBITMQ_CONFIG["port"],
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        purged_counts = {}
        
        # Purge embedding-tasks queue
        embedding_queue = RABBITMQ_CONFIG["embedding_queue"]
        try:
            method = channel.queue_purge(embedding_queue)
            purged_counts[embedding_queue] = method.method.message_count
        except Exception as e:
            print(f"  ⚠️  Could not purge queue '{embedding_queue}': {e}")
            purged_counts[embedding_queue] = 0
        
        # Purge extraction-tasks queue
        extraction_queue = RABBITMQ_CONFIG["extraction_queue"]
        try:
            method = channel.queue_purge(extraction_queue)
            purged_counts[extraction_queue] = method.method.message_count
        except Exception as e:
            print(f"  ⚠️  Could not purge queue '{extraction_queue}': {e}")
            purged_counts[extraction_queue] = 0
        
        # Close connection
        connection.close()
        
        return purged_counts
    
    except Exception as e:
        raise Exception(f"RabbitMQ cleanup failed: {e}")


# ============================================================================
# Main Cleanup Orchestration (Task 4.4)
# ============================================================================

def get_current_data_summary(conn) -> Dict[str, int]:
    """
    Get counts of existing data before cleanup.
    
    Args:
        conn: psycopg2 database connection
    
    Returns:
        dict: Counts of records per table
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    counts = {}
    
    tables = [
        'document_embeddings',
        'extracted_indicators',
        'esg_scores',
        'ingestion_metadata',
        'company_catalog'
    ]
    
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            counts[table] = cur.fetchone()['count']
        except Exception as e:
            print(f"  ⚠️  Could not count {table}: {e}")
            counts[table] = 0
    
    cur.close()
    return counts


def get_minio_object_count() -> int:
    """
    Get count of objects in MinIO bucket.
    
    Returns:
        int: Count of objects
    """
    try:
        endpoint_url = MINIO_CONFIG["endpoint"]
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=MINIO_CONFIG["access_key"],
            aws_secret_access_key=MINIO_CONFIG["secret_key"],
            use_ssl=MINIO_CONFIG["secure"]
        )
        
        bucket_name = MINIO_CONFIG["bucket"]
        count = 0
        
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        
        for page in pages:
            if 'Contents' in page:
                count += len(page['Contents'])
        
        return count
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            return 0
        raise
    except Exception:
        return 0


def get_rabbitmq_message_counts() -> Dict[str, int]:
    """
    Get counts of messages in RabbitMQ queues.
    
    Returns:
        dict: Message counts per queue
    """
    try:
        credentials = pika.PlainCredentials(
            RABBITMQ_CONFIG["user"],
            RABBITMQ_CONFIG["password"]
        )
        
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_CONFIG["host"],
            port=RABBITMQ_CONFIG["port"],
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        counts = {}
        
        # Get embedding queue count
        embedding_queue = RABBITMQ_CONFIG["embedding_queue"]
        try:
            method = channel.queue_declare(embedding_queue, passive=True)
            counts[embedding_queue] = method.method.message_count
        except Exception:
            counts[embedding_queue] = 0
        
        # Get extraction queue count
        extraction_queue = RABBITMQ_CONFIG["extraction_queue"]
        try:
            method = channel.queue_declare(extraction_queue, passive=True)
            counts[extraction_queue] = method.method.message_count
        except Exception:
            counts[extraction_queue] = 0
        
        connection.close()
        return counts
    
    except Exception:
        return {
            RABBITMQ_CONFIG["embedding_queue"]: 0,
            RABBITMQ_CONFIG["extraction_queue"]: 0
        }


def display_summary(title: str, db_counts: Dict[str, int], minio_count: int, queue_counts: Dict[str, int]):
    """Display formatted summary of data counts."""
    print(f"\n{title}")
    print("=" * 70)
    
    print("\n📊 Database Tables:")
    for table, count in db_counts.items():
        if table != 'company_catalog':  # Don't show company_catalog as we're not deleting it
            print(f"  • {table}: {count:,} records")
    
    print(f"\n📦 MinIO Storage:")
    print(f"  • {MINIO_CONFIG['bucket']}: {minio_count:,} objects")
    
    print(f"\n📨 RabbitMQ Queues:")
    for queue, count in queue_counts.items():
        print(f"  • {queue}: {count:,} messages")


def cleanup_all(force: bool = False) -> Dict:
    """
    Execute complete cleanup of all pipeline data.
    
    Args:
        force: If True, skip confirmation prompt
    
    Returns:
        dict: Summary of cleanup results
    
    Raises:
        Exception: If any cleanup operation fails
    """
    print("=" * 70)
    print("ESG Pipeline Data Cleanup")
    print("=" * 70)
    
    conn = None
    results = {
        'success': False,
        'database': {},
        'minio': 0,
        'rabbitmq': {}
    }
    
    try:
        # Connect to database
        print("\n📊 Connecting to database...")
        conn = get_db_connection()
        
        # Get current data summary
        print("🔍 Analyzing current data...")
        db_counts = get_current_data_summary(conn)
        minio_count = get_minio_object_count()
        queue_counts = get_rabbitmq_message_counts()
        
        # Display what will be deleted
        display_summary("Data to be deleted:", db_counts, minio_count, queue_counts)
        
        # Check if there's anything to clean
        total_db = sum(v for k, v in db_counts.items() if k != 'company_catalog')
        total_to_delete = total_db + minio_count + sum(queue_counts.values())
        
        if total_to_delete == 0:
            print("\n✓ No pipeline data found. System is clean!")
            results['success'] = True
            return results
        
        # Prompt for confirmation unless --force flag is used
        if not force:
            print("\n⚠️  WARNING: This will permanently delete all pipeline data!")
            print("⚠️  This action cannot be undone.")
            response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\n✗ Cleanup cancelled by user")
                return results
        
        # Execute cleanup operations
        print("\n🗑️  Executing cleanup...")
        
        # 1. Clean MinIO storage
        print("\n  Cleaning MinIO storage...")
        try:
            minio_deleted = cleanup_minio_storage()
            results['minio'] = minio_deleted
            print(f"  ✓ Deleted {minio_deleted:,} objects from MinIO")
        except Exception as e:
            print(f"  ✗ MinIO cleanup failed: {e}")
            # Continue with other cleanups
        
        # 2. Clean database tables (with transaction)
        print("\n  Cleaning database tables...")
        try:
            db_deleted = cleanup_database_tables(conn)
            results['database'] = db_deleted
            
            for table, count in db_deleted.items():
                print(f"  ✓ Deleted {count:,} records from {table}")
        
        except Exception as e:
            print(f"  ✗ Database cleanup failed: {e}")
            print("  ✓ Transaction rolled back - no database data was deleted")
            raise
        
        # 3. Clean RabbitMQ queues
        print("\n  Cleaning RabbitMQ queues...")
        try:
            queue_purged = cleanup_rabbitmq_queues()
            results['rabbitmq'] = queue_purged
            
            for queue, count in queue_purged.items():
                print(f"  ✓ Purged {count:,} messages from {queue}")
        except Exception as e:
            print(f"  ✗ RabbitMQ cleanup failed: {e}")
            # Continue - this is not critical
        
        # Display final summary
        print("\n" + "=" * 70)
        print("✓ Cleanup completed successfully!")
        print("=" * 70)
        
        print("\n📊 Summary:")
        print(f"\n  Database:")
        for table, count in results['database'].items():
            print(f"    • {table}: {count:,} records deleted")
        
        print(f"\n  MinIO:")
        print(f"    • {results['minio']:,} objects deleted")
        
        print(f"\n  RabbitMQ:")
        for queue, count in results['rabbitmq'].items():
            print(f"    • {queue}: {count:,} messages purged")
        
        total_deleted = (
            sum(results['database'].values()) +
            results['minio'] +
            sum(results['rabbitmq'].values())
        )
        print(f"\n  Total items cleaned: {total_deleted:,}")
        
        results['success'] = True
        return results
    
    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def get_db_connection():
    """Create and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(
        description='Clean up all ESG pipeline data from MinIO, PostgreSQL, and RabbitMQ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive cleanup with confirmation
  python cleanup_pipeline_data.py
  
  # Force cleanup without confirmation
  python cleanup_pipeline_data.py --force
  
Environment Variables:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, BUCKET_NAME
  RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_PASS
  QUEUE_NAME, EXTRACTION_QUEUE_NAME
        """
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt and delete immediately'
    )
    
    args = parser.parse_args()
    
    # Execute cleanup
    cleanup_all(force=args.force)


if __name__ == "__main__":
    main()
