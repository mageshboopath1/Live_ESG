import os
import pika
import time
import sys
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime

# --- RabbitMQ Configuration ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
QUEUE_NAME = 'dashboard_links_queue'
OUTPUT_QUEUE_NAME = 'pollution_data_queue' # New queue for scraped data

# --- Your Existing Scraper Functions (Unchanged) ---
def parse_tuple_to_json(data_tuples):
    structured_data = {}
    for data_tuple in data_tuples:
        if not data_tuple: continue
        parent_label = data_tuple[0]
        measurements = {}
        i = 1
        while i < len(data_tuple):
            measurement = data_tuple[i].strip()
            if i + 2 < len(data_tuple):
                value = data_tuple[i+1].strip()
                timestamp = data_tuple[i+2].replace(' Time', '').strip()
                if value == 'Currently Plant or OCEMS or both not operational':
                    measurements[measurement] = {"status": "Not Operational", "value": None, "time": None}
                else:
                    measurements[measurement] = {"status": "Operational", "value": value, "time": timestamp}
            i += 3
        structured_data[parent_label] = measurements
    return structured_data

def process_live_data_structured(driver, url, company_name, industry_name, state_name):
    final_json_output = {"company_name": company_name, "industry_name": industry_name, "state_name": state_name, "url": url, "pollution_data": {}}
    try:
        wait = WebDriverWait(driver, 30)
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.XPATH, "//hr/following-sibling::div[1]")))
        time.sleep(5)
        parent_div = driver.find_element(By.XPATH, "//hr/following-sibling::div[1]")
        child_divs = parent_div.find_elements(By.XPATH, "./div")
        all_data_tuples = []
        for child_div in child_divs:
            label_elements = child_div.find_elements(By.TAG_NAME, 'label')
            tuple_content = [elem.text.replace('\n', ' ').strip() for elem in label_elements if elem.text.strip()]
            if tuple_content:
                all_data_tuples.append(tuple(tuple_content))
        pollution_data_json = parse_tuple_to_json(all_data_tuples)
        final_json_output["pollution_data"] = pollution_data_json
    except Exception as e:
        print(f"  > Failed to process URL for {industry_name}. Error: {e}")
    return final_json_output

# --- Main Consumer Logic ---
def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    # Declare the new output queue
    channel.queue_declare(queue=OUTPUT_QUEUE_NAME, durable=True)
    print('[Live Pollution Scraper]: Waiting for messages...')

    def callback(ch, method, properties, body):
        message = json.loads(body.decode())
        print(f"\n[Live Pollution Scraper]: [✔] Received message for: {message.get('industry_name')}")

        company_name = message.get("company_name")
        industry_name = message.get("industry_name")
        state_name = message.get("state_name")
        url = message.get("detail_page_url")

        if not url:
            print(f"  > Skipping {industry_name}, no URL provided.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Explicitly define the path to the chromedriver installed by apt-get
            service = Service(executable_path="/usr/bin/chromedriver")
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print(f"  > Scraping {url}...")
            scraped_data = process_live_data_structured(driver, url, company_name, industry_name, state_name)

            # --- Add current timestamp to the scraped data ---
            scraped_data['scraped_datetime_utc'] = datetime.utcnow().isoformat() + 'Z'
            
            print("  > SCRAPED OUTPUT:")
            print(json.dumps(scraped_data, indent=4))

            # --- Publish the output to the new queue ---
            if scraped_data and scraped_data.get("pollution_data"):
                message_body = json.dumps(scraped_data)
                ch.basic_publish(
                    exchange='',
                    routing_key=OUTPUT_QUEUE_NAME,
                    body=message_body.encode('utf-8'),
                    properties=pika.BasicProperties(delivery_mode=2) # make message persistent
                )
                print(f"  > [✔] Published scraped data to '{OUTPUT_QUEUE_NAME}' queue.")

        except Exception as e:
            print(f"  > An error occurred during scraping and publishing: {e}")

        finally:
            if driver:
                driver.quit()
            ch.basic_ack(delivery_tag=method.delivery_tag) # Acknowledge the original message

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    time.sleep(15)
    main()