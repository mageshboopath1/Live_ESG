"""Test script to verify report endpoints."""

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


def test_list_company_reports():
    """Test listing reports for a company."""
    print("\nTesting GET /api/companies/{company_id}/reports...")
    try:
        # First get a company ID
        response = client.get("/api/companies?skip=0&limit=1")
        if response.status_code != 200 or not response.json()['companies']:
            print("✗ No companies available to test")
            return False
        
        company_id = response.json()['companies'][0]['id']
        company_name = response.json()['companies'][0]['company_name']
        
        # Now get reports for this company
        response = client.get(f"/api/companies/{company_id}/reports?skip=0&limit=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {len(data['reports'])} reports for {company_name} (total: {data['total']})")
            
            if data['reports']:
                print("\nSample reports:")
                for report in data['reports'][:3]:
                    print(f"  - {report['file_path']}")
                    print(f"    Year: {report['report_year']}, Type: {report['report_type']}")
                    print(f"    Status: {report['status']}, Embeddings: {report['has_embeddings']}, Extractions: {report['has_extractions']}")
            else:
                print("  (No reports found for this company)")
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_get_report_details():
    """Test getting report details by object key."""
    print("\nTesting GET /api/reports/{object_key}...")
    try:
        # First get a company with reports
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with reports
        object_key = None
        for company in companies:
            response = client.get(f"/api/companies/{company['id']}/reports?skip=0&limit=1")
            if response.status_code == 200 and response.json()['reports']:
                object_key = response.json()['reports'][0]['file_path']
                break
        
        if not object_key:
            print("⚠ No reports available to test (this is expected if no data has been ingested)")
            return True
        
        # Now get report details
        response = client.get(f"/api/reports/{object_key}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved report details: {data['file_path']}")
            print(f"  Company: {data['company_name']}")
            print(f"  Year: {data['report_year']}, Type: {data['report_type']}")
            print(f"  Status: {data['status']}")
            print(f"  Embeddings: {data['embedding_count']}, Extractions: {data['extraction_count']}")
            print(f"  Pages: {data['page_count']}, Chunks: {data['chunk_count']}")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_trigger_processing_validation():
    """Test trigger processing endpoint validation."""
    print("\nTesting POST /api/reports/trigger-processing (validation)...")
    try:
        # Test with non-existent object key
        response = client.post(
            "/api/reports/trigger-processing",
            json={"object_key": "NONEXISTENT/2024_BRSR.pdf", "force_reprocess": False}
        )
        
        if response.status_code == 404:
            print("✓ Correctly returns 404 for non-existent report")
            return True
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_trigger_processing_success():
    """Test trigger processing endpoint with valid data."""
    print("\nTesting POST /api/reports/trigger-processing (success case)...")
    try:
        # First get a company with reports that have embeddings
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a report with embeddings
        object_key = None
        for company in companies:
            response = client.get(f"/api/companies/{company['id']}/reports?skip=0&limit=10")
            if response.status_code == 200:
                reports = response.json()['reports']
                for report in reports:
                    if report['has_embeddings']:
                        object_key = report['file_path']
                        break
                if object_key:
                    break
        
        if not object_key:
            print("⚠ No reports with embeddings available to test (this is expected if no embeddings have been generated)")
            return True
        
        # Now trigger processing
        response = client.post(
            "/api/reports/trigger-processing",
            json={"object_key": object_key, "force_reprocess": False}
        )
        
        if response.status_code in [200, 202]:
            data = response.json()
            print(f"✓ Trigger processing response: {data['message']}")
            print(f"  Object key: {data['object_key']}")
            print(f"  Queued: {data['queued']}")
            print(f"  Already processed: {data['already_processed']}")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_reports_pagination():
    """Test pagination for reports endpoint."""
    print("\nTesting reports pagination...")
    try:
        # Get a company with multiple reports
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with reports
        company_id = None
        for company in companies:
            response = client.get(f"/api/companies/{company['id']}/reports?skip=0&limit=1")
            if response.status_code == 200 and response.json()['total'] > 0:
                company_id = company['id']
                break
        
        if not company_id:
            print("⚠ No companies with reports available to test pagination")
            return True
        
        # Test pagination
        response1 = client.get(f"/api/companies/{company_id}/reports?skip=0&limit=5")
        response2 = client.get(f"/api/companies/{company_id}/reports?skip=5&limit=5")
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            print(f"✓ Page 1: {len(data1['reports'])} reports")
            print(f"✓ Page 2: {len(data2['reports'])} reports")
            print(f"✓ Total reports: {data1['total']}")
            return True
        else:
            print(f"✗ Pagination test failed")
            return False
    except Exception as e:
        print(f"✗ Pagination test failed: {str(e)}")
        return False


def test_status_filter():
    """Test status filter for reports."""
    print("\nTesting status filter...")
    try:
        # Get a company with reports
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with reports
        company_id = None
        for company in companies:
            response = client.get(f"/api/companies/{company['id']}/reports?skip=0&limit=1")
            if response.status_code == 200 and response.json()['total'] > 0:
                company_id = company['id']
                break
        
        if not company_id:
            print("⚠ No companies with reports available to test filter")
            return True
        
        # Test with SUCCESS status filter
        response = client.get(f"/api/companies/{company_id}/reports?status_filter=SUCCESS")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Filter by status 'SUCCESS' returned {data['total']} reports")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Status filter test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Report Endpoints Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 2: List company reports
    results.append(("List Company Reports", test_list_company_reports()))
    
    # Test 3: Get report details
    results.append(("Get Report Details", test_get_report_details()))
    
    # Test 4: Trigger processing validation
    results.append(("Trigger Processing Validation", test_trigger_processing_validation()))
    
    # Test 5: Trigger processing success
    results.append(("Trigger Processing Success", test_trigger_processing_success()))
    
    # Test 6: Reports pagination
    results.append(("Reports Pagination", test_reports_pagination()))
    
    # Test 7: Status filter
    results.append(("Status Filter", test_status_filter()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Report endpoints are working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
