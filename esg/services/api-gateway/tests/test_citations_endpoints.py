"""Test script to verify citation endpoints."""

import sys
from fastapi.testclient import TestClient
from src.main import app
from src.db.connection import check_database_connection

# Create test client
client = TestClient(app)


def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    if check_database_connection():
        print("✓ Database connection successful")
        return True
    else:
        print("✗ Database connection failed")
        return False


def test_get_indicator_citations():
    """Test getting citations for an extracted indicator."""
    print("\nTesting GET /api/citations/{extracted_indicator_id}...")
    try:
        # First get a company with indicators
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with indicators
        company_id = None
        for company in companies:
            if company.get('indicator_count', 0) > 0:
                company_id = company['id']
                break
        
        if not company_id:
            print("⚠ No companies with indicators available to test (this is expected if no extractions have been done)")
            return True
        
        # Get indicators for this company
        response = client.get(f"/api/companies/{company_id}/indicators?skip=0&limit=1")
        if response.status_code != 200:
            print("✗ Failed to get indicators")
            return False
        
        data = response.json()
        if not data['indicators']:
            print("⚠ No indicators found for company")
            return True
        
        # Get the first indicator ID
        indicator_id = data['indicators'][0]['id']
        indicator_name = data['indicators'][0]['parameter_name']
        
        # Now get citations for this indicator
        response = client.get(f"/api/citations/{indicator_id}")
        if response.status_code == 200:
            citations = response.json()
            print(f"✓ Retrieved {len(citations)} citations for indicator '{indicator_name}'")
            
            if citations:
                print("\nSample citation:")
                citation = citations[0]
                print(f"  PDF: {citation['pdf_name']}")
                print(f"  Pages: {citation['pages']}")
                print(f"  Chunk IDs: {citation['chunk_ids']}")
                print(f"  Text preview: {citation['chunk_text'][:100]}...")
            else:
                print("  (No citations found - indicator may not have source data)")
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_get_indicator_citations_not_found():
    """Test getting citations for non-existent indicator."""
    print("\nTesting GET /api/citations/{extracted_indicator_id} with invalid ID...")
    try:
        response = client.get("/api/citations/999999")
        if response.status_code == 404:
            print("✓ Correctly returned 404 for non-existent indicator")
            return True
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_get_document_page_url():
    """Test getting presigned URL for a document page."""
    print("\nTesting GET /api/documents/{object_key}/page/{page_number}...")
    try:
        # First get a company with indicators to find a valid object_key
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with indicators
        company_id = None
        for company in companies:
            if company.get('indicator_count', 0) > 0:
                company_id = company['id']
                break
        
        if not company_id:
            print("⚠ No companies with indicators available to test")
            return True
        
        # Get indicators to find an object_key
        response = client.get(f"/api/companies/{company_id}/indicators?skip=0&limit=1")
        if response.status_code != 200:
            print("✗ Failed to get indicators")
            return False
        
        data = response.json()
        if not data['indicators']:
            print("⚠ No indicators found")
            return True
        
        object_key = data['indicators'][0]['object_key']
        
        # Now get presigned URL for this document
        response = client.get(f"/api/documents/{object_key}/page/1")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Generated presigned URL for document '{object_key}'")
            print(f"  URL: {data['url'][:80]}...")
            print(f"  Page: {data['page_number']}")
            print(f"  Expires in: {data['expires_in']} seconds")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_get_document_page_url_not_found():
    """Test getting presigned URL for non-existent document."""
    print("\nTesting GET /api/documents/{object_key}/page/{page_number} with invalid object_key...")
    try:
        response = client.get("/api/documents/INVALID_COMPANY/2099_INVALID.pdf/page/1")
        if response.status_code == 404:
            print("✓ Correctly returned 404 for non-existent document")
            return True
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("Testing Citation Endpoints")
    print("=" * 80)
    
    tests = [
        test_database_connection,
        test_get_indicator_citations,
        test_get_indicator_citations_not_found,
        test_get_document_page_url,
        test_get_document_page_url_not_found,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 80)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 80)
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
