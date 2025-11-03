import time
import pika
from config import get_rabbitmq_connection, QUEUE_NAME, logger
from extractor import process_download
from splitter import pages_to_chunks
from embedder import embed_chunks
from db import store_embeddings

EXTRACTION_QUEUE_NAME = "extraction-tasks"

def publish_to_extraction_queue(object_key: str):
    """
    Publish object_key to extraction-tasks queue for downstream processing.
    Implements error handling with retry logic.
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = get_rabbitmq_connection()
            channel = conn.channel()
            
            # Declare the extraction-tasks queue (idempotent operation)
            channel.queue_declare(queue=EXTRACTION_QUEUE_NAME, durable=True)
            
            # Publish message with persistent delivery mode
            channel.basic_publish(
                exchange='',
                routing_key=EXTRACTION_QUEUE_NAME,
                body=object_key.encode(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"Published {object_key} to {EXTRACTION_QUEUE_NAME} queue")
            conn.close()
            return True
            
        except pika.exceptions.AMQPError as e:
            logger.error(f"AMQP error publishing to extraction queue (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Failed to publish {object_key} to extraction queue after {max_retries} attempts")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error publishing to extraction queue: {e}", exc_info=True)
            return False

def process_object(object_key: str):
    logger.info(f"Processing document: {object_key}")
    pages = process_download(object_key, use_ocr=False)
    if not pages:
        logger.warning(f"No pages extracted for {object_key}. Skipping.")
        return

    chunk_dicts = pages_to_chunks(pages, chunk_size=1000, chunk_overlap=200)
    if not chunk_dicts:
        logger.warning(f"No chunks derived for {object_key}. Skipping.")
        return

    texts = [c["chunk_text"] for c in chunk_dicts]
    embeddings = embed_chunks(texts, batch_size=32, retries=3)
    store_embeddings(object_key, chunk_dicts, embeddings)
    logger.info(f"Finished processing embeddings for {object_key}")
    
    # Publish to extraction-tasks queue for downstream indicator extraction
    publish_success = publish_to_extraction_queue(object_key)
    if not publish_success:
        logger.warning(f"Failed to publish {object_key} to extraction queue, but embeddings were stored successfully")

def callback(ch, method, properties, body):
    object_key = body.decode()
    logger.info(f"Received message: {object_key}")
    try:
        process_object(object_key)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing {object_key}: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    while True:
        try:
            conn = get_rabbitmq_connection()
            channel = conn.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
            logger.info("Waiting for messages. To exit press CTRL+C")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
