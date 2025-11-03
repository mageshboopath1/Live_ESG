#!/usr/bin/env python3
"""
Script to publish extraction tasks to RabbitMQ for all PDFs from 2023-2024 and 2024-2025.

Usage:
    uv run scripts/publish_extraction_tasks.py
"""

import json
import pika
import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'moz',
    'user': 'drfitz',
    'password': 'h4i1hydr4'
}

# RabbitMQ configuration
RABBITMQ_CONFIG = {
    'host': 'localhost',
    'port': 5672,
    'user': 'esg_rabbitmq',
    'password': 'esg_secret'
}

QUEUE_NAME = 'extraction-tasks'


def get_pdf_files():
    """Query database for all PDF files from 2023-2024 and 2024-2025."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
    SELECT i.file_path, c.company_name, i.status 
    FROM ingestion_metadata i 
    JOIN company_catalog c ON i.company_id = c.id 
    WHERE i.file_path LIKE '%.pdf' 
    AND (i.file_path LIKE '%2023%' OR i.file_path LIKE '%2024%')
    ORDER BY c.company_name;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def publish_to_rabbitmq(file_paths):
    """Publish file paths to RabbitMQ extraction queue."""
    credentials = pika.PlainCredentials(
        RABBITMQ_CONFIG['user'],
        RABBITMQ_CONFIG['password']
    )
    
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_CONFIG['host'],
        port=RABBITMQ_CONFIG['port'],
        credentials=credentials
    )
    
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    # Queue already exists, no need to declare
    
    published_count = 0
    skipped_count = 0
    
    for record in file_paths:
        file_path = record['file_path']
        company_name = record['company_name']
        status = record['status']
        
        # Skip files that are already being processed or have been processed
        # if status in ['PROCESSING', 'SUCCESS']:
        #     print(f"Skipping {file_path} (status: {status})")
        #     skipped_count += 1
        #     continue
        
        # Create message payload
        message = {
            "object_key": file_path
        }
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        
        print(f"Published: {file_path} ({company_name})")
        published_count += 1
    
    connection.close()
    
    return published_count, skipped_count


def main():
    print("Fetching PDF files from database...")
    pdf_files = get_pdf_files()
    print(f"Found {len(pdf_files)} PDF files")
    
    print("\nPublishing to RabbitMQ extraction queue...")
    published, skipped = publish_to_rabbitmq(pdf_files)
    
    print(f"\n✓ Complete!")
    print(f"  Published: {published}")
    print(f"  Skipped: {skipped}")
    print(f"  Total: {len(pdf_files)}")


if __name__ == "__main__":
    main()
