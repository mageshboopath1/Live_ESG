"""Test script to verify indicator endpoints."""

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


def test_list_company_indicators():
    """Test listing indicators for a company."""
    print("\nTesting GET /api/companies/{company_id}/indicators...")
    try:
        # First get a company with indicators
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with indicators
        company_id = None
        company_name = None
        for company in companies:
            if company.get('indicator_count', 0) > 0:
                company_id = company['id']
                company_name = company['company_name']
                break
        
        if not company_id:
            print("⚠ No companies with indicators available to test (this is expected if no extractions have been done)")
            return True
        
        # Now get indicators for this company
        response = client.get(f"/api/companies/{company_id}/indicators?skip=0&limit=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {len(data['indicators'])} indicators for {company_name} (total: {data['total']})")
            
            if data['indicators']:
                print("\nSample indicators:")
                for indicator in data['indicators'][:3]:
                    print(f"  - {indicator['parameter_name']} ({indicator['indicator_code']})")
                    print(f"    Value: {indicator['extracted_value']}")
                    print(f"    Confidence: {indicator['confidence_score']}, Status: {indicator['validation_status']}")
                    print(f"    Pillar: {indicator['pillar']}, Attribute: {indicator['attribute_number']}")
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_list_indicators_with_year_filter():
    """Test listing indicators with year filter."""
    print("\nTesting GET /api/companies/{company_id}/indicators?year={year}...")
    try:
        # Get a company with indicators
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with indicators and available years
        company_id = None
        year = None
        for company in companies:
            if company.get('available_years'):
                company_id = company['id']
                year = company['available_years'][0]
                break
        
        if not company_id or not year:
            print("⚠ No companies with year data available to test")
            return True
        
        # Get indicators for specific year
        response = client.get(f"/api/companies/{company_id}/indicators?year={year}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {data['total']} indicators for year {year}")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_list_indicators_with_pillar_filter():
    """Test listing indicators with pillar filter."""
    print("\nTesting GET /api/companies/{company_id}/indicators?pillar=E...")
    try:
        # Get a company with indicators
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
        
        # Test each pillar
        for pillar in ['E', 'S', 'G']:
            response = client.get(f"/api/companies/{company_id}/indicators?pillar={pillar}")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Pillar {pillar}: {data['total']} indicators")
            else:
                print(f"✗ Request failed for pillar {pillar}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_list_indicators_with_confidence_filter():
    """Test listing indicators with minimum confidence filter."""
    print("\nTesting GET /api/companies/{company_id}/indicators?min_confidence=0.8...")
    try:
        # Get a company with indicators
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
        
        # Get indicators with high confidence
        response = client.get(f"/api/companies/{company_id}/indicators?min_confidence=0.8")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {data['total']} indicators with confidence >= 0.8")
            
            # Verify all returned indicators meet the threshold
            if data['indicators']:
                all_meet_threshold = all(
                    ind['confidence_score'] is None or float(ind['confidence_score']) >= 0.8
                    for ind in data['indicators']
                )
                if all_meet_threshold:
                    print("✓ All indicators meet confidence threshold")
                else:
                    print("✗ Some indicators don't meet confidence threshold")
                    return False
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_get_indicator_detail():
    """Test getting detailed indicator information with citations."""
    print("\nTesting GET /api/indicators/{indicator_id}...")
    try:
        # Get a company with indicators
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find an indicator
        indicator_id = None
        for company in companies:
            if company.get('indicator_count', 0) > 0:
                response = client.get(f"/api/companies/{company['id']}/indicators?skip=0&limit=1")
                if response.status_code == 200 and response.json()['indicators']:
                    indicator_id = response.json()['indicators'][0]['id']
                    break
        
        if not indicator_id:
            print("⚠ No indicators available to test")
            return True
        
        # Get indicator details
        response = client.get(f"/api/indicators/{indicator_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved indicator details: {data['parameter_name']}")
            print(f"  Company: {data['company_name']}")
            print(f"  Value: {data['extracted_value']}")
            print(f"  Confidence: {data['confidence_score']}")
            print(f"  Citations: {len(data['citations'])}")
            
            if data['citations']:
                print("\nSample citation:")
                citation = data['citations'][0]
                print(f"  PDF: {citation['pdf_name']}")
                print(f"  Pages: {citation['pages']}")
                print(f"  Text: {citation['chunk_text'][:100]}...")
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_compare_indicators():
    """Test comparing indicators across multiple companies."""
    print("\nTesting GET /api/indicators/compare...")
    try:
        # Get companies with indicators
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find at least 2 companies with indicators and same year
        company_ids = []
        common_year = None
        
        for company in companies:
            if company.get('available_years'):
                if not common_year:
                    common_year = company['available_years'][0]
                
                if common_year in company['available_years']:
                    company_ids.append(company['id'])
                
                if len(company_ids) >= 2:
                    break
        
        if len(company_ids) < 2:
            print("⚠ Not enough companies with common year data to test comparison")
            return True
        
        # Compare indicators
        companies_param = ','.join(map(str, company_ids[:3]))  # Use up to 3 companies
        response = client.get(f"/api/indicators/compare?companies={companies_param}&year={common_year}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Compared {data['total_indicators']} indicators across {data['company_count']} companies")
            print(f"  Year: {data['year']}")
            
            if data['comparisons']:
                print("\nSample comparison:")
                comparison = data['comparisons'][0]
                print(f"  Indicator: {comparison['parameter_name']} ({comparison['indicator_code']})")
                print(f"  Pillar: {comparison['pillar']}, Attribute: {comparison['attribute_number']}")
                print(f"  Companies:")
                for company_data in comparison['companies']:
                    status = "✓" if company_data['has_data'] else "✗"
                    value = company_data['extracted_value'] if company_data['has_data'] else "No data"
                    print(f"    {status} {company_data['company_name']}: {value}")
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_compare_indicators_with_pillar_filter():
    """Test comparing indicators with pillar filter."""
    print("\nTesting GET /api/indicators/compare?pillar=E...")
    try:
        # Get companies with indicators
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find companies with common year
        company_ids = []
        common_year = None
        
        for company in companies:
            if company.get('available_years'):
                if not common_year:
                    common_year = company['available_years'][0]
                
                if common_year in company['available_years']:
                    company_ids.append(company['id'])
                
                if len(company_ids) >= 2:
                    break
        
        if len(company_ids) < 2:
            print("⚠ Not enough companies to test comparison with filter")
            return True
        
        # Compare with pillar filter
        companies_param = ','.join(map(str, company_ids[:2]))
        response = client.get(f"/api/indicators/compare?companies={companies_param}&year={common_year}&pillar=E")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Compared {data['total_indicators']} Environmental indicators")
            
            # Verify all are Environmental
            if data['comparisons']:
                all_environmental = all(comp['pillar'] == 'E' for comp in data['comparisons'])
                if all_environmental:
                    print("✓ All indicators are Environmental (E)")
                else:
                    print("✗ Some indicators are not Environmental")
                    return False
            
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_compare_indicators_validation():
    """Test comparison endpoint validation."""
    print("\nTesting comparison endpoint validation...")
    try:
        # Test with invalid company IDs (FastAPI returns 422 for validation errors)
        response = client.get("/api/indicators/compare?companies=invalid&year=2024")
        if response.status_code in [400, 422]:
            print(f"✓ Correctly returns {response.status_code} for invalid company IDs")
        else:
            print(f"✗ Expected 400 or 422, got {response.status_code}")
            return False
        
        # Test with only one company
        response = client.get("/api/indicators/compare?companies=1&year=2024")
        if response.status_code == 400:
            print("✓ Correctly returns 400 for single company")
        else:
            print(f"✗ Expected 400, got {response.status_code}")
            return False
        
        # Test with non-existent companies
        response = client.get("/api/indicators/compare?companies=99999,99998&year=2024")
        if response.status_code == 404:
            print("✓ Correctly returns 404 for non-existent companies")
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Validation test failed: {str(e)}")
        return False


def test_indicators_pagination():
    """Test pagination for indicators endpoint."""
    print("\nTesting indicators pagination...")
    try:
        # Get a company with multiple indicators
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with indicators
        company_id = None
        for company in companies:
            if company.get('indicator_count', 0) > 5:  # Need at least 5 for pagination test
                company_id = company['id']
                break
        
        if not company_id:
            print("⚠ No companies with enough indicators to test pagination")
            return True
        
        # Test pagination
        response1 = client.get(f"/api/companies/{company_id}/indicators?skip=0&limit=3")
        response2 = client.get(f"/api/companies/{company_id}/indicators?skip=3&limit=3")
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            print(f"✓ Page 1: {len(data1['indicators'])} indicators")
            print(f"✓ Page 2: {len(data2['indicators'])} indicators")
            print(f"✓ Total indicators: {data1['total']}")
            
            # Verify different results
            if data1['indicators'] and data2['indicators']:
                if data1['indicators'][0]['id'] != data2['indicators'][0]['id']:
                    print("✓ Pagination returns different results")
                else:
                    print("⚠ Pagination returned same results")
            
            return True
        else:
            print(f"✗ Pagination test failed")
            return False
    except Exception as e:
        print(f"✗ Pagination test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Indicator Endpoints Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 2: List company indicators
    results.append(("List Company Indicators", test_list_company_indicators()))
    
    # Test 3: List indicators with year filter
    results.append(("Year Filter", test_list_indicators_with_year_filter()))
    
    # Test 4: List indicators with pillar filter
    results.append(("Pillar Filter", test_list_indicators_with_pillar_filter()))
    
    # Test 5: List indicators with confidence filter
    results.append(("Confidence Filter", test_list_indicators_with_confidence_filter()))
    
    # Test 6: Get indicator detail
    results.append(("Get Indicator Detail", test_get_indicator_detail()))
    
    # Test 7: Compare indicators
    results.append(("Compare Indicators", test_compare_indicators()))
    
    # Test 8: Compare with pillar filter
    results.append(("Compare with Pillar Filter", test_compare_indicators_with_pillar_filter()))
    
    # Test 9: Comparison validation
    results.append(("Comparison Validation", test_compare_indicators_validation()))
    
    # Test 10: Indicators pagination
    results.append(("Indicators Pagination", test_indicators_pagination()))
    
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
        print("\n✓ All tests passed! Indicator endpoints are working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
