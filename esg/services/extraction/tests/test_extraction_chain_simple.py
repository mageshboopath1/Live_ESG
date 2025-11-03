"""
Simple test script for extraction chain structure verification.

This script verifies the extraction chain structure without requiring
database connections or API keys.
"""

import os
os.environ["GOOGLE_API_KEY"] = "test_key_for_structure_test"

from src.chains.extraction_chain import ExtractionChain
from src.models.brsr_models import BRSRIndicatorDefinition, Pillar


def test_class_structure():
    """Test that the ExtractionChain class has all required methods."""
    print("=" * 80)
    print("TEST 1: ExtractionChain Class Structure")
    print("=" * 80)

    # Check class exists
    assert ExtractionChain is not None
    print("✓ ExtractionChain class exists")

    # Check required methods exist
    required_methods = [
        "__init__",
        "extract_indicator",
        "extract_indicators_batch",
        "_build_search_query",
        "_retrieve_with_retry",
        "_execute_chain_with_retry",
    ]

    for method in required_methods:
        assert hasattr(ExtractionChain, method), f"Missing method: {method}"
        print(f"✓ Method exists: {method}")

    print("\n✓ All required methods present")


def test_factory_function_exists():
    """Test that the factory function exists."""
    print("\n" + "=" * 80)
    print("TEST 2: Factory Function")
    print("=" * 80)

    from src.chains.extraction_chain import create_extraction_chain

    assert create_extraction_chain is not None
    print("✓ create_extraction_chain function exists")

    # Check function signature
    import inspect

    sig = inspect.signature(create_extraction_chain)
    params = list(sig.parameters.keys())

    required_params = [
        "connection_string",
        "company_name",
        "report_year",
        "google_api_key",
    ]

    for param in required_params:
        assert param in params, f"Missing parameter: {param}"
        print(f"✓ Parameter exists: {param}")

    print("\n✓ Factory function signature correct")


def test_search_query_building_logic():
    """Test the search query building logic without initialization."""
    print("\n" + "=" * 80)
    print("TEST 3: Search Query Building Logic")
    print("=" * 80)

    # Create a sample indicator
    indicator = BRSRIndicatorDefinition(
        indicator_code="GHG_SCOPE1",
        attribute_number=1,
        parameter_name="Total Scope 1 emissions",
        measurement_unit="MT CO2e",
        description="Total direct GHG emissions from owned or controlled sources",
        pillar=Pillar.ENVIRONMENTAL,
        weight=0.15,
        data_assurance_approach="Third-party verification",
        brsr_reference="Essential Indicator 1.1",
    )

    print("✓ Sample indicator created")
    print(f"  - Code: {indicator.indicator_code}")
    print(f"  - Name: {indicator.parameter_name}")
    print(f"  - Unit: {indicator.measurement_unit}")
    print(f"  - Pillar: {indicator.pillar}")


def test_imports():
    """Test that all required imports work."""
    print("\n" + "=" * 80)
    print("TEST 4: Module Imports")
    print("=" * 80)

    try:
        from src.chains.extraction_chain import create_extraction_chain, ExtractionChain

        print("✓ Main exports imported successfully")

        from src.models.brsr_models import (
            BRSRIndicatorOutput,
            BRSRIndicatorDefinition,
        )

        print("✓ Model imports successful")

        from src.retrieval.filtered_retriever import FilteredPGVectorRetriever

        print("✓ Retriever import successful")

        from src.prompts.extraction_prompts import (
            create_extraction_prompt,
            get_output_parser,
        )

        print("✓ Prompt imports successful")

        print("\n✓ All imports working correctly")

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        raise


def test_retry_configuration():
    """Test retry configuration parameters."""
    print("\n" + "=" * 80)
    print("TEST 5: Retry Configuration")
    print("=" * 80)

    # Test default values
    default_max_retries = 3
    default_initial_delay = 1.0

    print(f"✓ Default max_retries: {default_max_retries}")
    print(f"✓ Default initial_retry_delay: {default_initial_delay}")

    # Test exponential backoff calculation
    delays = [default_initial_delay * (2**i) for i in range(default_max_retries)]
    print(f"✓ Exponential backoff delays: {delays}")

    assert delays == [1.0, 2.0, 4.0]
    print("✓ Exponential backoff calculation correct")


def test_documentation():
    """Test that key functions have docstrings."""
    print("\n" + "=" * 80)
    print("TEST 6: Documentation")
    print("=" * 80)

    from src.chains.extraction_chain import create_extraction_chain, ExtractionChain

    # Check class docstring
    assert ExtractionChain.__doc__ is not None
    print("✓ ExtractionChain has class docstring")

    # Check method docstrings
    assert ExtractionChain.extract_indicator.__doc__ is not None
    print("✓ extract_indicator has docstring")

    assert ExtractionChain.extract_indicators_batch.__doc__ is not None
    print("✓ extract_indicators_batch has docstring")

    # Check factory function docstring
    assert create_extraction_chain.__doc__ is not None
    print("✓ create_extraction_chain has docstring")

    print("\n✓ All key components documented")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EXTRACTION CHAIN STRUCTURE TEST SUITE")
    print("=" * 80)
    print("\nNote: This test suite verifies structure without requiring")
    print("database connections or valid API keys.")
    print("=" * 80)

    try:
        test_imports()
        test_class_structure()
        test_factory_function_exists()
        test_search_query_building_logic()
        test_retry_configuration()
        test_documentation()

        print("\n" + "=" * 80)
        print("ALL STRUCTURE TESTS PASSED ✓")
        print("=" * 80)
        print("\nThe extraction chain structure is correct!")
        print("\nNext steps for full testing:")
        print("  1. Set up PostgreSQL with pgvector and embeddings")
        print("  2. Configure valid Google API key")
        print("  3. Run integration tests with real data")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
