#!/usr/bin/env python3
"""
Clean up sample data from the database.
This removes extracted indicators with 'Sample:' prefix and orphaned ESG scores.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse


# Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "moz"),
    "user": os.getenv("DB_USER", "drfitz"),
    "password": os.getenv("DB_PASSWORD", "h4i1hydr4")
}


def get_db_connection():
    """Create and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def identify_sample_data(conn):
    """
    Identify sample data in the database.
    Returns count of sample records by table.
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Count extracted indicators with 'Sample:' prefix
    cur.execute("""
        SELECT COUNT(*) as count
        FROM extracted_indicators 
        WHERE extracted_value LIKE 'Sample:%'
    """)
    sample_indicators_count = cur.fetchone()['count']
    
    # Count orphaned ESG scores (scores with no associated indicators)
    cur.execute("""
        SELECT COUNT(*) as count
        FROM esg_scores es
        WHERE NOT EXISTS (
            SELECT 1 FROM extracted_indicators ei 
            WHERE ei.company_id = es.company_id 
            AND ei.report_year = es.report_year
        )
    """)
    orphaned_scores_count = cur.fetchone()['count']
    
    cur.close()
    
    return {
        'sample_indicators': sample_indicators_count,
        'orphaned_scores': orphaned_scores_count
    }


def delete_sample_indicators(conn):
    """
    Delete extracted indicators with 'Sample:' prefix.
    Returns number of deleted records.
    """
    cur = conn.cursor()
    
    cur.execute("""
        DELETE FROM extracted_indicators 
        WHERE extracted_value LIKE 'Sample:%'
    """)
    
    deleted_count = cur.rowcount
    cur.close()
    
    print(f"  ✓ Deleted {deleted_count} sample indicators")
    return deleted_count


def delete_orphaned_scores(conn):
    """
    Delete ESG scores that have no associated extracted indicators.
    Returns number of deleted records.
    """
    cur = conn.cursor()
    
    cur.execute("""
        DELETE FROM esg_scores es
        WHERE NOT EXISTS (
            SELECT 1 FROM extracted_indicators ei 
            WHERE ei.company_id = es.company_id 
            AND ei.report_year = es.report_year
        )
    """)
    
    deleted_count = cur.rowcount
    cur.close()
    
    print(f"  ✓ Deleted {deleted_count} orphaned ESG scores")
    return deleted_count


def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(
        description='Clean up sample data from the database'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt and delete immediately'
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("Database Sample Data Cleanup")
    print("=" * 70)
    
    conn = None
    
    try:
        # Connect to database
        print("\n📊 Connecting to database...")
        conn = get_db_connection()
        
        # Identify sample data
        print("🔍 Identifying sample data...")
        counts = identify_sample_data(conn)
        
        print(f"\nFound sample data:")
        print(f"  • Sample indicators: {counts['sample_indicators']}")
        print(f"  • Orphaned ESG scores: {counts['orphaned_scores']}")
        
        # Check if there's anything to clean
        total_to_delete = counts['sample_indicators'] + counts['orphaned_scores']
        if total_to_delete == 0:
            print("\n✓ No sample data found. Database is clean!")
            conn.close()
            return
        
        # Prompt for confirmation unless --force flag is used
        if not args.force:
            print("\n⚠️  This will permanently delete the above records.")
            response = input("Do you want to proceed? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\n✗ Cleanup cancelled by user")
                conn.close()
                return
        
        # Execute deletions in transaction
        print("\n🗑️  Deleting sample data...")
        
        try:
            # Start transaction
            conn.autocommit = False
            
            # Delete sample indicators first
            indicators_deleted = delete_sample_indicators(conn)
            
            # Delete orphaned scores
            scores_deleted = delete_orphaned_scores(conn)
            
            # Commit transaction
            conn.commit()
            
            print("\n" + "=" * 70)
            print("✓ Cleanup completed successfully!")
            print("=" * 70)
            print(f"\nSummary:")
            print(f"  • Sample indicators deleted: {indicators_deleted}")
            print(f"  • Orphaned ESG scores deleted: {scores_deleted}")
            print(f"  • Total records deleted: {indicators_deleted + scores_deleted}")
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            print(f"\n✗ Error during deletion: {e}")
            print("✓ Transaction rolled back - no data was deleted")
            raise
        
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


if __name__ == "__main__":
    main()
