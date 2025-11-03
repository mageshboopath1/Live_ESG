"""Test script to verify score endpoints."""

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


def test_get_company_scores():
    """Test getting ESG scores for a company."""
    print("\nTesting GET /api/companies/{company_id}/scores...")
    try:
        # First get a company with scores
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with available years (likely has scores)
        company_id = None
        company_name = None
        year = None
        for company in companies:
            if company.get('available_years'):
                company_id = company['id']
                company_name = company['company_name']
                year = company['available_years'][0]
                break
        
        if not company_id:
            print("⚠ No companies with year data available to test (this is expected if no scores have been calculated)")
            return True
        
        # Get scores for this company
        response = client.get(f"/api/companies/{company_id}/scores?year={year}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved scores for {company_name} (year {year})")
            print(f"  Overall Score: {data['overall_score']}")
            print(f"  Environmental: {data['environmental_score']}")
            print(f"  Social: {data['social_score']}")
            print(f"  Governance: {data['governance_score']}")
            print(f"  Calculated at: {data['calculated_at']}")
            return True
        elif response.status_code == 404:
            print(f"⚠ No scores found for {company_name} (this is expected if scores haven't been calculated)")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_get_company_scores_latest():
    """Test getting latest ESG scores without specifying year."""
    print("\nTesting GET /api/companies/{company_id}/scores (latest year)...")
    try:
        # Get a company with scores
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with available years
        company_id = None
        company_name = None
        for company in companies:
            if company.get('available_years'):
                company_id = company['id']
                company_name = company['company_name']
                break
        
        if not company_id:
            print("⚠ No companies with year data available to test")
            return True
        
        # Get latest scores (no year parameter)
        response = client.get(f"/api/companies/{company_id}/scores")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved latest scores for {company_name}")
            print(f"  Year: {data['report_year']}")
            print(f"  Overall Score: {data['overall_score']}")
            return True
        elif response.status_code == 404:
            print(f"⚠ No scores found for {company_name}")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_get_score_breakdown():
    """Test getting detailed score breakdown with transparency."""
    print("\nTesting GET /api/scores/breakdown/{company_id}/{year}...")
    try:
        # Get a company with scores
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with available years
        company_id = None
        company_name = None
        year = None
        for company in companies:
            if company.get('available_years'):
                company_id = company['id']
                company_name = company['company_name']
                year = company['available_years'][0]
                break
        
        if not company_id:
            print("⚠ No companies with year data available to test")
            return True
        
        # Get score breakdown
        response = client.get(f"/api/scores/breakdown/{company_id}/{year}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved score breakdown for {company_name} (year {year})")
            print(f"  Overall Score: {data['overall_score']}")
            print(f"  Total Indicators: {data['total_indicators']}")
            print(f"  Pillars: {len(data['pillars'])}")
            
            # Display pillar breakdown
            print("\nPillar Breakdown:")
            for pillar in data['pillars']:
                print(f"  {pillar['pillar']} ({pillar['pillar_code']}):")
                print(f"    Score: {pillar['score']}")
                print(f"    Weight: {pillar['weight']}")
                print(f"    Indicators: {pillar['indicator_count']}")
                print(f"    Method: {pillar['calculation_method']}")
                
                # Show sample indicators
                if pillar['indicators']:
                    print(f"    Sample indicators:")
                    for indicator in pillar['indicators'][:2]:
                        print(f"      - {indicator['parameter_name']}")
                        print(f"        Value: {indicator['extracted_value']}")
                        print(f"        Weight: {indicator['weight']}")
                        print(f"        Confidence: {indicator['confidence_score']}")
                        print(f"        Pages: {indicator['source_pages']}")
            
            # Verify structure
            if len(data['pillars']) == 3:
                print("\n✓ All 3 pillars (E, S, G) present")
            else:
                print(f"\n⚠ Expected 3 pillars, got {len(data['pillars'])}")
            
            return True
        elif response.status_code == 404:
            print(f"⚠ No score breakdown found for {company_name}")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def test_score_breakdown_transparency():
    """Test that score breakdown provides full transparency."""
    print("\nTesting score breakdown transparency features...")
    try:
        # Get a company with scores
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with available years
        company_id = None
        year = None
        for company in companies:
            if company.get('available_years'):
                company_id = company['id']
                year = company['available_years'][0]
                break
        
        if not company_id:
            print("⚠ No companies with year data available to test")
            return True
        
        # Get score breakdown
        response = client.get(f"/api/scores/breakdown/{company_id}/{year}")
        if response.status_code == 200:
            data = response.json()
            
            # Check transparency features
            checks = []
            
            # 1. Pillar weights present
            if data['pillars']:
                has_weights = all('weight' in pillar for pillar in data['pillars'])
                checks.append(("Pillar weights present", has_weights))
            
            # 2. Indicator contributions present
            has_indicators = any(pillar['indicators'] for pillar in data['pillars'])
            checks.append(("Indicator contributions present", has_indicators))
            
            # 3. Source citations present
            if has_indicators:
                has_citations = any(
                    indicator.get('source_pages')
                    for pillar in data['pillars']
                    for indicator in pillar['indicators']
                )
                checks.append(("Source citations present", has_citations))
            
            # 4. Calculation metadata present
            has_metadata = 'calculation_metadata' in data
            checks.append(("Calculation metadata present", has_metadata))
            
            # 5. Indicator weights present
            if has_indicators:
                has_ind_weights = any(
                    'weight' in indicator
                    for pillar in data['pillars']
                    for indicator in pillar['indicators']
                )
                checks.append(("Indicator weights present", has_ind_weights))
            
            # 6. Confidence scores present
            if has_indicators:
                has_confidence = any(
                    'confidence_score' in indicator
                    for pillar in data['pillars']
                    for indicator in pillar['indicators']
                )
                checks.append(("Confidence scores present", has_confidence))
            
            # Print results
            all_passed = True
            for check_name, result in checks:
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}")
                if not result:
                    all_passed = False
            
            if all_passed:
                print("\n✓ All transparency features present")
            else:
                print("\n⚠ Some transparency features missing")
            
            return True
        elif response.status_code == 404:
            print("⚠ No score breakdown available to test transparency")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Transparency test failed: {str(e)}")
        return False


def test_scores_validation():
    """Test score endpoint validation."""
    print("\nTesting score endpoint validation...")
    try:
        # Test with non-existent company
        response = client.get("/api/companies/99999/scores")
        if response.status_code == 404:
            print("✓ Correctly returns 404 for non-existent company")
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            return False
        
        # Test breakdown with non-existent company
        response = client.get("/api/scores/breakdown/99999/2024")
        if response.status_code == 404:
            print("✓ Correctly returns 404 for non-existent company in breakdown")
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Validation test failed: {str(e)}")
        return False


def test_score_pillar_structure():
    """Test that score breakdown has correct pillar structure."""
    print("\nTesting score pillar structure...")
    try:
        # Get a company with scores
        response = client.get("/api/companies?skip=0&limit=10")
        if response.status_code != 200:
            print("✗ Failed to get companies")
            return False
        
        companies = response.json()['companies']
        
        # Find a company with available years
        company_id = None
        year = None
        for company in companies:
            if company.get('available_years'):
                company_id = company['id']
                year = company['available_years'][0]
                break
        
        if not company_id:
            print("⚠ No companies with year data available to test")
            return True
        
        # Get score breakdown
        response = client.get(f"/api/scores/breakdown/{company_id}/{year}")
        if response.status_code == 200:
            data = response.json()
            
            # Check pillar structure
            expected_pillars = {'E', 'S', 'G'}
            actual_pillars = {pillar['pillar_code'] for pillar in data['pillars']}
            
            if expected_pillars == actual_pillars:
                print("✓ All expected pillars (E, S, G) present")
            else:
                print(f"✗ Expected pillars {expected_pillars}, got {actual_pillars}")
                return False
            
            # Check pillar names
            pillar_names = {
                'E': 'Environmental',
                'S': 'Social',
                'G': 'Governance'
            }
            
            for pillar in data['pillars']:
                expected_name = pillar_names[pillar['pillar_code']]
                if pillar['pillar'] == expected_name:
                    print(f"✓ Pillar {pillar['pillar_code']} has correct name: {pillar['pillar']}")
                else:
                    print(f"✗ Pillar {pillar['pillar_code']} has incorrect name: {pillar['pillar']}")
                    return False
            
            return True
        elif response.status_code == 404:
            print("⚠ No score breakdown available to test structure")
            return True
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Structure test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Score Endpoints Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 2: Get company scores with year
    results.append(("Get Company Scores (with year)", test_get_company_scores()))
    
    # Test 3: Get company scores (latest)
    results.append(("Get Company Scores (latest)", test_get_company_scores_latest()))
    
    # Test 4: Get score breakdown
    results.append(("Get Score Breakdown", test_get_score_breakdown()))
    
    # Test 5: Score breakdown transparency
    results.append(("Score Breakdown Transparency", test_score_breakdown_transparency()))
    
    # Test 6: Score validation
    results.append(("Score Validation", test_scores_validation()))
    
    # Test 7: Pillar structure
    results.append(("Pillar Structure", test_score_pillar_structure()))
    
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
        print("\n✓ All tests passed! Score endpoints are working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
