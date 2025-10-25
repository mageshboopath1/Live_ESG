import os
import requests
import schedule
import time
import pika
import json

API_URL = "http://api:8000/live_dashboard_links"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
QUEUE_NAME = 'dashboard_links_queue'

def populate_queue():
    """
    Fetches data from the API and publishes it to the RabbitMQ queue.
    """
    print("Scheduler: Calling API to get dashboard links...")
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json().get('data', [])
        print(f"Scheduler: Successfully fetched {len(data)} records.")

        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        for record in data:
            message_body = json.dumps(record)
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=message_body,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        
        print(f"Scheduler: Published {len(data)} messages to queue '{QUEUE_NAME}'.")
        connection.close()

    except requests.exceptions.RequestException as e:
        print(f"Scheduler: Could not connect to API. Error: {e}")
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Scheduler: Could not connect to RabbitMQ. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

print("Scheduler service started.")
schedule.every(5).minutes.do(populate_queue)
populate_queue() # Initial run

while True:
    schedule.run_pending()
    time.sleep(1)