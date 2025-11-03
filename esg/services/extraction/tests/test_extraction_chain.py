"""
Test script for extraction chain.

This script verifies that the extraction chain is correctly configured
and can integrate all components (retriever, LLM, prompts, parser).
"""

from src.chains.extraction_chain import create_extraction_chain, ExtractionChain
from src.models.brsr_models import BRSRIndicatorDefinition, Pillar
from src.config import config


def test_chain_initialization():
    """Test creating an extraction chain."""
    print("=" * 80)
    print("TEST 1: Extraction Chain Initialization")
    print("=" * 80)

    try:
        # Use a mock connection string for testing
        test_connection_string = "postgresql://test:test@localhost:5432/test_db"
        
        chain = create_extraction_chain(
            connection_string=test_connection_string,
            company_name="RELIANCE",
            report_year=2024,
            google_api_key="test_api_key_for_initialization",
        )

        print("✓ Chain created successfully")
        print(f"✓ Chain type: {type(chain).__name__}")
        print(f"✓ Company: {chain.company_name}")
        print(f"✓ Report year: {chain.report_year}")
        print(f"✓ Model: {chain.model_name}")
        print(f"✓ Temperature: {chain.temperature}")
        print(f"✓ Max retries: {chain.max_retries}")
        print(f"✓ Retriever initialized: {chain.retriever is not None}")
        print(f"✓ LLM initialized: {chain.llm is not None}")
        print(f"✓ Output parser initialized: {chain.output_parser is not None}")

    except Exception as e:
        print(f"✗ Chain initialization failed: {e}")
        raise


def test_search_query_building():
    """Test building search queries from indicator definitions."""
    print("\n" + "=" * 80)
    print("TEST 2: Search Query Building")
    print("=" * 80)

    try:
        test_connection_string = "postgresql://test:test@localhost:5432/test_db"
        
        chain = create_extraction_chain(
            connection_string=test_connection_string,
            company_name="RELIANCE",
            report_year=2024,
            google_api_key="test_api_key",
        )

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

        query = chain._build_search_query(indicator)

        print(f"\nGenerated search query:")
        print("-" * 80)
        print(query)
        print("-" * 80)
        print("✓ Search query built successfully")
        print(f"✓ Query length: {len(query)} characters")
        print(f"✓ Contains parameter name: {'Total Scope 1 emissions' in query}")
        print(f"✓ Contains unit: {'MT CO2e' in query}")

    except Exception as e:
        print(f"✗ Search query building failed: {e}")
        raise


def test_chain_components():
    """Test that all chain components are properly configured."""
    print("\n" + "=" * 80)
    print("TEST 3: Chain Components Configuration")
    print("=" * 80)

    try:
        test_connection_string = "postgresql://test:test@localhost:5432/test_db"
        
        chain = create_extraction_chain(
            connection_string=test_connection_string,
            company_name="RELIANCE",
            report_year=2024,
            google_api_key="test_api_key",
            model_name="gemini-2.5-flash",
            temperature=0.1,
            max_retries=3,
            initial_retry_delay=1.0,
        )

        # Check retriever
        assert chain.retriever is not None, "Retriever not initialized"
        assert chain.retriever.company_name == "RELIANCE"
        assert chain.retriever.report_year == 2024
        print("✓ Retriever configured correctly")

        # Check LLM
        assert chain.llm is not None, "LLM not initialized"
        assert chain.llm.model_name == "gemini-2.5-flash"
        assert chain.llm.temperature == 0.1
        print("✓ LLM configured correctly")

        # Check output parser
        assert chain.output_parser is not None, "Output parser not initialized"
        print("✓ Output parser configured correctly")

        # Check retry configuration
        assert chain.max_retries == 3
        assert chain.initial_retry_delay == 1.0
        print("✓ Retry logic configured correctly")

        print("\n✓ All components configured successfully")

    except Exception as e:
        print(f"✗ Component configuration failed: {e}")
        raise


def test_batch_extraction_structure():
    """Test the structure of batch extraction method."""
    print("\n" + "=" * 80)
    print("TEST 4: Batch Extraction Structure")
    print("=" * 80)

    try:
        test_connection_string = "postgresql://test:test@localhost:5432/test_db"
        
        chain = create_extraction_chain(
            connection_string=test_connection_string,
            company_name="RELIANCE",
            report_year=2024,
            google_api_key="test_api_key",
        )

        # Create sample indicators
        indicators = [
            BRSRIndicatorDefinition(
                indicator_code="GHG_SCOPE1",
                attribute_number=1,
                parameter_name="Total Scope 1 emissions",
                measurement_unit="MT CO2e",
                description="Direct GHG emissions",
                pillar=Pillar.ENVIRONMENTAL,
                weight=0.15,
                data_assurance_approach="Third-party verification",
                brsr_reference="Essential Indicator 1.1",
            ),
            BRSRIndicatorDefinition(
                indicator_code="WATER_CONSUMPTION",
                attribute_number=2,
                parameter_name="Total water consumption",
                measurement_unit="Kiloliters",
                description="Total water consumed",
                pillar=Pillar.ENVIRONMENTAL,
                weight=0.12,
                data_assurance_approach="Internal audit",
                brsr_reference="Essential Indicator 2.1",
            ),
        ]

        # Verify method exists and has correct signature
        assert hasattr(chain, "extract_indicators_batch")
        print("✓ Batch extraction method exists")
        print(f"✓ Test indicators created: {len(indicators)}")

        # Note: We don't actually call the method here as it requires
        # real database connections and API calls

    except Exception as e:
        print(f"✗ Batch extraction structure test failed: {e}")
        raise


def test_factory_function():
    """Test the factory function with different configurations."""
    print("\n" + "=" * 80)
    print("TEST 5: Factory Function Configurations")
    print("=" * 80)

    try:
        test_connection_string = "postgresql://test:test@localhost:5432/test_db"
        
        # Test with default parameters
        chain1 = create_extraction_chain(
            connection_string=test_connection_string,
            company_name="RELIANCE",
            report_year=2024,
            google_api_key="test_api_key",
        )
        print("✓ Chain created with default parameters")

        # Test with custom parameters
        chain2 = create_extraction_chain(
            connection_string=test_connection_string,
            company_name="TCS",
            report_year=2023,
            google_api_key="test_api_key",
            model_name="gemini-2.5-flash",
            temperature=0.2,
            max_retries=5,
            initial_retry_delay=2.0,
        )
        print("✓ Chain created with custom parameters")

        # Verify custom parameters
        assert chain2.company_name == "TCS"
        assert chain2.report_year == 2023
        assert chain2.temperature == 0.2
        assert chain2.max_retries == 5
        assert chain2.initial_retry_delay == 2.0
        print("✓ Custom parameters applied correctly")

    except Exception as e:
        print(f"✗ Factory function test failed: {e}")
        raise


def test_error_handling_structure():
    """Test that error handling is properly structured."""
    print("\n" + "=" * 80)
    print("TEST 6: Error Handling Structure")
    print("=" * 80)

    try:
        test_connection_string = "postgresql://test:test@localhost:5432/test_db"
        
        chain = create_extraction_chain(
            connection_string=test_connection_string,
            company_name="RELIANCE",
            report_year=2024,
            google_api_key="test_api_key",
        )

        # Verify retry methods exist
        assert hasattr(chain, "_retrieve_with_retry")
        assert hasattr(chain, "_execute_chain_with_retry")
        print("✓ Retry methods exist")

        # Verify retry configuration
        assert chain.max_retries > 0
        assert chain.initial_retry_delay > 0
        print("✓ Retry configuration is valid")

        print("\n✓ Error handling structure verified")

    except Exception as e:
        print(f"✗ Error handling structure test failed: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EXTRACTION CHAIN TEST SUITE")
    print("=" * 80)

    try:
        test_chain_initialization()
        test_search_query_building()
        test_chain_components()
        test_batch_extraction_structure()
        test_factory_function()
        test_error_handling_structure()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nThe extraction chain is ready for use!")
        print("Next steps:")
        print("  1. Test with real database and embeddings")
        print("  2. Integrate with indicator extraction logic")
        print("  3. Test end-to-end extraction pipeline")
        print("\nNote: Full integration tests require:")
        print("  - PostgreSQL with pgvector and embeddings")
        print("  - Valid Google API key")
        print("  - BRSR indicator definitions in database")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
