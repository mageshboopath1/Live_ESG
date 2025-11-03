import pika
import time
import threading
import logging

RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "esg_rabbitmq"
RABBITMQ_PASS = "esg_secret"
QUEUE_NAME = "embedding-tasks"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def producer():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        count = 0
        while True:
            msg = f"test-message-{count}"
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=msg.encode(),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logging.info(f"[PRODUCER] Sent: {msg}")
            count += 1
            time.sleep(2)
    except Exception as e:
        logging.error(f"[PRODUCER] Error: {e}")
    finally:
        try:
            connection.close()
        except:
            pass

def consumer():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        def callback(ch, method, properties, body):
            logging.info(f"[CONSUMER] Received: {body.decode()}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            time.sleep(2)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        logging.info("[*] Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()
    except Exception as e:
        logging.error(f"[CONSUMER] Error: {e}")
    finally:
        try:
            connection.close()
        except:
            pass

if __name__ == "__main__":
    logging.info("Starting RabbitMQ producer and consumer test...")
    threading.Thread(target=producer, daemon=True).start()
    consumer()