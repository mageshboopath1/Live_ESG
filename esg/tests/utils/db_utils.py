"""
Database utility functions for integration tests
"""
import psycopg2
from typing import List, Dict, Any, Optional
import os


def get_db_connection():
    """Create a database connection with default parameters"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "moz"),
        user=os.getenv("DB_USER", "drfitz"),
        password=os.getenv("DB_PASSWORD", "h4i1hydr4")
    )


def execute_query(query: str, params: Optional[tuple] = None) -> List[tuple]:
    """
    Execute a query and return results.
    
    Args:
        query: SQL query to execute
        params: Optional parameters for the query
        
    Returns:
        List of result tuples
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results
    finally:
        conn.close()


def execute_query_dict(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute a query and return results as dictionaries.
    
    Args:
        query: SQL query to execute
        params: Optional parameters for the query
        
    Returns:
        List of result dictionaries
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return results
    finally:
        conn.close()


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        True if table exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = %s
        )
    """
    result = execute_query(query, (table_name,))
    return result[0][0] if result else False


def get_table_count(table_name: str) -> int:
    """
    Get the number of rows in a table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        Number of rows in the table
    """
    query = f"SELECT COUNT(*) FROM {table_name}"
    result = execute_query(query)
    return result[0][0] if result else 0


def get_table_columns(table_name: str) -> List[str]:
    """
    Get the column names for a table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of column names
    """
    query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
    """
    results = execute_query(query, (table_name,))
    return [row[0] for row in results]


def verify_foreign_key(table_name: str, column_name: str, foreign_table: str) -> bool:
    """
    Verify a foreign key constraint exists.
    
    Args:
        table_name: Name of the table with the foreign key
        column_name: Name of the column with the foreign key
        foreign_table: Name of the referenced table
        
    Returns:
        True if foreign key exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
            AND kcu.column_name = %s
            AND ccu.table_name = %s
        )
    """
    result = execute_query(query, (table_name, column_name, foreign_table))
    return result[0][0] if result else False


def get_brsr_indicator_count() -> int:
    """Get the count of BRSR indicators in the database"""
    return get_table_count("brsr_indicators")


def get_brsr_indicators_by_pillar() -> Dict[str, int]:
    """
    Get BRSR indicator counts grouped by pillar.
    
    Returns:
        Dictionary with pillar as key and count as value
    """
    query = "SELECT pillar, COUNT(*) FROM brsr_indicators GROUP BY pillar"
    results = execute_query(query)
    return {row[0]: row[1] for row in results}


def get_company_count() -> int:
    """Get the count of companies in the database"""
    return get_table_count("company_catalog")


def get_embedding_count() -> int:
    """Get the count of document embeddings in the database"""
    return get_table_count("document_embeddings")


def get_extracted_indicator_count() -> int:
    """Get the count of extracted indicators in the database"""
    return get_table_count("extracted_indicators")


def get_score_count() -> int:
    """Get the count of ESG scores in the database"""
    return get_table_count("esg_scores")


def cleanup_test_data(table_name: str, condition: str):
    """
    Clean up test data from a table.
    
    Args:
        table_name: Name of the table to clean
        condition: WHERE clause condition (without WHERE keyword)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = f"DELETE FROM {table_name} WHERE {condition}"
        cursor.execute(query)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def insert_test_data(table_name: str, data: Dict[str, Any]) -> Optional[int]:
    """
    Insert test data into a table and return the ID.
    
    Args:
        table_name: Name of the table
        data: Dictionary of column names and values
        
    Returns:
        ID of inserted row if available, None otherwise
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING id"
        
        cursor.execute(query, tuple(data.values()))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        return result[0] if result else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_test_data(table_name: str, data: Dict[str, Any], condition: str):
    """
    Update test data in a table.
    
    Args:
        table_name: Name of the table
        data: Dictionary of column names and values to update
        condition: WHERE clause condition (without WHERE keyword)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        
        cursor.execute(query, tuple(data.values()))
        conn.commit()
        cursor.close()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def verify_data_exists(table_name: str, condition: str) -> bool:
    """
    Verify that data exists in a table matching the condition.
    
    Args:
        table_name: Name of the table
        condition: WHERE clause condition (without WHERE keyword)
        
    Returns:
        True if data exists, False otherwise
    """
    query = f"SELECT EXISTS (SELECT 1 FROM {table_name} WHERE {condition})"
    result = execute_query(query)
    return result[0][0] if result else False


def get_record_by_id(table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a record by ID.
    
    Args:
        table_name: Name of the table
        record_id: ID of the record
        
    Returns:
        Dictionary of record data or None if not found
    """
    query = f"SELECT * FROM {table_name} WHERE id = %s"
    results = execute_query_dict(query, (record_id,))
    return results[0] if results else None


def verify_index_exists(table_name: str, index_name: str) -> bool:
    """
    Verify that an index exists on a table.
    
    Args:
        table_name: Name of the table
        index_name: Name of the index
        
    Returns:
        True if index exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE tablename = %s
            AND indexname = %s
        )
    """
    result = execute_query(query, (table_name, index_name))
    return result[0][0] if result else False


def verify_extension_installed(extension_name: str) -> bool:
    """
    Verify that a PostgreSQL extension is installed.
    
    Args:
        extension_name: Name of the extension (e.g., 'vector')
        
    Returns:
        True if extension is installed, False otherwise
    """
    query = "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = %s)"
    result = execute_query(query, (extension_name,))
    return result[0][0] if result else False


def get_brsr_attributes() -> List[int]:
    """
    Get list of distinct BRSR attribute numbers.
    
    Returns:
        List of attribute numbers
    """
    query = "SELECT DISTINCT attribute_number FROM brsr_indicators ORDER BY attribute_number"
    results = execute_query(query)
    return [row[0] for row in results]


def verify_brsr_completeness() -> Dict[str, Any]:
    """
    Verify BRSR indicators are complete and properly configured.
    
    Returns:
        Dictionary with verification results
    """
    return {
        "total_count": get_brsr_indicator_count(),
        "attributes": get_brsr_attributes(),
        "pillars": get_brsr_indicators_by_pillar(),
        "has_all_attributes": len(get_brsr_attributes()) == 9,
        "has_all_pillars": set(get_brsr_indicators_by_pillar().keys()) == {'E', 'S', 'G'}
    }


def get_company_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get a company by ticker symbol.
    
    Args:
        ticker: Company ticker symbol
        
    Returns:
        Company dictionary or None if not found
    """
    query = "SELECT * FROM company_catalog WHERE ticker = %s"
    results = execute_query_dict(query, (ticker,))
    return results[0] if results else None


def get_indicators_for_company(company_id: int) -> List[Dict[str, Any]]:
    """
    Get all extracted indicators for a company.
    
    Args:
        company_id: ID of the company
        
    Returns:
        List of indicator dictionaries
    """
    query = "SELECT * FROM extracted_indicators WHERE company_id = %s"
    return execute_query_dict(query, (company_id,))


def get_scores_for_company(company_id: int) -> List[Dict[str, Any]]:
    """
    Get all ESG scores for a company.
    
    Args:
        company_id: ID of the company
        
    Returns:
        List of score dictionaries
    """
    query = "SELECT * FROM esg_scores WHERE company_id = %s"
    return execute_query_dict(query, (company_id,))


def verify_pipeline_data(company_id: int) -> Dict[str, bool]:
    """
    Verify that pipeline data exists for a company.
    
    Args:
        company_id: ID of the company
        
    Returns:
        Dictionary with verification results for each pipeline stage
    """
    return {
        "has_company": verify_data_exists("company_catalog", f"id = {company_id}"),
        "has_documents": verify_data_exists("ingestion_metadata", f"company_id = {company_id}"),
        "has_embeddings": verify_data_exists("document_embeddings", f"company_id = {company_id}"),
        "has_indicators": verify_data_exists("extracted_indicators", f"company_id = {company_id}"),
        "has_scores": verify_data_exists("esg_scores", f"company_id = {company_id}")
    }
