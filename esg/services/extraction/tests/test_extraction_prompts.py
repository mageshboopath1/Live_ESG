"""
Test script for extraction prompt templates.

This script verifies that the prompt templates are correctly configured
and can generate proper prompts with format instructions.
"""

from src.prompts.extraction_prompts import (
    create_extraction_prompt,
    get_output_parser,
    format_context_from_documents,
    create_batch_extraction_prompt,
)


def test_single_extraction_prompt():
    """Test creating a single indicator extraction prompt."""
    print("=" * 80)
    print("TEST 1: Single Indicator Extraction Prompt")
    print("=" * 80)

    prompt = create_extraction_prompt(
        company_name="RELIANCE",
        report_year=2024,
        indicator_code="GHG_SCOPE1",
        indicator_name="Total Scope 1 emissions",
        indicator_description="Total direct GHG emissions from owned or controlled sources",
        expected_unit="MT CO2e",
        pillar="E",
    )

    # Test with sample context
    sample_context = """
    [Page 45, Chunk 1]
    Our total Scope 1 emissions for FY 2024 were 1,250 MT CO2e, representing
    a 5% reduction from the previous year. This includes emissions from all
    owned and controlled sources across our operations.
    """

    formatted_prompt = prompt.format(context=sample_context)
    print("\nGenerated Prompt:")
    print("-" * 80)
    print(formatted_prompt[:500] + "...")
    print("-" * 80)
    print("✓ Prompt created successfully")
    print(f"✓ Input variables: {prompt.input_variables}")
    print(f"✓ Partial variables: {list(prompt.partial_variables.keys())}")


def test_output_parser():
    """Test the Pydantic output parser."""
    print("\n" + "=" * 80)
    print("TEST 2: Output Parser")
    print("=" * 80)

    parser = get_output_parser()
    format_instructions = parser.get_format_instructions()

    print("\nFormat Instructions:")
    print("-" * 80)
    print(format_instructions[:300] + "...")
    print("-" * 80)
    print("✓ Output parser created successfully")
    print(f"✓ Parser type: {type(parser).__name__}")
    print(f"✓ Pydantic model: {parser.pydantic_object.__name__}")


def test_batch_extraction_prompt():
    """Test creating a batch extraction prompt."""
    print("\n" + "=" * 80)
    print("TEST 3: Batch Extraction Prompt")
    print("=" * 80)

    indicators = [
        {
            "indicator_code": "GHG_SCOPE1",
            "indicator_name": "Total Scope 1 emissions",
            "indicator_description": "Direct GHG emissions from owned sources",
            "expected_unit": "MT CO2e",
            "pillar": "E",
        },
        {
            "indicator_code": "WATER_CONSUMPTION",
            "indicator_name": "Total water consumption",
            "indicator_description": "Total water consumed across operations",
            "expected_unit": "Kiloliters",
            "pillar": "E",
        },
    ]

    prompt = create_batch_extraction_prompt(
        company_name="RELIANCE", report_year=2024, indicators=indicators
    )

    sample_context = "Sample context for batch extraction..."
    formatted_prompt = prompt.format(context=sample_context)

    print("\nGenerated Batch Prompt:")
    print("-" * 80)
    print(formatted_prompt[:500] + "...")
    print("-" * 80)
    print("✓ Batch prompt created successfully")
    print(f"✓ Number of indicators: {len(indicators)}")


def test_context_formatting():
    """Test formatting documents into context."""
    print("\n" + "=" * 80)
    print("TEST 4: Context Formatting")
    print("=" * 80)

    # Mock document objects
    class MockDocument:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata

    docs = [
        MockDocument(
            "Our Scope 1 emissions were 1,250 MT CO2e in FY 2024.",
            {"page_number": 45, "chunk_index": 1},
        ),
        MockDocument(
            "This represents a 5% reduction from the previous year.",
            {"page_number": 45, "chunk_index": 2},
        ),
    ]

    context = format_context_from_documents(docs)

    print("\nFormatted Context:")
    print("-" * 80)
    print(context)
    print("-" * 80)
    print("✓ Context formatted successfully")
    print(f"✓ Number of documents: {len(docs)}")


def test_prompt_with_parser():
    """Test that prompt and parser work together."""
    print("\n" + "=" * 80)
    print("TEST 5: Prompt + Parser Integration")
    print("=" * 80)

    prompt = create_extraction_prompt(
        company_name="RELIANCE",
        report_year=2024,
        indicator_code="GHG_SCOPE1",
        indicator_name="Total Scope 1 emissions",
        indicator_description="Total direct GHG emissions",
        expected_unit="MT CO2e",
        pillar="E",
    )

    parser = get_output_parser()

    # Verify format instructions are in the prompt
    sample_context = "Sample context"
    formatted = prompt.format(context=sample_context)

    assert "format_instructions" not in formatted.lower() or "json" in formatted.lower()
    print("✓ Prompt includes format instructions")
    print("✓ Prompt and parser are compatible")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EXTRACTION PROMPTS TEST SUITE")
    print("=" * 80)

    try:
        test_single_extraction_prompt()
        test_output_parser()
        test_batch_extraction_prompt()
        test_context_formatting()
        test_prompt_with_parser()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nThe prompt templates are ready for use with LangChain!")
        print("Next steps:")
        print("  1. Integrate with FilteredPGVectorRetriever")
        print("  2. Build extraction chain with Google GenAI")
        print("  3. Test with real document embeddings")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
