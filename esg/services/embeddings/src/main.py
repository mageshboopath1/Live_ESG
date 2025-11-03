import os
import time
import pika
import boto3
import psycopg2
from psycopg2.extras import execute_values
import fitz  # PyMuPDF
from tqdm import tqdm

# Import from local modules
from embedder import embed_chunks

# --- Environment Variables ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET_NAME = "esg-reports"

RABBITMQ_HOST = "rabbitmq"
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
QUEUE_NAME = "embedding-tasks"

PG_HOST = os.getenv("DB_HOST")
PG_DB = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")

# --- Initialize Clients ---
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

def get_db_connection():
    return psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )

def recursive_character_text_splitter(text, chunk_size=1000, chunk_overlap=200):
    chunks = []
    for i in range(0, len(text), chunk_size - chunk_overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def process_document(object_key):
    print(f"Processing document: {object_key}")
    local_path = f"/tmp/{os.path.basename(object_key)}"
    s3.download_file(BUCKET_NAME, object_key, local_path)

    try:
        with fitz.open(local_path) as doc:
            full_text = "\n".join([page.get_text() for page in doc])
        chunks = recursive_character_text_splitter(full_text)

        if not chunks:
            print(f"Warning: No text could be extracted from {object_key}. Skipping.")
            return

        # Use embed_chunks from embedder.py which uses gemini-embedding-001 with 3072 dimensions
        embeddings = embed_chunks(chunks, batch_size=32, retries=3)

        # Validate embedding dimensions before storage
        valid_rows = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is None:
                continue
            
            # Verify embedding dimension is 3072
            if len(embedding) != 3072:
                print(f"Warning: Invalid embedding dimension for chunk {i} of {object_key}: expected 3072, got {len(embedding)}")
                continue
                
            valid_rows.append((
                object_key,
                object_key.split('/')[0],
                int(object_key.split('/')[1].split('_')[0]),
                i + 1,  # This is not the page number anymore, but the chunk number
                embedding,
                chunk
            ))

        if not valid_rows:
            print(f"Warning: No valid embeddings to store for {object_key}")
            return

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    "INSERT INTO document_embeddings (object_key, company_name, report_year, page_number, embedding, chunk_text) VALUES %s",
                    valid_rows
                )
            conn.commit()
        print(f"Successfully processed and stored {len(valid_rows)} embeddings for {object_key}")

    except Exception as e:
        print(f"Error processing document {object_key}: {e}")
    finally:
        os.remove(local_path)

def callback(ch, method, properties, body):
    object_key = body.decode()
    print(f"Received message: {object_key}")
    process_document(object_key)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
            print("Waiting for messages. To exit press CTRL+C")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
