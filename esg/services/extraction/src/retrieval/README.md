# Retrieval Module

This module provides filtered vector retrieval functionality for the ESG Intelligence Platform extraction service.

## FilteredPGVectorRetriever

The `FilteredPGVectorRetriever` class implements a custom retriever that filters embeddings by company name and report year before performing vector similarity search. This approach significantly improves both performance and accuracy by reducing the search space from 40,000+ embeddings to approximately 200-500 per document.

### Features

- **Filtered Search**: Pre-filters embeddings by company_name and report_year before vector similarity search
- **Efficient Indexing**: Uses composite index on (company_name, report_year) for fast filtering
- **LangChain Integration**: Returns standard LangChain Document objects with rich metadata
- **Error Handling**: Comprehensive error handling for empty results and database failures
- **Logging**: Detailed logging for debugging and monitoring

### Usage

```python
from src.retrieval.filtered_retriever import FilteredPGVectorRetriever
from src.config import config

# Initialize retriever for a specific company and year
retriever = FilteredPGVectorRetriever(
    connection_string=config.database_url,
    company_name="RELIANCE",
    report_year=2024,
    embedding_model="models/embedding-001"
)

# Retrieve relevant documents
documents = retriever.get_relevant_documents(
    query="What are the total Scope 1 emissions?",
    k=5  # Number of documents to retrieve
)

# Access document content and metadata
for doc in documents:
    print(f"Page: {doc.metadata['page_number']}")
    print(f"Distance: {doc.metadata['distance']}")
    print(f"Content: {doc.page_content}")
```

### Parameters

#### `__init__`

- `connection_string` (str): PostgreSQL connection string
- `company_name` (str): Company name to filter by
- `report_year` (int): Report year to filter by
- `embedding_model` (str, optional): Google GenAI embedding model name (default: "models/embedding-001")

#### `get_relevant_documents`

- `query` (str): Search query text
- `k` (int, optional): Number of documents to retrieve (default: 5)
- `distance_threshold` (float, optional): Maximum distance threshold for results

**Returns**: List of LangChain Document objects

**Raises**:
- `ValueError`: If no documents are found
- `psycopg2.Error`: If database query fails

### Document Metadata

Each returned Document includes the following metadata:

- `id`: Database ID of the embedding
- `object_key`: MinIO object key (e.g., "RELIANCE/2024_BRSR.pdf")
- `company_name`: Company name
- `report_year`: Report year
- `page_number`: Page number in the source PDF
- `chunk_index`: Index of the chunk within the page
- `distance`: Cosine distance from the query (lower is more similar)

### Performance Optimization

The retriever uses a SQL query with WHERE clause filtering before vector similarity search:

```sql
SELECT ... 
FROM document_embeddings
WHERE company_name = ? AND report_year = ?
ORDER BY embedding <=> ?::vector
LIMIT ?
```

This approach:
1. Filters to ~200-500 embeddings per document (vs 40k+ total)
2. Uses composite index for fast filtering
3. Performs vector search only on filtered subset
4. Returns top-k most similar chunks

### Requirements Satisfied

- **Requirement 6.1**: Retrieves relevant context chunks using Vector Similarity Search with pgvector
- **Requirement 11.1**: Uses LangChain VectorStore integration with pgvector for semantic retrieval
- **Requirement 11.2**: Combines retrieval with generation in LangChain chains

### Error Handling

The retriever handles the following error cases:

1. **Empty Results**: Raises `ValueError` with descriptive message if no documents found
2. **Database Errors**: Logs and re-raises `psycopg2.Error` for database failures
3. **Distance Threshold**: Filters results by distance if threshold specified
4. **Connection Failures**: Proper connection cleanup with context managers

### Testing

Run the structural validation test:

```bash
uv run python test_retriever_structure.py
```

This validates:
- Class structure and methods
- Method signatures and parameters
- Import availability
- Return type annotations

### Integration with LangChain

The retriever is designed to integrate seamlessly with LangChain chains:

```python
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI

# Create LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Create retrieval chain
chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff"
)

# Execute query
result = chain.run("What are the total Scope 1 emissions?")
```

### Database Schema Requirements

The retriever expects the following table structure:

```sql
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    object_key TEXT NOT NULL,
    company_name TEXT NOT NULL,
    report_year INT NOT NULL,
    page_number INT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(3072),
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Required indexes
CREATE INDEX idx_company_year ON document_embeddings(company_name, report_year);
CREATE INDEX idx_embedding_vector ON document_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```
