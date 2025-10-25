import os
import pika
import json
import time
import sys
from pymongo import MongoClient 
# Import necessary PyMongo exceptions for robust error handling
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError, OperationFailure

# --- RabbitMQ Configuration ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
QUEUE_NAME = 'pollution_data_queue' 

# --- MongoDB Configuration ---
# Variables are read from the docker-compose environment block
MONGO_URI = os.getenv("MONGO_URI") 
MONGO_DB_NAME = os.getenv("MONGO_DB") 
MONGO_COLLECTION_NAME = 'pollution_records' 

# Global variable to hold the MongoDB connection
mongo_client = None

def connect_to_mongodb():
    """
    Establishes and returns a connection to the MongoDB server, using retries.
    """
    global mongo_client
    if mongo_client:
        return mongo_client
        
    print(f"MongoDB Service: Attempting to connect to MongoDB at {MONGO_URI}...")
    max_retries = 10
    
    # Check if MONGO_URI is available, preventing a crash if environment variable is missing
    if not MONGO_URI:
        print("CRITICAL ERROR: MONGO_URI environment variable is missing.")
        sys.exit(1)
        
    for i in range(max_retries):
        try:
            # Connect to MongoDB with a timeout and disable TLS for Docker networking
            # Using connect=False ensures MongoClient is initialized without an immediate network call
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=False, connect=False)
            
            # The ismaster command forces the connection check and raises ServerSelectionTimeoutError on failure
            client.admin.command('ismaster') 
            mongo_client = client
            print("MongoDB Service: Successfully connected to MongoDB.")
            return client
        except ServerSelectionTimeoutError as e:
            print(f"MongoDB Connection failed (ServerSelectionTimeoutError). Retrying in 5 seconds... ({i+1}/{max_retries}). Error: {e}")
            time.sleep(5)
        except Exception as e:
            # Catch all unexpected errors during the connection attempt and log them
            print(f"FATAL ERROR during MongoDB connection attempt (before loop finished): {e}")
            time.sleep(5)
            
    print("MongoDB Service: Failed to connect to MongoDB after multiple retries. Exiting.")
    sys.exit(1)


def main():
    """
    Main function to connect to RabbitMQ and start consuming messages.
    """
    # Initialize MongoDB connection globally
    connect_to_mongodb()
    
    # 1. RabbitMQ Connection Setup with Retries
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = None
    print("MongoDB Service: Attempting to connect to RabbitMQ...")
    max_retries = 30
    for i in range(max_retries):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=RABBITMQ_HOST, 
                credentials=credentials, 
                heartbeat=60
            ))
            print("MongoDB Service: Connected to RabbitMQ.")
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"RabbitMQ Connection failed. Retrying in 5 seconds... ({i+1}/{max_retries})")
            time.sleep(5)
    else:
        print("RabbitMQ Service: Failed to connect after multiple retries. Exiting.")
        sys.exit(1)

    channel = connection.channel()
    
    # 2. Declare the Queue
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    print(f'[MongoDB Service]: Waiting for messages on queue: {QUEUE_NAME}.')

    def callback(ch, method, properties, body):
        """
        Callback function to process messages and insert them into MongoDB.
        """
        global mongo_client 
        
        try:
            # Decode and parse the JSON message
            scraped_data = json.loads(body.decode('utf-8'))
            
            # --- Get the database and collection ---
            if not mongo_client:
                 print("[MongoDB Service]: MongoDB client lost connection. Attempting to reconnect...")
                 connect_to_mongodb() 
                 if not mongo_client:
                     raise Exception("Failed to re-initialize MongoDB client. Skipping insertion.")

            db = mongo_client[MONGO_DB_NAME]
            collection = db[MONGO_COLLECTION_NAME] 
            
            # --- MongoDB Insertion ---
            result = collection.insert_one(scraped_data)
            
            # Confirmation log replaces the debugging print statement
            print(f"[MongoDB Service]: [✔] Inserted record for {scraped_data.get('industry_name')} (ID: {result.inserted_id})")
            
        except json.JSONDecodeError:
            print("[MongoDB Service]: Received malformed JSON message. Skipping.")
        except (ConfigurationError, OperationFailure) as e:
            print(f"[MongoDB Service]: MongoDB Operation/Configuration Failure: {e}")
        except Exception as e:
            print(f"[MongoDB Service]: An unexpected error occurred: {e}")
        finally:
            # 3. Acknowledge the message to signal successful processing or logging of an error
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # 4. Start Consuming
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[MongoDB Service]: Exiting consumer.")
        channel.stop_consuming()
    except Exception as e:
        print(f"\n[MongoDB Service]: An error occurred during consuming: {e}")
    finally:
        # Close connections safely
        if mongo_client:
            mongo_client.close()
        if connection and connection.is_open:
            connection.close()

if __name__ == '__main__':
    time.sleep(10)
    main()