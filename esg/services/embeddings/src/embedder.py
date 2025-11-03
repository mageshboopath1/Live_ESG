import time
import random
from config import GOOGLE_API_KEY, logger
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from google.genai import types

# Initialize embedding model
# Using gemini-embedding-001 with 3072 dimensions
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY,
    config=types.EmbedContentConfig(output_dimensionality=3072)
    # optionally task_type="RETRIEVAL_DOCUMENT" or others
)

def embed_chunks(chunk_texts: list[str], batch_size: int=32, retries: int=3):
    """
    Given list of chunk_texts, returns list of embeddings (list of floats) or None aligned.
    """
    # filter empty
    valid_indices = []
    valid_texts = []
    for i, t in enumerate(chunk_texts):
        if t and t.strip():
            valid_indices.append(i)
            valid_texts.append(t)
    if not valid_texts:
        logger.warning("No valid chunks to embed.")
        return [None] * len(chunk_texts)

    embeddings = [None] * len(chunk_texts)
    for i in range(0, len(valid_texts), batch_size):
        batch = valid_texts[i:i+batch_size]
        attempt = 0
        while attempt < retries:
            try:
                batch_embeds = embeddings_model.embed_documents(batch)
                break
            except Exception as e:
                attempt += 1
                if attempt < retries:
                    wait = (2 ** attempt) + random.random()
                    logger.warning(f"Embedding batch failed (attempt {attempt}/{retries}) – retrying in {wait:.1f}s. Error: {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"Embedding failed after {retries} attempts. Error: {e}")
                    batch_embeds = [None] * len(batch)

        for j, emb in enumerate(batch_embeds):
            orig_idx = valid_indices[i + j]
            embeddings[orig_idx] = emb
    return embeddings
