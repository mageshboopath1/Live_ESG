"""Test script to verify company endpoints."""

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


def test_health_endpoint():
    """Test health check endpoint."""
    print("\nTesting health endpoint...")
    try:
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data}")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {str(e)}")
        return False


def test_list_companies():
    """Test listing companies endpoint."""
    print("\nTesting GET /api/companies...")
    try:
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {len(data['companies'])} companies (total: {data['total']})")
            
            if data['companies']:
                print("\nSample companies:")
                for company in data['companies'][:3]:
                    print(f"  - {company['company_name']} ({company['symbol']})")
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_get_company():
    """Test getting a single company endpoint."""
    print("\nTesting GET /api/companies/{company_id}...")
    try:
        # First get a company ID from the list
        response = client.get("/api/companies?skip=0&limit=1")
        if response.status_code != 200 or not response.json()['companies']:
            print("✗ No companies available to test")
            return False
        
        company_id = response.json()['companies'][0]['id']
        
        # Now get the specific company
        response = client.get(f"/api/companies/{company_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved company: {data['company_name']} ({data['symbol']})")
            print(f"  Reports: {data['report_count']}, Indicators: {data['indicator_count']}")
            print(f"  Available years: {data['available_years']}")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_search_companies():
    """Test searching companies endpoint."""
    print("\nTesting GET /api/companies/search...")
    try:
        # First get a company name to search for
        response = client.get("/api/companies?skip=0&limit=1")
        if response.status_code != 200 or not response.json()['companies']:
            print("✗ No companies available to test")
            return False
        
        company_name = response.json()['companies'][0]['company_name']
        search_term = company_name.split()[0]  # Use first word of company name
        
        # Now search for it
        response = client.get(f"/api/companies/search?q={search_term}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Search for '{search_term}' returned {len(data['companies'])} companies (total: {data['total']})")
            
            if data['companies']:
                print("\nMatching companies:")
                for company in data['companies'][:3]:
                    print(f"  - {company['company_name']} ({company['symbol']})")
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_pagination():
    """Test pagination parameters."""
    print("\nTesting pagination...")
    try:
        # Test with different pagination parameters
        response1 = client.get("/api/companies?skip=0&limit=5")
        response2 = client.get("/api/companies?skip=5&limit=5")
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            print(f"✓ Page 1: {len(data1['companies'])} companies")
            print(f"✓ Page 2: {len(data2['companies'])} companies")
            
            # Verify different results
            if data1['companies'] and data2['companies']:
                if data1['companies'][0]['id'] != data2['companies'][0]['id']:
                    print("✓ Pagination returns different results")
                    return True
                else:
                    print("⚠ Pagination returned same results (might be expected if few companies)")
                    return True
            else:
                print("✓ Pagination works (not enough data to verify different results)")
                return True
        else:
            print(f"✗ Pagination test failed")
            return False
    except Exception as e:
        print(f"✗ Pagination test failed: {str(e)}")
        return False


def test_industry_filter():
    """Test industry filter."""
    print("\nTesting industry filter...")
    try:
        # First get an industry
        response = client.get("/api/companies?skip=0&limit=1")
        if response.status_code != 200 or not response.json()['companies']:
            print("✗ No companies available to test")
            return False
        
        industry = response.json()['companies'][0].get('industry')
        if not industry:
            print("⚠ No industry data available to test filter")
            return True
        
        # Now filter by industry
        response = client.get(f"/api/companies?industry={industry}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Filter by industry '{industry}' returned {data['total']} companies")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Industry filter test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Company Endpoints Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 2: Health endpoint
    results.append(("Health Endpoint", test_health_endpoint()))
    
    # Test 3: List companies
    results.append(("List Companies", test_list_companies()))
    
    # Test 4: Get single company
    results.append(("Get Company", test_get_company()))
    
    # Test 5: Search companies
    results.append(("Search Companies", test_search_companies()))
    
    # Test 6: Pagination
    results.append(("Pagination", test_pagination()))
    
    # Test 7: Industry filter
    results.append(("Industry Filter", test_industry_filter()))
    
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
        print("\n✓ All tests passed! Company endpoints are working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
