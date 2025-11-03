import psycopg2
from psycopg2.extras import execute_values
from config import PG_HOST, PG_DB, PG_USER, PG_PASS, logger

def get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )

def store_embeddings(object_key: str, chunk_dicts: list[dict], embeddings: list):
    rows = []
    for c, emb in zip(chunk_dicts, embeddings):
        if emb is None:
            continue
        
        # Validate embedding dimensions (should be 3072 for gemini-embedding-001)
        if len(emb) != 3072:
            logger.error(f"Invalid embedding dimension for {object_key}: expected 3072, got {len(emb)}")
            continue
            
        rows.append((
            object_key,
            object_key.split('/')[0],  # company_name extraction assumption
            int(object_key.split('/')[1].split('_')[0]),  # report_year assumption
            c["page_num"],
            c["chunk_index"],
            emb,
            c["chunk_text"]
        ))
    if not rows:
        logger.warning(f"No embeddings to store for {object_key}")
        return

    sql = """
    INSERT INTO document_embeddings
      (object_key, company_name, report_year, page_number, chunk_index, embedding, chunk_text)
    VALUES %s
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, rows)
        logger.info(f"Stored {len(rows)} embeddings for {object_key}")
    except Exception as e:
        logger.error(f"Error storing embeddings for {object_key}: {e}")
    finally:
        conn.close()
