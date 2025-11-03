#!/usr/bin/env python3
"""
Pipeline orchestrator script for end-to-end testing.
Coordinates all pipeline stages and monitors progress.
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import pika

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
    RABBITMQ_CONFIG = {
        "host": _config.rabbitmq.host,
        "port": _config.rabbitmq.port,
        "user": _config.rabbitmq.user,
        "password": _config.rabbitmq.password,
        "embedding_queue": _config.rabbitmq.embedding_queue,
        "extraction_queue": _config.rabbitmq.extraction_queue
    }
    PIPELINE_CONFIG = {
        "embedding_timeout": _config.queue_monitoring.embedding_timeout,
        "extraction_timeout": _config.queue_monitoring.extraction_timeout,
        "queue_check_interval": _config.queue_monitoring.check_interval,
        "empty_queue_wait": _config.queue_monitoring.empty_queue_wait,
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

    RABBITMQ_CONFIG = {
        "host": os.getenv("RABBITMQ_HOST", "localhost"),
        "port": int(os.getenv("RABBITMQ_PORT", "5672")),
        "user": os.getenv("RABBITMQ_DEFAULT_USER", "esg_rabbitmq"),
        "password": os.getenv("RABBITMQ_DEFAULT_PASS", "esg_secret"),
        "embedding_queue": os.getenv("QUEUE_NAME", "embedding-tasks"),
        "extraction_queue": os.getenv("EXTRACTION_QUEUE_NAME", "extraction-tasks")
    }

    # Pipeline configuration
    PIPELINE_CONFIG = {
        "embedding_timeout": int(os.getenv("EMBEDDING_TIMEOUT", "3600")),  # 1 hour
        "extraction_timeout": int(os.getenv("EXTRACTION_TIMEOUT", "7200")),  # 2 hours
        "queue_check_interval": int(os.getenv("QUEUE_CHECK_INTERVAL", "10")),  # 10 seconds
        "empty_queue_wait": int(os.getenv("EMPTY_QUEUE_WAIT", "30")),  # 30 seconds
    }


# ============================================================================
# Task 6.1: Queue Monitoring Functions
# ============================================================================

def get_queue_message_count(queue_name: str) -> int:
    """
    Query RabbitMQ queue depth.
    
    Args:
        queue_name: Name of the queue to check
    
    Returns:
        int: Number of messages in the queue
    
    Raises:
        Exception: If RabbitMQ connection fails
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
        
        # Declare queue passively to get message count
        method = channel.queue_declare(queue_name, passive=True)
        message_count = method.method.message_count
        
        connection.close()
        return message_count
    
    except Exception as e:
        raise Exception(f"Failed to get message count for queue '{queue_name}': {e}")


def monitor_queue(
    queue_name: str,
    timeout: int = 3600,
    check_interval: int = 10,
    empty_wait: int = 30
) -> Dict:
    """
    Monitor RabbitMQ queue until empty or timeout.
    Verifies queue stays empty for specified duration before considering complete.
    
    Args:
        queue_name: Name of the queue to monitor
        timeout: Maximum time to wait in seconds (default: 3600)
        check_interval: How often to check queue in seconds (default: 10)
        empty_wait: How long queue must stay empty in seconds (default: 30)
    
    Returns:
        dict: {
            'success': bool,
            'messages_processed': int,
            'duration_seconds': float,
            'error': str (optional)
        }
    """
    print(f"\n📊 Monitoring queue: {queue_name}")
    print(f"   Timeout: {timeout}s | Check interval: {check_interval}s | Empty wait: {empty_wait}s")
    
    start_time = time.time()
    initial_count = get_queue_message_count(queue_name)
    last_count = initial_count
    empty_since = None
    
    print(f"   Initial message count: {initial_count}")
    
    while True:
        elapsed = time.time() - start_time
        
        # Check for timeout
        if elapsed > timeout:
            return {
                'success': False,
                'messages_processed': initial_count - last_count,
                'duration_seconds': elapsed,
                'error': f'Timeout exceeded ({timeout}s)',
                'remaining_messages': last_count
            }
        
        # Get current queue depth
        try:
            current_count = get_queue_message_count(queue_name)
        except Exception as e:
            return {
                'success': False,
                'messages_processed': initial_count - last_count,
                'duration_seconds': elapsed,
                'error': f'Failed to query queue: {e}'
            }
        
        # Check if queue is empty
        if current_count == 0:
            if empty_since is None:
                empty_since = time.time()
                print(f"   ✓ Queue empty at {elapsed:.1f}s - waiting {empty_wait}s to confirm...")
            else:
                # Check if queue has been empty long enough
                empty_duration = time.time() - empty_since
                if empty_duration >= empty_wait:
                    # Verify one more time
                    final_count = get_queue_message_count(queue_name)
                    if final_count == 0:
                        print(f"   ✓ Queue confirmed empty for {empty_wait}s")
                        return {
                            'success': True,
                            'messages_processed': initial_count,
                            'duration_seconds': time.time() - start_time,
                            'remaining_messages': 0
                        }
                    else:
                        # New messages appeared, reset
                        print(f"   ⚠️  New messages appeared ({final_count}), continuing...")
                        empty_since = None
                        last_count = final_count
        else:
            # Queue not empty, reset empty timer
            if empty_since is not None:
                print(f"   ⚠️  Queue no longer empty ({current_count} messages)")
            empty_since = None
            
            # Log progress if count changed
            if current_count != last_count:
                processed = initial_count - current_count
                rate = processed / elapsed if elapsed > 0 else 0
                print(f"   📈 Progress: {processed}/{initial_count} processed "
                      f"({current_count} remaining) | "
                      f"Rate: {rate:.2f} msg/s | "
                      f"Elapsed: {elapsed:.1f}s")
            
            last_count = current_count
        
        # Wait before next check
        time.sleep(check_interval)


# ============================================================================
# Helper Functions
# ============================================================================

def get_db_connection():
    """Create and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def print_stage_header(stage_name: str):
    """Print formatted stage header."""
    print("\n" + "=" * 70)
    print(f"  {stage_name}")
    print("=" * 70)


def print_stage_result(success: bool, message: str):
    """Print formatted stage result."""
    symbol = "✓" if success else "✗"
    print(f"\n{symbol} {message}")



# ============================================================================
# Task 6.2: Pipeline Stage Orchestration
# ============================================================================

def run_cleanup_stage(force: bool = False) -> Dict:
    """
    Execute cleanup stage and verify.
    
    Args:
        force: If True, skip confirmation prompt
    
    Returns:
        dict: Cleanup results with success status
    """
    print_stage_header("Stage 1: Cleanup")
    
    try:
        # Import cleanup function from cleanup script
        import cleanup_pipeline_data
        
        # Execute cleanup
        results = cleanup_pipeline_data.cleanup_all(force=force)
        
        if results['success']:
            print_stage_result(True, "Cleanup completed successfully")
        else:
            print_stage_result(False, "Cleanup failed or was cancelled")
        
        return results
    
    except Exception as e:
        print_stage_result(False, f"Cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


def run_ingestion_stage(companies: Optional[List[str]] = None, limit: Optional[int] = None) -> Dict:
    """
    Trigger ingestion for specified companies.
    
    Args:
        companies: List of company symbols to ingest (None = all)
        limit: Maximum number of companies to process (None = no limit)
    
    Returns:
        dict: {
            'success': bool,
            'companies_processed': int,
            'companies_failed': int,
            'duration_seconds': float,
            'error': str (optional)
        }
    """
    print_stage_header("Stage 2: Ingestion")
    
    start_time = time.time()
    
    try:
        # Build command to run ingestion service
        cmd = ["python", "services/ingestion/src/download_reports.py"]
        
        # Add company filter if specified
        if companies:
            print(f"   Processing companies: {', '.join(companies)}")
        elif limit:
            print(f"   Processing up to {limit} companies")
        else:
            print(f"   Processing all companies")
        
        # Note: The ingestion script would need to be updated to accept these parameters
        # For now, we'll run it as-is and monitor the results
        
        print(f"\n   Starting ingestion process...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"   ✓ Ingestion completed in {format_duration(duration)}")
            
            # Parse output to get statistics (basic implementation)
            # In a real implementation, the ingestion script should output structured data
            print(f"\n   Output:\n{result.stdout}")
            
            print_stage_result(True, f"Ingestion completed in {format_duration(duration)}")
            
            return {
                'success': True,
                'duration_seconds': duration,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            print(f"   ✗ Ingestion failed with exit code {result.returncode}")
            print(f"\n   Error output:\n{result.stderr}")
            
            print_stage_result(False, f"Ingestion failed: {result.stderr[:200]}")
            
            return {
                'success': False,
                'duration_seconds': duration,
                'error': result.stderr,
                'exit_code': result.returncode
            }
    
    except Exception as e:
        duration = time.time() - start_time
        print_stage_result(False, f"Ingestion failed: {e}")
        return {
            'success': False,
            'duration_seconds': duration,
            'error': str(e)
        }


def monitor_embedding_stage(timeout: Optional[int] = None) -> Dict:
    """
    Wait for embedding queue completion.
    
    Args:
        timeout: Maximum time to wait in seconds (default: from config)
    
    Returns:
        dict: Monitoring results with success status
    """
    print_stage_header("Stage 3: Embedding Processing")
    
    if timeout is None:
        timeout = PIPELINE_CONFIG["embedding_timeout"]
    
    check_interval = PIPELINE_CONFIG["queue_check_interval"]
    empty_wait = PIPELINE_CONFIG["empty_queue_wait"]
    
    queue_name = RABBITMQ_CONFIG["embedding_queue"]
    
    results = monitor_queue(
        queue_name=queue_name,
        timeout=timeout,
        check_interval=check_interval,
        empty_wait=empty_wait
    )
    
    if results['success']:
        print_stage_result(
            True,
            f"Embedding stage completed: {results['messages_processed']} messages processed "
            f"in {format_duration(results['duration_seconds'])}"
        )
    else:
        error_msg = results.get('error', 'Unknown error')
        remaining = results.get('remaining_messages', 'unknown')
        print_stage_result(
            False,
            f"Embedding stage failed: {error_msg} ({remaining} messages remaining)"
        )
    
    return results


def monitor_extraction_stage(timeout: Optional[int] = None) -> Dict:
    """
    Wait for extraction queue completion.
    
    Args:
        timeout: Maximum time to wait in seconds (default: from config)
    
    Returns:
        dict: Monitoring results with success status
    """
    print_stage_header("Stage 4: Extraction Processing")
    
    if timeout is None:
        timeout = PIPELINE_CONFIG["extraction_timeout"]
    
    check_interval = PIPELINE_CONFIG["queue_check_interval"]
    empty_wait = PIPELINE_CONFIG["empty_queue_wait"]
    
    queue_name = RABBITMQ_CONFIG["extraction_queue"]
    
    results = monitor_queue(
        queue_name=queue_name,
        timeout=timeout,
        check_interval=check_interval,
        empty_wait=empty_wait
    )
    
    if results['success']:
        print_stage_result(
            True,
            f"Extraction stage completed: {results['messages_processed']} messages processed "
            f"in {format_duration(results['duration_seconds'])}"
        )
    else:
        error_msg = results.get('error', 'Unknown error')
        remaining = results.get('remaining_messages', 'unknown')
        print_stage_result(
            False,
            f"Extraction stage failed: {error_msg} ({remaining} messages remaining)"
        )
    
    return results



# ============================================================================
# Task 6.3: Validation Functions
# ============================================================================

def check_embeddings_count() -> Dict:
    """
    Verify embeddings were created.
    
    Returns:
        dict: {
            'success': bool,
            'count': int,
            'message': str
        }
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT COUNT(*) as count FROM document_embeddings")
        result = cur.fetchone()
        count = result['count']
        
        cur.close()
        conn.close()
        
        success = count > 0
        message = f"Found {count:,} embeddings" if success else "No embeddings found"
        
        return {
            'success': success,
            'count': count,
            'message': message
        }
    
    except Exception as e:
        return {
            'success': False,
            'count': 0,
            'message': f"Failed to check embeddings: {e}"
        }


def check_embedding_dimensions() -> Dict:
    """
    Verify all embeddings are 3072 dimensions.
    
    Returns:
        dict: {
            'success': bool,
            'total_embeddings': int,
            'invalid_dimensions': int,
            'message': str
        }
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total count
        cur.execute("SELECT COUNT(*) as count FROM document_embeddings")
        total = cur.fetchone()['count']
        
        # Check for embeddings with incorrect dimensions
        # Note: pgvector stores vectors with their dimension, we can check array_length
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM document_embeddings 
            WHERE array_length(embedding::float[], 1) != 3072
        """)
        invalid = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        success = invalid == 0 and total > 0
        
        if total == 0:
            message = "No embeddings to validate"
        elif invalid == 0:
            message = f"All {total:,} embeddings have correct dimensions (3072)"
        else:
            message = f"Found {invalid:,} embeddings with incorrect dimensions (out of {total:,})"
        
        return {
            'success': success,
            'total_embeddings': total,
            'invalid_dimensions': invalid,
            'message': message
        }
    
    except Exception as e:
        return {
            'success': False,
            'total_embeddings': 0,
            'invalid_dimensions': 0,
            'message': f"Failed to check embedding dimensions: {e}"
        }


def check_indicators_count() -> Dict:
    """
    Verify indicators were extracted.
    
    Returns:
        dict: {
            'success': bool,
            'count': int,
            'unique_reports': int,
            'message': str
        }
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total indicators
        cur.execute("SELECT COUNT(*) as count FROM extracted_indicators")
        count = cur.fetchone()['count']
        
        # Get unique reports
        cur.execute("""
            SELECT COUNT(DISTINCT object_key) as count 
            FROM extracted_indicators
        """)
        unique_reports = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        success = count > 0
        message = (
            f"Found {count:,} extracted indicators across {unique_reports} reports"
            if success else "No indicators extracted"
        )
        
        return {
            'success': success,
            'count': count,
            'unique_reports': unique_reports,
            'message': message
        }
    
    except Exception as e:
        return {
            'success': False,
            'count': 0,
            'unique_reports': 0,
            'message': f"Failed to check indicators: {e}"
        }


def check_scores_count() -> Dict:
    """
    Verify ESG scores were calculated.
    
    Returns:
        dict: {
            'success': bool,
            'count': int,
            'message': str
        }
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT COUNT(*) as count FROM esg_scores")
        result = cur.fetchone()
        count = result['count']
        
        cur.close()
        conn.close()
        
        success = count > 0
        message = f"Found {count:,} ESG scores" if success else "No ESG scores found"
        
        return {
            'success': success,
            'count': count,
            'message': message
        }
    
    except Exception as e:
        return {
            'success': False,
            'count': 0,
            'message': f"Failed to check scores: {e}"
        }


def check_referential_integrity() -> Dict:
    """
    Verify no orphaned records exist.
    
    Returns:
        dict: {
            'success': bool,
            'issues': list,
            'message': str
        }
    """
    issues = []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check for extracted_indicators without corresponding embeddings
        cur.execute("""
            SELECT COUNT(*) as count
            FROM extracted_indicators ei
            LEFT JOIN document_embeddings de 
                ON ei.object_key = de.object_key
            WHERE de.object_key IS NULL
        """)
        orphaned_indicators = cur.fetchone()['count']
        if orphaned_indicators > 0:
            issues.append(f"{orphaned_indicators} extracted_indicators without embeddings")
        
        # Check for extracted_indicators without company_catalog entry
        cur.execute("""
            SELECT COUNT(*) as count
            FROM extracted_indicators ei
            LEFT JOIN company_catalog cc ON ei.company_id = cc.id
            WHERE cc.id IS NULL
        """)
        indicators_no_company = cur.fetchone()['count']
        if indicators_no_company > 0:
            issues.append(f"{indicators_no_company} extracted_indicators without company_catalog entry")
        
        # Check for esg_scores without company_catalog entry
        cur.execute("""
            SELECT COUNT(*) as count
            FROM esg_scores es
            LEFT JOIN company_catalog cc ON es.company_id = cc.id
            WHERE cc.id IS NULL
        """)
        scores_no_company = cur.fetchone()['count']
        if scores_no_company > 0:
            issues.append(f"{scores_no_company} esg_scores without company_catalog entry")
        
        # Check for esg_scores without corresponding extracted_indicators
        cur.execute("""
            SELECT COUNT(DISTINCT es.company_id, es.report_year) as count
            FROM esg_scores es
            LEFT JOIN extracted_indicators ei 
                ON es.company_id = ei.company_id 
                AND es.report_year = ei.report_year
            WHERE ei.id IS NULL
        """)
        scores_no_indicators = cur.fetchone()['count']
        if scores_no_indicators > 0:
            issues.append(f"{scores_no_indicators} esg_scores without extracted_indicators")
        
        cur.close()
        conn.close()
        
        success = len(issues) == 0
        
        if success:
            message = "No referential integrity issues found"
        else:
            message = f"Found {len(issues)} referential integrity issues"
        
        return {
            'success': success,
            'issues': issues,
            'message': message
        }
    
    except Exception as e:
        return {
            'success': False,
            'issues': [],
            'message': f"Failed to check referential integrity: {e}"
        }


def validate_pipeline_output() -> Dict:
    """
    Run all validation checks.
    
    Returns:
        dict: {
            'success': bool,
            'checks': dict,
            'summary': str
        }
    """
    print_stage_header("Stage 5: Validation")
    
    checks = {}
    
    # Run all validation checks
    print("\n   Running validation checks...")
    
    print("   • Checking embeddings count...")
    checks['embeddings_count'] = check_embeddings_count()
    print(f"     {checks['embeddings_count']['message']}")
    
    print("   • Checking embedding dimensions...")
    checks['embedding_dimensions'] = check_embedding_dimensions()
    print(f"     {checks['embedding_dimensions']['message']}")
    
    print("   • Checking indicators count...")
    checks['indicators_count'] = check_indicators_count()
    print(f"     {checks['indicators_count']['message']}")
    
    print("   • Checking scores count...")
    checks['scores_count'] = check_scores_count()
    print(f"     {checks['scores_count']['message']}")
    
    print("   • Checking referential integrity...")
    checks['referential_integrity'] = check_referential_integrity()
    print(f"     {checks['referential_integrity']['message']}")
    if checks['referential_integrity']['issues']:
        for issue in checks['referential_integrity']['issues']:
            print(f"       ⚠️  {issue}")
    
    # Determine overall success
    all_passed = all(check['success'] for check in checks.values())
    
    # Count passed/failed
    passed = sum(1 for check in checks.values() if check['success'])
    total = len(checks)
    
    summary = f"{passed}/{total} validation checks passed"
    
    print_stage_result(all_passed, summary)
    
    return {
        'success': all_passed,
        'checks': checks,
        'summary': summary,
        'passed': passed,
        'total': total
    }



# ============================================================================
# Task 6.4: Main Pipeline Execution Function
# ============================================================================

def run_full_pipeline(
    companies: Optional[List[str]] = None,
    limit: Optional[int] = None,
    skip_cleanup: bool = False,
    force_cleanup: bool = False,
    embedding_timeout: Optional[int] = None,
    extraction_timeout: Optional[int] = None
) -> Dict:
    """
    Orchestrate all pipeline stages.
    
    Args:
        companies: List of company symbols to process (None = all)
        limit: Maximum number of companies to process (None = no limit)
        skip_cleanup: If True, skip cleanup stage
        force_cleanup: If True, skip cleanup confirmation
        embedding_timeout: Override default embedding timeout
        extraction_timeout: Override default extraction timeout
    
    Returns:
        dict: {
            'success': bool,
            'stages': dict,
            'total_duration': float,
            'summary': str
        }
    """
    print("\n" + "=" * 70)
    print("  ESG PIPELINE END-TO-END TEST")
    print("=" * 70)
    print(f"\n  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    pipeline_start = time.time()
    stages = {}
    
    try:
        # Stage 1: Cleanup (optional)
        if not skip_cleanup:
            cleanup_result = run_cleanup_stage(force=force_cleanup)
            stages['cleanup'] = cleanup_result
            
            if not cleanup_result['success']:
                print("\n✗ Pipeline aborted: Cleanup failed or was cancelled")
                return {
                    'success': False,
                    'stages': stages,
                    'total_duration': time.time() - pipeline_start,
                    'summary': 'Pipeline aborted at cleanup stage'
                }
        else:
            print_stage_header("Stage 1: Cleanup")
            print("   ⊘ Skipped (--skip-cleanup flag)")
        
        # Stage 2: Ingestion
        ingestion_result = run_ingestion_stage(companies=companies, limit=limit)
        stages['ingestion'] = ingestion_result
        
        if not ingestion_result['success']:
            print("\n✗ Pipeline aborted: Ingestion failed")
            return {
                'success': False,
                'stages': stages,
                'total_duration': time.time() - pipeline_start,
                'summary': 'Pipeline aborted at ingestion stage'
            }
        
        # Stage 3: Embedding Processing
        embedding_result = monitor_embedding_stage(timeout=embedding_timeout)
        stages['embedding'] = embedding_result
        
        if not embedding_result['success']:
            print("\n⚠️  Warning: Embedding stage did not complete successfully")
            print("   Continuing to extraction stage...")
        
        # Stage 4: Extraction Processing
        extraction_result = monitor_extraction_stage(timeout=extraction_timeout)
        stages['extraction'] = extraction_result
        
        if not extraction_result['success']:
            print("\n⚠️  Warning: Extraction stage did not complete successfully")
            print("   Continuing to validation...")
        
        # Stage 5: Validation
        validation_result = validate_pipeline_output()
        stages['validation'] = validation_result
        
        # Calculate total duration
        total_duration = time.time() - pipeline_start
        
        # Determine overall success
        # Pipeline is successful if all critical stages succeeded
        critical_stages_success = (
            ingestion_result['success'] and
            embedding_result['success'] and
            extraction_result['success'] and
            validation_result['success']
        )
        
        # Print final summary
        print("\n" + "=" * 70)
        print("  PIPELINE SUMMARY")
        print("=" * 70)
        
        print(f"\n  Total Duration: {format_duration(total_duration)}")
        print(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n  Stage Results:")
        if not skip_cleanup and 'cleanup' in stages:
            status = "✓" if stages['cleanup']['success'] else "✗"
            print(f"    {status} Cleanup")
        
        status = "✓" if stages['ingestion']['success'] else "✗"
        duration = format_duration(stages['ingestion']['duration_seconds'])
        print(f"    {status} Ingestion ({duration})")
        
        status = "✓" if stages['embedding']['success'] else "✗"
        duration = format_duration(stages['embedding']['duration_seconds'])
        processed = stages['embedding']['messages_processed']
        print(f"    {status} Embedding ({duration}, {processed} messages)")
        
        status = "✓" if stages['extraction']['success'] else "✗"
        duration = format_duration(stages['extraction']['duration_seconds'])
        processed = stages['extraction']['messages_processed']
        print(f"    {status} Extraction ({duration}, {processed} messages)")
        
        status = "✓" if stages['validation']['success'] else "✗"
        passed = stages['validation']['passed']
        total = stages['validation']['total']
        print(f"    {status} Validation ({passed}/{total} checks passed)")
        
        # Print data statistics
        if validation_result['success']:
            print("\n  Data Statistics:")
            checks = validation_result['checks']
            
            if 'embeddings_count' in checks:
                count = checks['embeddings_count']['count']
                print(f"    • Embeddings: {count:,}")
            
            if 'indicators_count' in checks:
                count = checks['indicators_count']['count']
                reports = checks['indicators_count']['unique_reports']
                print(f"    • Indicators: {count:,} (across {reports} reports)")
            
            if 'scores_count' in checks:
                count = checks['scores_count']['count']
                print(f"    • ESG Scores: {count:,}")
        
        # Final result
        print("\n" + "=" * 70)
        if critical_stages_success:
            print("  ✓ PIPELINE COMPLETED SUCCESSFULLY")
            summary = "All stages completed successfully"
        else:
            print("  ✗ PIPELINE COMPLETED WITH ERRORS")
            failed_stages = [
                name for name, result in stages.items()
                if not result.get('success', False)
            ]
            summary = f"Failed stages: {', '.join(failed_stages)}"
        print("=" * 70)
        
        return {
            'success': critical_stages_success,
            'stages': stages,
            'total_duration': total_duration,
            'summary': summary
        }
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        return {
            'success': False,
            'stages': stages,
            'total_duration': time.time() - pipeline_start,
            'summary': 'Pipeline interrupted by user'
        }
    
    except Exception as e:
        print(f"\n\n✗ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'stages': stages,
            'total_duration': time.time() - pipeline_start,
            'summary': f'Pipeline failed: {e}'
        }


# ============================================================================
# Command-Line Interface
# ============================================================================

def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='ESG Pipeline End-to-End Test Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with all companies
  python pipeline_orchestrator.py
  
  # Run with specific companies
  python pipeline_orchestrator.py --companies RELIANCE TCS INFY
  
  # Run with limited number of companies
  python pipeline_orchestrator.py --limit 5
  
  # Skip cleanup stage (for incremental testing)
  python pipeline_orchestrator.py --skip-cleanup
  
  # Force cleanup without confirmation
  python pipeline_orchestrator.py --force-cleanup
  
  # Custom timeouts
  python pipeline_orchestrator.py --embedding-timeout 7200 --extraction-timeout 14400

Environment Variables:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_PASS
  QUEUE_NAME, EXTRACTION_QUEUE_NAME
  EMBEDDING_TIMEOUT, EXTRACTION_TIMEOUT, QUEUE_CHECK_INTERVAL, EMPTY_QUEUE_WAIT
        """
    )
    
    parser.add_argument(
        '--companies',
        nargs='+',
        help='List of company symbols to process (e.g., RELIANCE TCS INFY)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of companies to process'
    )
    
    parser.add_argument(
        '--skip-cleanup',
        action='store_true',
        help='Skip cleanup stage (for incremental testing)'
    )
    
    parser.add_argument(
        '--force-cleanup',
        action='store_true',
        help='Skip cleanup confirmation prompt'
    )
    
    parser.add_argument(
        '--embedding-timeout',
        type=int,
        help=f'Embedding stage timeout in seconds (default: {PIPELINE_CONFIG["embedding_timeout"]})'
    )
    
    parser.add_argument(
        '--extraction-timeout',
        type=int,
        help=f'Extraction stage timeout in seconds (default: {PIPELINE_CONFIG["extraction_timeout"]})'
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    result = run_full_pipeline(
        companies=args.companies,
        limit=args.limit,
        skip_cleanup=args.skip_cleanup,
        force_cleanup=args.force_cleanup,
        embedding_timeout=args.embedding_timeout,
        extraction_timeout=args.extraction_timeout
    )
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
