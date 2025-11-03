"""
LangChain extraction chain for BRSR Core indicator extraction.

This module provides the main extraction chain that combines:
1. FilteredPGVectorRetriever for company/year-specific document retrieval
2. Google GenAI (gemini-2.5-flash) for LLM-based extraction
3. Prompt templates for structured indicator extraction
4. Retry logic with exponential backoff for API failures

The chain follows the RAG (Retrieval-Augmented Generation) pattern to ensure
accurate, grounded extractions with source citations.

Requirements: 6.2, 6.3, 11.2, 11.4, 11.5
"""

import logging
import time
from typing import Optional, Dict, Any, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import PydanticOutputParser

from ..models.brsr_models import BRSRIndicatorOutput, BRSRIndicatorDefinition
from ..retrieval.filtered_retriever import FilteredPGVectorRetriever
from ..prompts.extraction_prompts import (
    create_extraction_prompt,
    get_output_parser,
    format_context_from_documents,
)

logger = logging.getLogger(__name__)


class ExtractionChain:
    """
    LangChain-based extraction chain for BRSR Core indicators.
    
    This class encapsulates the complete extraction pipeline:
    - Filtered vector retrieval by company and year
    - LLM-based extraction with structured output
    - Retry logic with exponential backoff
    - Error handling and logging
    
    Requirements: 6.2, 6.3, 11.2, 11.4, 11.5
    """
    
    def __init__(
        self,
        connection_string: str,
        company_name: str,
        report_year: int,
        google_api_key: str,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.1,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
    ):
        """
        Initialize the extraction chain.
        
        Args:
            connection_string: PostgreSQL connection string
            company_name: Company name for filtering
            report_year: Report year for filtering
            google_api_key: Google GenAI API key
            model_name: Google GenAI model name (default: gemini-2.5-flash)
            temperature: LLM temperature for extraction (default: 0.1 for consistency)
            max_retries: Maximum number of retry attempts for API failures
            initial_retry_delay: Initial delay in seconds for exponential backoff
        """
        self.connection_string = connection_string
        self.company_name = company_name
        self.report_year = report_year
        self.google_api_key = google_api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        
        # Initialize retriever
        # Note: FilteredPGVectorRetriever will initialize GoogleGenerativeAIEmbeddings
        # which reads the API key from GOOGLE_API_KEY environment variable
        # Use models/text-embedding-004 with 768 dimensions (matches database embeddings)
        self.retriever = FilteredPGVectorRetriever(
            connection_string=connection_string,
            company_name=company_name,
            report_year=report_year,
            embedding_model="models/text-embedding-004",
        )
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=google_api_key,
        )
        
        # Initialize output parser
        self.output_parser = get_output_parser()
        
        logger.info(
            f"Initialized ExtractionChain for company={company_name}, "
            f"year={report_year}, model={model_name}"
        )
    
    def extract_indicator(
        self,
        indicator: BRSRIndicatorDefinition,
        k: int = 10,
    ) -> BRSRIndicatorOutput:
        """
        Extract a single BRSR indicator from the company's report.
        
        This method:
        1. Retrieves relevant document chunks using filtered vector search
        2. Constructs a prompt with indicator details and context
        3. Executes the LLM chain with retry logic
        4. Parses and validates the structured output
        
        Args:
            indicator: BRSR indicator definition to extract
            k: Number of document chunks to retrieve (default: 10)
            
        Returns:
            BRSRIndicatorOutput with extracted value, confidence, and citations
            
        Raises:
            Exception: If extraction fails after all retries
            
        Requirements: 6.2, 6.3, 11.2, 11.4, 11.5
        """
        logger.info(
            f"Extracting indicator {indicator.indicator_code} "
            f"({indicator.parameter_name})"
        )
        
        # Build search query from indicator details
        query = self._build_search_query(indicator)
        
        # Retrieve relevant documents with retry logic
        documents = self._retrieve_with_retry(query, k)
        
        if not documents:
            logger.warning(
                f"No documents retrieved for indicator {indicator.indicator_code}"
            )
            # Return a "not found" result
            return BRSRIndicatorOutput(
                indicator_code=indicator.indicator_code,
                value="Not Found",
                numeric_value=None,
                unit=indicator.measurement_unit or "N/A",
                confidence=0.0,
                source_pages=[],
            )
        
        # Format context from retrieved documents
        context = format_context_from_documents(documents)
        
        # Create extraction prompt
        prompt = create_extraction_prompt(
            company_name=self.company_name,
            report_year=self.report_year,
            indicator_code=indicator.indicator_code,
            indicator_name=indicator.parameter_name,
            indicator_description=indicator.description,
            expected_unit=indicator.measurement_unit or "N/A",
            pillar=indicator.pillar.value,
        )
        
        # Build and execute chain with retry logic
        result = self._execute_chain_with_retry(prompt, context)
        
        logger.info(
            f"Successfully extracted indicator {indicator.indicator_code} "
            f"with confidence {result.confidence:.2f}"
        )
        
        return result
    
    def _build_search_query(self, indicator: BRSRIndicatorDefinition) -> str:
        """
        Build a search query from indicator definition.
        
        Args:
            indicator: BRSR indicator definition
            
        Returns:
            Search query string optimized for vector similarity
        """
        # Combine indicator name and description for better retrieval
        query_parts = [
            indicator.parameter_name,
            indicator.description,
        ]
        
        # Add measurement unit if available
        if indicator.measurement_unit:
            query_parts.append(indicator.measurement_unit)
        
        query = " ".join(query_parts)
        logger.debug(f"Built search query: {query[:200]}...")
        
        return query
    
    def _retrieve_with_retry(
        self,
        query: str,
        k: int,
    ) -> List[Any]:
        """
        Retrieve documents with retry logic for transient failures.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents
            
        Raises:
            Exception: If retrieval fails after all retries
            
        Requirements: 11.5
        """
        for attempt in range(self.max_retries):
            try:
                documents = self.retriever.get_relevant_documents(query, k)
                if attempt > 0:
                    logger.info(
                        f"Retrieval succeeded on attempt {attempt + 1}",
                        extra={
                            "company_name": self.company_name,
                            "report_year": self.report_year,
                            "attempt": attempt + 1,
                            "documents_retrieved": len(documents)
                        }
                    )
                return documents
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.initial_retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Retrieval attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                        f"Retrying in {delay}s...",
                        extra={
                            "company_name": self.company_name,
                            "report_year": self.report_year,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "retry_delay": delay,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Retrieval failed after {self.max_retries} attempts: {e}",
                        exc_info=True,
                        extra={
                            "company_name": self.company_name,
                            "report_year": self.report_year,
                            "max_retries": self.max_retries,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "final_failure": True
                        }
                    )
                    raise
        
        return []
    
    def _execute_chain_with_retry(
        self,
        prompt: Any,
        context: str,
    ) -> BRSRIndicatorOutput:
        """
        Execute the LLM chain with exponential backoff retry logic.
        
        This method handles transient API failures (rate limits, network issues)
        by retrying with exponentially increasing delays. All retry attempts are
        logged with detailed context for monitoring and debugging.
        
        Args:
            prompt: LangChain PromptTemplate
            context: Formatted context from retrieved documents
            
        Returns:
            Parsed BRSRIndicatorOutput
            
        Raises:
            Exception: If extraction fails after all retries
            
        Requirements: 11.5, 9.1, 9.2
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Build the chain: prompt -> LLM -> output parser
                chain = prompt | self.llm | self.output_parser
                
                # Execute the chain with context
                result = chain.invoke({"context": context})
                
                # Log successful extraction after retry
                if attempt > 0:
                    logger.info(
                        f"LLM extraction succeeded on attempt {attempt + 1}",
                        extra={
                            "company_name": self.company_name,
                            "report_year": self.report_year,
                            "model_name": self.model_name,
                            "attempt": attempt + 1,
                            "confidence": result.confidence if hasattr(result, 'confidence') else None
                        }
                    )
                
                return result
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_message = str(e)
                
                # Check if it's a rate limit error
                is_rate_limit = "rate" in error_message.lower() or "quota" in error_message.lower()
                
                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay
                    delay = self.initial_retry_delay * (2 ** attempt)
                    
                    # Add extra delay for rate limit errors
                    if is_rate_limit:
                        delay *= 2
                    
                    logger.warning(
                        f"LLM API error on attempt {attempt + 1}/{self.max_retries}: {error_type} - {error_message}. "
                        f"Retrying in {delay}s...",
                        extra={
                            "company_name": self.company_name,
                            "report_year": self.report_year,
                            "model_name": self.model_name,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "retry_delay": delay,
                            "error_type": error_type,
                            "error_message": error_message,
                            "is_rate_limit": is_rate_limit
                        }
                    )
                    
                    time.sleep(delay)
                else:
                    logger.error(
                        f"LLM API error after {self.max_retries} attempts: {error_type} - {error_message}",
                        exc_info=True,
                        extra={
                            "company_name": self.company_name,
                            "report_year": self.report_year,
                            "model_name": self.model_name,
                            "max_retries": self.max_retries,
                            "error_type": error_type,
                            "error_message": error_message,
                            "is_rate_limit": is_rate_limit,
                            "final_failure": True
                        }
                    )
                    raise
        
        # This should never be reached, but added for type safety
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in retry logic")
    
    def extract_indicators_batch(
        self,
        indicators: List[BRSRIndicatorDefinition],
        k: int = 10,
    ) -> List[BRSRIndicatorOutput]:
        """
        Extract multiple indicators sequentially.
        
        Note: This method extracts indicators one by one. For true batch extraction
        with a single LLM call, use the batch extraction prompt template.
        
        Args:
            indicators: List of BRSR indicator definitions
            k: Number of document chunks to retrieve per indicator
            
        Returns:
            List of BRSRIndicatorOutput objects
            
        Requirements: 12.1, 12.2
        """
        results = []
        
        for i, indicator in enumerate(indicators, 1):
            logger.info(
                f"Extracting indicator {i}/{len(indicators)}: "
                f"{indicator.indicator_code}"
            )
            
            try:
                result = self.extract_indicator(indicator, k)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Failed to extract indicator {indicator.indicator_code}: {e}. "
                    f"Continuing with next indicator..."
                )
                # Create a failed result
                failed_result = BRSRIndicatorOutput(
                    indicator_code=indicator.indicator_code,
                    value="Extraction Failed",
                    numeric_value=None,
                    unit=indicator.measurement_unit or "N/A",
                    confidence=0.0,
                    source_pages=[],
                )
                results.append(failed_result)
        
        logger.info(
            f"Batch extraction complete. Successfully extracted "
            f"{sum(1 for r in results if r.confidence > 0.0)}/{len(results)} indicators"
        )
        
        return results


def create_extraction_chain(
    connection_string: str,
    company_name: str,
    report_year: int,
    google_api_key: str,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.1,
    max_retries: int = 3,
    initial_retry_delay: float = 1.0,
) -> ExtractionChain:
    """
    Factory function to create an ExtractionChain instance.
    
    This is the main entry point for creating extraction chains. It initializes
    all necessary components (retriever, LLM, parser) and returns a ready-to-use
    chain for indicator extraction.
    
    Args:
        connection_string: PostgreSQL connection string
        company_name: Company name for filtering (e.g., "RELIANCE")
        report_year: Report year for filtering (e.g., 2024)
        google_api_key: Google GenAI API key
        model_name: Google GenAI model name (default: gemini-2.5-flash)
        temperature: LLM temperature (default: 0.1 for consistent extraction)
        max_retries: Maximum retry attempts for API failures (default: 3)
        initial_retry_delay: Initial retry delay in seconds (default: 1.0)
        
    Returns:
        Configured ExtractionChain ready for indicator extraction
        
    Requirements: 6.2, 6.3, 11.2, 11.4, 11.5
    
    Example:
        >>> from src.config import config
        >>> from src.db.repository import load_brsr_indicators
        >>> 
        >>> # Create extraction chain
        >>> chain = create_extraction_chain(
        ...     connection_string=config.database_url,
        ...     company_name="RELIANCE",
        ...     report_year=2024,
        ...     google_api_key=config.google_api_key,
        ... )
        >>> 
        >>> # Load indicator definitions
        >>> indicators = load_brsr_indicators(config.database_url)
        >>> 
        >>> # Extract a single indicator
        >>> ghg_indicator = next(
        ...     ind for ind in indicators 
        ...     if ind.indicator_code == "GHG_SCOPE1"
        ... )
        >>> result = chain.extract_indicator(ghg_indicator)
        >>> 
        >>> print(f"Extracted value: {result.value}")
        >>> print(f"Confidence: {result.confidence}")
        >>> print(f"Source pages: {result.source_pages}")
        >>> 
        >>> # Extract multiple indicators
        >>> results = chain.extract_indicators_batch(indicators[:5])
    """
    return ExtractionChain(
        connection_string=connection_string,
        company_name=company_name,
        report_year=report_year,
        google_api_key=google_api_key,
        model_name=model_name,
        temperature=temperature,
        max_retries=max_retries,
        initial_retry_delay=initial_retry_delay,
    )
