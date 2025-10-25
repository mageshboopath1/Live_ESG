import os
import psycopg2
from psycopg2 import sql
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import re
import json
import sys
from tqdm import tqdm

# --- Database configuration ---
DB_HOST = 'localhost'
DB_NAME = 'Environment'
DB_USER = 'mageshboopathi'
DB_PASSWORD = 'jesus'
TABLE_NAME = 'live_dashboard_links'

def parse_tuple_to_json(data_tuples):
    """
    Parses a list of tuples into a structured JSON dictionary.
    """
    structured_data = {}
    for data_tuple in data_tuples:
        if not data_tuple:
            continue

        parent_label = data_tuple[0]
        measurements = {}
        
        # Iterate through the rest of the tuple in steps of 3
        i = 1
        while i < len(data_tuple):
            measurement = data_tuple[i].strip()
            
            if i + 2 < len(data_tuple):
                value = data_tuple[i+1].strip()
                timestamp = data_tuple[i+2].replace(' Time', '').strip()
                
                if value == 'Currently Plant or OCEMS or both not operational':
                    measurements[measurement] = {
                        "status": "Not Operational",
                        "value": None,
                        "time": None
                    }
                else:
                    measurements[measurement] = {
                        "status": "Operational",
                        "value": value,
                        "time": timestamp
                    }
            
            i += 3
        
        structured_data[parent_label] = measurements
    return structured_data

def process_live_data_structured(driver, url, company_name, industry_name, state_name):
    """
    Opens a URL, scrapes pollution data, and returns a structured JSON dictionary.
    """
    final_json_output = {
        "company_name": company_name,
        "industry_name": industry_name,
        "state_name": state_name,
        "url": url,
        "pollution_data": {}
    }
    
    try:
        wait = WebDriverWait(driver, 30)
        driver.get(url)
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//hr/following-sibling::div[1]")))
        time.sleep(5)
        
        parent_div = driver.find_element(By.XPATH, "//hr/following-sibling::div[1]")
        child_divs = parent_div.find_elements(By.XPATH, "./div")
        
        all_data_tuples = []
        for i, child_div in enumerate(child_divs):
            try:
                label_elements = child_div.find_elements(By.TAG_NAME, 'label')
                
                tuple_content = []
                
                for label_elem in label_elements:
                    full_text = label_elem.text.replace('\n', ' ').strip()
                    if full_text:
                        tuple_content.append(full_text)

                all_data_tuples.append(tuple(tuple_content))
                
            except Exception as e:
                tqdm.write(f"  > Skipping record {i+1} due to missing elements. Error: {e}")
        
        pollution_data_json = parse_tuple_to_json(all_data_tuples)
        final_json_output["pollution_data"] = pollution_data_json
        
    except Exception as e:
        tqdm.write(f"  > Failed to process URL for {industry_name}. Error: {e}")
    
    return final_json_output

def get_data_from_db():
    """
    Connects to the database and retrieves the required data.
    """
    conn = None
    all_records = []
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        cursor = conn.cursor()
        
        query = sql.SQL('SELECT company_name, industry_name, state_name, detail_page_url FROM {table}').format(table=sql.Identifier(TABLE_NAME))
        cursor.execute(query)
        
        all_records = cursor.fetchall()
        tqdm.write(f"Found {len(all_records)} records in the database.")
        
    except Exception as e:
        tqdm.write(f"Database connection or query failed: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    
    return all_records

def main():
    driver = None
    try:
        db_records = get_data_from_db()
        
        if not db_records:
            tqdm.write("No records to process. Exiting.")
        else:
            service = Service()
            driver = webdriver.Chrome(service=service)
            
            all_scraped_data = []
            
            with tqdm(total=len(db_records), desc="Scraping Progress") as pbar:
                for record in db_records:
                    company_name, industry_name, state_name, url = record
                    if url:
                        scraped_record = process_live_data_structured(driver, url, company_name, industry_name, state_name)
                        all_scraped_data.append(scraped_record)
                    else:
                        tqdm.write(f"Skipping {industry_name} as it has no URL.")
                    pbar.update(1)
            
            # Save all collected data to a single JSON file
            output_filename = "all_pollution_data.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(all_scraped_data, f, indent=4)
            tqdm.write(f"\nAll data saved to {output_filename}")

    finally:
        if driver:
            driver.quit()
        tqdm.write("\nBrowser closed.")

if __name__ == "__main__":
    main()