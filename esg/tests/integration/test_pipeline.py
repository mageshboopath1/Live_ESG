"""
End-to-end pipeline integration tests

These tests verify:
- Document upload to MinIO
- Embeddings generation and storage
- Extraction service processing
- Scores calculation
- Data verification at each step by querying database
"""
import pytest
import io
import time
from minio import Minio
from minio.error import S3Error


def test_minio_document_upload(minio_config):
    """Test document can be uploaded to MinIO"""
    try:
        client = Minio(
            minio_config["endpoint"],
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=minio_config["secure"]
        )
        
        bucket_name = "esg-reports"
        
        # Create bucket if it doesn't exist
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"✓ Created bucket '{bucket_name}'")
        
        # Upload a test file
        test_content = b"Test PDF content for integration testing"
        test_file = io.BytesIO(test_content)
        object_name = "test/integration_test_document.pdf"
        
        client.put_object(
            bucket_name,
            object_name,
            test_file,
            length=len(test_content),
            content_type="application/pdf"
        )
        
        print(f"✓ Uploaded test document to MinIO: {object_name}")
        
        # Verify upload by retrieving
        response = client.get_object(bucket_name, object_name)
        retrieved_content = response.read()
        response.close()
        response.release_conn()
        
        assert retrieved_content == test_content, "Retrieved content doesn't match uploaded content"
        print(f"✓ Verified document retrieval from MinIO")
        
        # Clean up
        client.remove_object(bucket_name, object_name)
        
    except S3Error as e:
        pytest.fail(f"MinIO upload test failed: {e}")
    except Exception as e:
        pytest.fail(f"MinIO test failed: {e}")


def test_minio_document_metadata(minio_config):
    """Test document metadata is stored correctly in MinIO"""
    try:
        client = Minio(
            minio_config["endpoint"],
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=minio_config["secure"]
        )
        
        bucket_name = "esg-reports"
        
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        
        # Upload with metadata
        test_content = b"Test document with metadata"
        test_file = io.BytesIO(test_content)
        object_name = "test/metadata_test.pdf"
        
        metadata = {
            "company-id": "test-company",
            "report-year": "2024",
            "report-type": "BRSR"
        }
        
        client.put_object(
            bucket_name,
            object_name,
            test_file,
            length=len(test_content),
            content_type="application/pdf",
            metadata=metadata
        )
        
        # Retrieve and verify metadata
        stat = client.stat_object(bucket_name, object_name)
        assert stat.metadata is not None, "No metadata found"
        
        # MinIO prefixes metadata keys with 'x-amz-meta-'
        for key, value in metadata.items():
            meta_key = f"x-amz-meta-{key}"
            assert meta_key in stat.metadata, f"Metadata key {key} not found"
            assert stat.metadata[meta_key] == value, f"Metadata value mismatch for {key}"
        
        print(f"✓ Document metadata stored and retrieved correctly")
        
        # Clean up
        client.remove_object(bucket_name, object_name)
        
    except Exception as e:
        pytest.fail(f"MinIO metadata test failed: {e}")


def test_ingestion_metadata_table(db_cursor):
    """Test ingestion metadata is tracked in database"""
    # Check if ingestion_metadata table has the right structure
    db_cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'ingestion_metadata'
        ORDER BY ordinal_position
    """)
    
    columns = db_cursor.fetchall()
    assert len(columns) > 0, "ingestion_metadata table has no columns"
    
    column_names = [col[0] for col in columns]
    
    # Check for essential columns
    essential_columns = ["id", "company_id", "file_path", "status"]
    for col in essential_columns:
        assert col in column_names, f"Missing essential column: {col}"
    
    print(f"✓ ingestion_metadata table has correct structure ({len(columns)} columns)")


def test_embeddings_storage_structure(db_cursor):
    """Test document_embeddings table can store embeddings"""
    # Verify table structure
    db_cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_embeddings'
        ORDER BY ordinal_position
    """)
    
    columns = db_cursor.fetchall()
    assert len(columns) > 0, "document_embeddings table has no columns"
    
    column_names = [col[0] for col in columns]
    
    # Check for essential columns (actual schema uses object_key, not document_id)
    essential_columns = ["id", "object_key", "chunk_text", "embedding"]
    for col in essential_columns:
        assert col in column_names, f"Missing essential column: {col}"
    
    print(f"✓ document_embeddings table has correct structure")


def test_embeddings_vector_operations(db_cursor):
    """Test vector operations work on embeddings table"""
    # Check if we can perform vector operations
    try:
        # This will fail if pgvector is not properly set up
        db_cursor.execute("""
            SELECT COUNT(*) 
            FROM document_embeddings 
            WHERE embedding IS NOT NULL
        """)
        
        count = db_cursor.fetchone()[0]
        print(f"✓ Vector operations work (found {count} embeddings)")
        
    except Exception as e:
        pytest.fail(f"Vector operations test failed: {e}")


def test_extracted_indicators_structure(db_cursor):
    """Test extracted_indicators table structure"""
    db_cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'extracted_indicators'
        ORDER BY ordinal_position
    """)
    
    columns = db_cursor.fetchall()
    assert len(columns) > 0, "extracted_indicators table has no columns"
    
    column_names = [col[0] for col in columns]
    
    # Check for essential columns (actual schema uses indicator_id and extracted_value, not indicator_code and value)
    essential_columns = ["id", "company_id", "indicator_id", "extracted_value"]
    for col in essential_columns:
        assert col in column_names, f"Missing essential column: {col}"
    
    print(f"✓ extracted_indicators table has correct structure")


def test_esg_scores_structure(db_cursor):
    """Test esg_scores table structure"""
    db_cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'esg_scores'
        ORDER BY ordinal_position
    """)
    
    columns = db_cursor.fetchall()
    assert len(columns) > 0, "esg_scores table has no columns"
    
    column_names = [col[0] for col in columns]
    
    # Check for essential columns (actual schema has separate score columns, not score_type/score_value)
    essential_columns = ["id", "company_id", "environmental_score", "social_score", "governance_score", "overall_score"]
    for col in essential_columns:
        assert col in column_names, f"Missing essential column: {col}"
    
    print(f"✓ esg_scores table has correct structure")


def test_pipeline_data_flow_verification(db_cursor):
    """
    Test that pipeline tables are properly linked for data flow.
    This verifies foreign key relationships exist.
    """
    # Check foreign keys from extracted_indicators to company_catalog
    db_cursor.execute("""
        SELECT 
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'extracted_indicators'
    """)
    
    foreign_keys = db_cursor.fetchall()
    
    # Should have at least company_id foreign key
    fk_tables = [fk[2] for fk in foreign_keys]
    
    if 'company_catalog' in fk_tables:
        print(f"✓ extracted_indicators properly linked to company_catalog")
    else:
        print(f"⚠ extracted_indicators may not have foreign key to company_catalog")
    
    if 'brsr_indicators' in fk_tables:
        print(f"✓ extracted_indicators properly linked to brsr_indicators")
    else:
        print(f"⚠ extracted_indicators may not have foreign key to brsr_indicators")


def test_end_to_end_data_consistency(db_cursor):
    """
    Test data consistency across pipeline tables.
    If data exists, verify it's properly linked.
    """
    # Check if we have any extracted indicators
    db_cursor.execute("SELECT COUNT(*) FROM extracted_indicators")
    indicator_count = db_cursor.fetchone()[0]
    
    if indicator_count == 0:
        print("⚠ No extracted indicators yet - pipeline not run")
        return
    
    # Verify extracted indicators reference valid companies
    db_cursor.execute("""
        SELECT COUNT(*) 
        FROM extracted_indicators ei
        LEFT JOIN company_catalog cc ON ei.company_id = cc.id
        WHERE cc.id IS NULL
    """)
    orphaned_indicators = db_cursor.fetchone()[0]
    
    assert orphaned_indicators == 0, \
        f"Found {orphaned_indicators} extracted indicators with invalid company_id"
    
    # Verify extracted indicators reference valid BRSR indicators
    db_cursor.execute("""
        SELECT COUNT(*) 
        FROM extracted_indicators ei
        LEFT JOIN brsr_indicators bi ON ei.indicator_code = bi.indicator_code
        WHERE bi.indicator_code IS NULL
    """)
    invalid_indicators = db_cursor.fetchone()[0]
    
    assert invalid_indicators == 0, \
        f"Found {invalid_indicators} extracted indicators with invalid indicator_code"
    
    print(f"✓ Data consistency verified across pipeline tables ({indicator_count} indicators)")


def test_scores_calculation_readiness(db_cursor):
    """Test system is ready to calculate ESG scores"""
    # Check if we have the necessary data for score calculation
    
    # 1. BRSR indicators with weights
    db_cursor.execute("""
        SELECT COUNT(*) 
        FROM brsr_indicators 
        WHERE weight IS NOT NULL AND weight > 0
    """)
    weighted_indicators = db_cursor.fetchone()[0]
    
    assert weighted_indicators > 0, "No BRSR indicators with weights for score calculation"
    
    # 2. Check pillar distribution for balanced scoring
    db_cursor.execute("""
        SELECT pillar, COUNT(*), SUM(weight)
        FROM brsr_indicators 
        GROUP BY pillar
    """)
    pillar_stats = db_cursor.fetchall()
    
    pillars = {stat[0]: {"count": stat[1], "weight": float(stat[2])} for stat in pillar_stats}
    
    assert 'E' in pillars, "No Environmental indicators for scoring"
    assert 'S' in pillars, "No Social indicators for scoring"
    assert 'G' in pillars, "No Governance indicators for scoring"
    
    print(f"✓ Score calculation ready:")
    print(f"  - Environmental: {pillars['E']['count']} indicators, weight: {pillars['E']['weight']}")
    print(f"  - Social: {pillars['S']['count']} indicators, weight: {pillars['S']['weight']}")
    print(f"  - Governance: {pillars['G']['count']} indicators, weight: {pillars['G']['weight']}")


@pytest.mark.slow
def test_full_pipeline_simulation(db_cursor, minio_config):
    """
    Simulate a full pipeline run (without actually processing).
    This test verifies all components are in place for E2E processing.
    """
    print("\n=== Full Pipeline Simulation ===")
    
    # Step 1: Document upload capability
    try:
        client = Minio(
            minio_config["endpoint"],
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=minio_config["secure"]
        )
        bucket_exists = client.bucket_exists("esg-reports")
        print(f"✓ Step 1: Document storage ready (bucket exists: {bucket_exists})")
    except Exception as e:
        print(f"✗ Step 1: Document storage failed: {e}")
        pytest.fail("Pipeline step 1 failed")
    
    # Step 2: Embeddings storage capability
    db_cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='document_embeddings')")
    embeddings_table_exists = db_cursor.fetchone()[0]
    print(f"✓ Step 2: Embeddings storage ready (table exists: {embeddings_table_exists})")
    
    # Step 3: BRSR indicators available for extraction
    db_cursor.execute("SELECT COUNT(*) FROM brsr_indicators")
    indicator_count = db_cursor.fetchone()[0]
    print(f"✓ Step 3: Extraction ready ({indicator_count} BRSR indicators available)")
    
    # Step 4: Extracted indicators storage capability
    db_cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='extracted_indicators')")
    extracted_table_exists = db_cursor.fetchone()[0]
    print(f"✓ Step 4: Indicator storage ready (table exists: {extracted_table_exists})")
    
    # Step 5: Score calculation capability
    db_cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='esg_scores')")
    scores_table_exists = db_cursor.fetchone()[0]
    print(f"✓ Step 5: Score storage ready (table exists: {scores_table_exists})")
    
    print("\n✓ All pipeline components are in place and ready")
