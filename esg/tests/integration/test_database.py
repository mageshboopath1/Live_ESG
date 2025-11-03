"""
Database integration tests

These tests verify:
- Database connectivity
- Required tables exist
- BRSR indicators are properly seeded
- pgvector extension is installed
- Actual data exists in tables
"""
import pytest
import psycopg2


def test_database_connection(db_connection):
    """Test database is accessible and connection works"""
    assert db_connection is not None
    assert db_connection.closed == 0, "Database connection is closed"


def test_required_tables_exist(db_cursor):
    """Test all required tables exist in the database"""
    required_tables = [
        "brsr_indicators",
        "company_catalog",
        "document_embeddings",
        "extracted_indicators",
        "esg_scores",
        "ingestion_metadata",
        "users",
        "api_keys"
    ]
    
    for table in required_tables:
        db_cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
            (table,)
        )
        exists = db_cursor.fetchone()[0]
        assert exists, f"Required table '{table}' does not exist"


def test_brsr_indicators_seeded(db_cursor):
    """
    Test BRSR indicators are seeded with complete set from Annexure I.
    Verifies actual data exists, not just schema.
    """
    # Verify table has data
    db_cursor.execute("SELECT COUNT(*) FROM brsr_indicators")
    count = db_cursor.fetchone()[0]
    
    assert count > 0, "BRSR indicators table is empty - no data seeded"
    assert count >= 55, f"Expected at least 55 indicators from Annexure I, found {count}"
    
    print(f"✓ Found {count} BRSR indicators")


def test_brsr_indicators_all_attributes(db_cursor):
    """Test all 9 BRSR attributes are represented in the indicators"""
    db_cursor.execute(
        "SELECT DISTINCT attribute_number FROM brsr_indicators ORDER BY attribute_number"
    )
    attributes = [row[0] for row in db_cursor.fetchall()]
    
    expected_attributes = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert attributes == expected_attributes, \
        f"Missing attributes. Expected {expected_attributes}, found {attributes}"
    
    print(f"✓ All 9 BRSR attributes present")


def test_brsr_indicators_pillars_assigned(db_cursor):
    """Test BRSR indicators have correct pillar assignments (E/S/G)"""
    db_cursor.execute(
        "SELECT pillar, COUNT(*) FROM brsr_indicators GROUP BY pillar ORDER BY pillar"
    )
    pillars = dict(db_cursor.fetchall())
    
    assert 'E' in pillars, "No Environmental (E) indicators found"
    assert 'S' in pillars, "No Social (S) indicators found"
    assert 'G' in pillars, "No Governance (G) indicators found"
    
    assert pillars['E'] > 0, "Environmental pillar has no indicators"
    assert pillars['S'] > 0, "Social pillar has no indicators"
    assert pillars['G'] > 0, "Governance pillar has no indicators"
    
    print(f"✓ Pillar distribution: E={pillars.get('E', 0)}, S={pillars.get('S', 0)}, G={pillars.get('G', 0)}")


def test_brsr_indicators_have_required_fields(db_cursor):
    """Test BRSR indicators have all required fields populated"""
    db_cursor.execute("""
        SELECT 
            indicator_code,
            parameter_name,
            measurement_unit,
            description,
            pillar,
            weight
        FROM brsr_indicators
        LIMIT 5
    """)
    
    indicators = db_cursor.fetchall()
    assert len(indicators) > 0, "No indicators found to verify"
    
    for indicator in indicators:
        code, param_name, unit, desc, pillar, weight = indicator
        assert code is not None and code != "", f"Indicator has empty code"
        assert param_name is not None and param_name != "", f"Indicator {code} has empty parameter_name"
        assert unit is not None and unit != "", f"Indicator {code} has empty measurement_unit"
        assert pillar in ['E', 'S', 'G'], f"Indicator {code} has invalid pillar: {pillar}"
        assert weight is not None and weight > 0, f"Indicator {code} has invalid weight: {weight}"
    
    print(f"✓ Verified {len(indicators)} indicators have required fields")


def test_pgvector_extension_installed(db_cursor):
    """Test pgvector extension is installed and available"""
    db_cursor.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')"
    )
    exists = db_cursor.fetchone()[0]
    
    assert exists, "pgvector extension is not installed"
    print("✓ pgvector extension is installed")


def test_document_embeddings_table_structure(db_cursor):
    """Test document_embeddings table has vector column"""
    db_cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_embeddings' 
        AND column_name = 'embedding'
    """)
    
    result = db_cursor.fetchone()
    assert result is not None, "document_embeddings table missing 'embedding' column"
    
    column_name, data_type = result
    assert column_name == 'embedding', "Embedding column not found"
    assert data_type == 'USER-DEFINED', "Embedding column is not a vector type"
    
    print("✓ document_embeddings table has vector column")


def test_database_indexes_exist(db_cursor):
    """Test critical indexes exist for performance"""
    # Check for indexes on commonly queried columns
    db_cursor.execute("""
        SELECT tablename, indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public'
        AND tablename IN ('brsr_indicators', 'company_catalog', 'document_embeddings')
    """)
    
    indexes = db_cursor.fetchall()
    assert len(indexes) > 0, "No indexes found on critical tables"
    
    print(f"✓ Found {len(indexes)} indexes on critical tables")


def test_foreign_key_constraints_exist(db_cursor):
    """Test foreign key constraints are properly defined"""
    db_cursor.execute("""
        SELECT 
            tc.table_name, 
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
    """)
    
    foreign_keys = db_cursor.fetchall()
    assert len(foreign_keys) > 0, "No foreign key constraints found"
    
    print(f"✓ Found {len(foreign_keys)} foreign key constraints")
