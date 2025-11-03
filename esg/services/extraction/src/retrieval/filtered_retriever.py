"""Filtered vector retriever for company and year-specific document search."""

import logging
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from google.genai import types

logger = logging.getLogger(__name__)


class FilteredPGVectorRetriever:
    """
    Custom retriever that filters embeddings by company_name and report_year
    before performing vector similarity search.
    
    This significantly reduces the search space from 120k+ embeddings to ~200-500
    per document, improving both performance and accuracy.
    """
    
    def __init__(
        self,
        connection_string: str,
        company_name: str,
        report_year: int,
        embedding_model: str = "models/gemini-embedding-001"
    ):
        """
        Initialize the filtered retriever.
        
        Args:
            connection_string: PostgreSQL connection string
            company_name: Company name to filter by
            report_year: Report year to filter by
            embedding_model: Google GenAI embedding model name
        """
        self.connection_string = connection_string
        self.company_name = company_name
        self.report_year = report_year
        
        # Initialize embedding function with 3072 dimensions to match database embeddings
        # Using models/gemini-embedding-001 which produces 3072-dimensional embeddings
        self.embedding_function = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            config=types.EmbedContentConfig(output_dimensionality=3072)
        )
        
        logger.info(
            f"Initialized FilteredPGVectorRetriever for company={company_name}, "
            f"year={report_year}, model={embedding_model}, dimensions=3072"
        )
    
    def get_relevant_documents(
        self,
        query: str,
        k: int = 5,
        distance_threshold: Optional[float] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents filtered by company and year.
        
        This method:
        1. Generates an embedding for the query
        2. Filters embeddings by company_name and report_year
        3. Performs vector similarity search using cosine distance
        4. Returns top-k most relevant chunks as LangChain Documents
        
        Args:
            query: Search query text
            k: Number of documents to retrieve (default: 5)
            distance_threshold: Optional maximum distance threshold for results
            
        Returns:
            List of LangChain Document objects with metadata
            
        Raises:
            psycopg2.Error: If database query fails
            ValueError: If no documents are found
        """
        try:
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {query[:100]}...")
            query_embedding = self.embedding_function.embed_query(query)
            
            # Convert embedding to PostgreSQL vector format
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Build SQL query with filtering and vector similarity
            sql = """
            SELECT 
                id,
                object_key,
                company_name,
                report_year,
                page_number,
                chunk_index,
                chunk_text,
                embedding <=> %s::vector AS distance
            FROM document_embeddings
            WHERE company_name = %s 
              AND report_year = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """
            
            params = [
                embedding_str,
                self.company_name,
                self.report_year,
                embedding_str,
                k
            ]
            
            # Execute query
            logger.debug(
                f"Executing filtered vector search for company={self.company_name}, "
                f"year={self.report_year}, k={k}"
            )
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql, params)
                    results = cur.fetchall()
            
            # Check if results are empty
            if not results:
                error_msg = (
                    f"No documents found for company={self.company_name}, "
                    f"year={self.report_year}"
                )
                logger.warning(error_msg)
                raise ValueError(error_msg)
            
            # Apply distance threshold if specified
            if distance_threshold is not None:
                results = [r for r in results if r['distance'] <= distance_threshold]
                if not results:
                    error_msg = (
                        f"No documents found within distance threshold "
                        f"{distance_threshold} for company={self.company_name}, "
                        f"year={self.report_year}"
                    )
                    logger.warning(error_msg)
                    raise ValueError(error_msg)
            
            # Convert to LangChain Document format
            documents = []
            for row in results:
                doc = Document(
                    page_content=row['chunk_text'],
                    metadata={
                        "id": row['id'],
                        "object_key": row['object_key'],
                        "company_name": row['company_name'],
                        "report_year": row['report_year'],
                        "page_number": row['page_number'],
                        "chunk_index": row['chunk_index'],
                        "distance": float(row['distance'])
                    }
                )
                documents.append(doc)
            
            logger.info(
                f"Retrieved {len(documents)} documents for query. "
                f"Distance range: [{documents[-1].metadata['distance']:.4f}, "
                f"{documents[0].metadata['distance']:.4f}]"
            )
            
            return documents
            
        except psycopg2.Error as e:
            logger.error(f"Database error during retrieval: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during retrieval: {e}")
            raise
    
    def get_relevant_documents_with_scores(
        self,
        query: str,
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """
        Retrieve relevant documents with their similarity scores.
        
        Args:
            query: Search query text
            k: Number of documents to retrieve
            
        Returns:
            List of tuples (Document, score) where score is the distance
        """
        documents = self.get_relevant_documents(query, k)
        return [(doc, doc.metadata['distance']) for doc in documents]
