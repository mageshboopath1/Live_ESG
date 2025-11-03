"""Test script to verify database models and connection setup."""

import sys
from src.db import (
    CompanyCatalog,
    IngestionMetadata,
    DocumentEmbedding,
    BRSRIndicator,
    ExtractedIndicator,
    ESGScore,
    check_database_connection,
    get_db_context,
)


def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    if check_database_connection():
        print("✓ Database connection successful")
        return True
    else:
        print("✗ Database connection failed")
        return False


def test_models_import():
    """Test that all models can be imported."""
    print("\nTesting model imports...")
    models = [
        CompanyCatalog,
        IngestionMetadata,
        DocumentEmbedding,
        BRSRIndicator,
        ExtractedIndicator,
        ESGScore,
    ]
    
    for model in models:
        print(f"✓ {model.__name__} imported successfully")
    
    return True


def test_query_companies():
    """Test querying companies from database."""
    print("\nTesting database query...")
    try:
        with get_db_context() as db:
            companies = db.query(CompanyCatalog).limit(5).all()
            print(f"✓ Successfully queried {len(companies)} companies")
            
            if companies:
                print("\nSample companies:")
                for company in companies[:3]:
                    print(f"  - {company.company_name} ({company.symbol})")
            
            return True
    except Exception as e:
        print(f"✗ Query failed: {str(e)}")
        return False


def test_query_indicators():
    """Test querying BRSR indicators from database."""
    print("\nTesting BRSR indicators query...")
    try:
        with get_db_context() as db:
            indicators = db.query(BRSRIndicator).limit(5).all()
            print(f"✓ Successfully queried {len(indicators)} indicators")
            
            if indicators:
                print("\nSample indicators:")
                for indicator in indicators[:3]:
                    print(f"  - {indicator.indicator_code}: {indicator.parameter_name} (Pillar: {indicator.pillar})")
            
            return True
    except Exception as e:
        print(f"✗ Query failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: Model imports
    results.append(("Model Imports", test_models_import()))
    
    # Test 2: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 3: Query companies
    results.append(("Query Companies", test_query_companies()))
    
    # Test 4: Query indicators
    results.append(("Query Indicators", test_query_indicators()))
    
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
        print("\n✓ All tests passed! Database setup is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
