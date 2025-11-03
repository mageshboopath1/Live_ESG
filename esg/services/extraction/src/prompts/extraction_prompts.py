"""
LangChain prompt templates for BRSR Core indicator extraction.

This module provides prompt templates and output parsers for extracting
structured BRSR Core indicators from company sustainability reports using
Google GenAI with LangChain.

The prompts are designed to:
1. Extract specific BRSR indicators with high accuracy
2. Include confidence scoring for each extraction
3. Identify source page numbers for transparency
4. Handle both quantitative and qualitative indicators
5. Provide structured output using Pydantic models

Requirements: 6.2, 6.3, 11.3
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from ..models.brsr_models import BRSRIndicatorOutput


# Main extraction template for BRSR Core indicators
EXTRACTION_TEMPLATE = """You are an expert ESG analyst tasked with extracting specific BRSR Core indicators from company sustainability reports.

**Company Context:**
Company Name: {company_name}
Report Year: {report_year}
Report Type: BRSR (Business Responsibility and Sustainability Report)

**Indicator to Extract:**
Indicator Code: {indicator_code}
Parameter Name: {indicator_name}
Description: {indicator_description}
Expected Unit: {expected_unit}
Pillar: {pillar} (Environmental/Social/Governance)

**Instructions:**
1. Carefully read the provided context from the company's report
2. Extract the EXACT value for the specified indicator
3. If the value is numeric, extract both the text value and numeric representation
4. Identify the unit of measurement (use the expected unit if found, or determine from context)
5. Provide a confidence score (0.0-1.0) based on:
   - 1.0: Value explicitly stated with clear labeling
   - 0.8-0.9: Value clearly stated but requires minor interpretation
   - 0.6-0.7: Value found but requires moderate interpretation or calculation
   - 0.4-0.5: Value inferred from related information
   - 0.0-0.3: Value not found or highly uncertain
6. Record ALL page numbers where relevant information was found
7. If the indicator is not found in the context, return confidence 0.0 and value "Not Found"

**Context from {company_name} {report_year} Report:**
{context}

**Output Requirements:**
{format_instructions}

**Important Notes:**
- Extract values EXACTLY as stated in the document
- Do not make assumptions or calculations unless explicitly required by the indicator definition
- For qualitative indicators (Yes/No, descriptions), extract the exact text
- Always include page numbers for traceability
- Be conservative with confidence scores - only use high scores when certain
"""


# Alternative template for batch extraction of multiple indicators
BATCH_EXTRACTION_TEMPLATE = """You are an expert ESG analyst tasked with extracting multiple BRSR Core indicators from company sustainability reports.

**Company Context:**
Company Name: {company_name}
Report Year: {report_year}
Report Type: BRSR (Business Responsibility and Sustainability Report)

**Indicators to Extract:**
{indicators_list}

**Instructions:**
1. For each indicator listed above, extract the value from the provided context
2. Follow the same extraction guidelines as for single indicators
3. Provide confidence scores and source pages for each indicator
4. If an indicator is not found, mark it with confidence 0.0 and value "Not Found"

**Context from {company_name} {report_year} Report:**
{context}

**Output Requirements:**
Return a JSON array of indicator extractions, where each element follows this structure:
{format_instructions}

**Important Notes:**
- Process all indicators even if some are not found
- Maintain high accuracy over speed
- Always include source page numbers for transparency
"""


def create_extraction_prompt(
    company_name: str,
    report_year: int,
    indicator_code: str,
    indicator_name: str,
    indicator_description: str,
    expected_unit: str,
    pillar: str,
) -> PromptTemplate:
    """
    Create a LangChain PromptTemplate for extracting a single BRSR indicator.

    This function creates a prompt template that includes all necessary context
    for the LLM to extract a specific indicator with high accuracy and transparency.

    Args:
        company_name: Name of the company (e.g., "RELIANCE")
        report_year: Year of the report (e.g., 2024)
        indicator_code: BRSR indicator code (e.g., "GHG_SCOPE1")
        indicator_name: Human-readable indicator name (e.g., "Total Scope 1 emissions")
        indicator_description: Detailed description of what to extract
        expected_unit: Expected unit of measurement (e.g., "MT CO2e")
        pillar: ESG pillar - "E" (Environmental), "S" (Social), or "G" (Governance)

    Returns:
        PromptTemplate configured with the extraction template and output parser

    Requirements: 6.2, 6.3, 11.3

    Example:
        >>> prompt = create_extraction_prompt(
        ...     company_name="RELIANCE",
        ...     report_year=2024,
        ...     indicator_code="GHG_SCOPE1",
        ...     indicator_name="Total Scope 1 emissions",
        ...     indicator_description="Total direct GHG emissions from owned or controlled sources",
        ...     expected_unit="MT CO2e",
        ...     pillar="E"
        ... )
        >>> # Use with LangChain chain
        >>> chain = prompt | llm | output_parser
    """
    # Get the output parser for structured output
    output_parser = get_output_parser()

    # Create the prompt template with all required variables
    prompt = PromptTemplate(
        template=EXTRACTION_TEMPLATE,
        input_variables=[
            "company_name",
            "report_year",
            "indicator_code",
            "indicator_name",
            "indicator_description",
            "expected_unit",
            "pillar",
            "context",
        ],
        partial_variables={
            "format_instructions": output_parser.get_format_instructions(),
            "company_name": company_name,
            "report_year": str(report_year),
            "indicator_code": indicator_code,
            "indicator_name": indicator_name,
            "indicator_description": indicator_description,
            "expected_unit": expected_unit,
            "pillar": pillar,
        },
    )

    return prompt


def get_output_parser() -> PydanticOutputParser:
    """
    Get a PydanticOutputParser configured for BRSRIndicatorOutput.

    This parser ensures that the LLM output is structured according to the
    BRSRIndicatorOutput Pydantic model, with automatic validation of:
    - Confidence scores (0.0-1.0)
    - Source pages (non-empty list of positive integers)
    - Required fields (indicator_code, value, unit, etc.)

    Returns:
        PydanticOutputParser configured for BRSRIndicatorOutput model

    Requirements: 6.3, 11.3

    Example:
        >>> parser = get_output_parser()
        >>> result = parser.parse(llm_output)
        >>> print(result.indicator_code, result.confidence)
    """
    return PydanticOutputParser(pydantic_object=BRSRIndicatorOutput)


def create_batch_extraction_prompt(
    company_name: str,
    report_year: int,
    indicators: list[dict],
) -> PromptTemplate:
    """
    Create a LangChain PromptTemplate for extracting multiple BRSR indicators.

    This function creates a prompt template for batch extraction of multiple
    indicators from the same document context, which can be more efficient
    than individual extractions.

    Args:
        company_name: Name of the company (e.g., "RELIANCE")
        report_year: Year of the report (e.g., 2024)
        indicators: List of indicator dictionaries, each containing:
            - indicator_code: str
            - indicator_name: str
            - indicator_description: str
            - expected_unit: str
            - pillar: str

    Returns:
        PromptTemplate configured for batch extraction

    Requirements: 6.2, 6.3, 11.3, 12.2

    Example:
        >>> indicators = [
        ...     {
        ...         "indicator_code": "GHG_SCOPE1",
        ...         "indicator_name": "Total Scope 1 emissions",
        ...         "indicator_description": "Direct GHG emissions",
        ...         "expected_unit": "MT CO2e",
        ...         "pillar": "E"
        ...     },
        ...     # ... more indicators
        ... ]
        >>> prompt = create_batch_extraction_prompt("RELIANCE", 2024, indicators)
    """
    # Format indicators list for the prompt
    indicators_list = "\n".join(
        [
            f"{i+1}. {ind['indicator_code']} - {ind['indicator_name']}\n"
            f"   Description: {ind['indicator_description']}\n"
            f"   Expected Unit: {ind['expected_unit']}\n"
            f"   Pillar: {ind['pillar']}"
            for i, ind in enumerate(indicators)
        ]
    )

    # Get the output parser
    output_parser = get_output_parser()

    # Create the prompt template
    prompt = PromptTemplate(
        template=BATCH_EXTRACTION_TEMPLATE,
        input_variables=["context"],
        partial_variables={
            "company_name": company_name,
            "report_year": str(report_year),
            "indicators_list": indicators_list,
            "format_instructions": output_parser.get_format_instructions(),
        },
    )

    return prompt


def format_context_from_documents(documents: list) -> str:
    """
    Format retrieved documents into a context string for the prompt.

    This helper function takes LangChain Document objects from the retriever
    and formats them into a readable context string with page numbers.

    Args:
        documents: List of LangChain Document objects with page_content and metadata

    Returns:
        Formatted context string with page numbers and chunk text

    Example:
        >>> docs = retriever.get_relevant_documents(query)
        >>> context = format_context_from_documents(docs)
        >>> # Use context in prompt
    """
    if not documents:
        return "No relevant context found in the document."

    context_parts = []
    for i, doc in enumerate(documents, 1):
        page_num = doc.metadata.get("page_number", "Unknown")
        chunk_text = doc.page_content
        context_parts.append(f"[Page {page_num}, Chunk {i}]\n{chunk_text}")

    return "\n\n---\n\n".join(context_parts)
