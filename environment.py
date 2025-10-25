import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import json

def get_element_text(element, col_id):
    """
    Safely gets the text of a child element, handling cases where the element or its
    text-containing span might be missing.
    """
    try:
        return element.find_element(By.XPATH, f'.//div[@col-id="{col_id}"]/span').text
    except:
        try:
            return element.find_element(By.XPATH, f'.//div[@col-id="{col_id}"]').text
        except:
            return "N/A"

def check_for_clickable_action(row_element):
    """
    Checks if a clickable view button exists within the 'action' column div for a given row.
    """
    try:
        row_element.find_element(By.XPATH, ".//div[@col-id='action']//span[@title='View']")
        return True
    except:
        return False

def process_company_names(filename):
    """
    Reads company names from a file, searches for them on the webpage,
    clicks on each record's view button, and saves the data to JSON files
    in a specified directory.
    """
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    url = 'https://rtdms.cpcb.gov.in/publicdata/#/l/public-data'
    driver.get(url)

    # Create the output directory if it doesn't exist
    output_directory = "data/recordLinks"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created directory: {output_directory}")

    try:
        wait = WebDriverWait(driver, 30)

        print("Waiting for the main webpage to load...")
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Central Repository Of OCEMS Data'))
        print("Main page loaded successfully.")
        
        input_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Industry Name Filter Input']")))
        
        with open(filename, 'r') as file:
            for company_name in file:
                original_name = company_name.strip()
                if not original_name:
                    continue

                search_names = [original_name]
                if " Ltd" in original_name:
                    search_names.append(original_name.replace(" Ltd", " Limited"))
                elif " Limited" in original_name:
                    search_names.append(original_name.replace(" Limited", " Ltd"))
                
                final_company_data = []
                
                for name_to_search in search_names:
                    print(f"\nSearching for: {name_to_search}")
                    
                    input_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Industry Name Filter Input']")))
                    input_field.clear()
                    input_field.send_keys(name_to_search)
                    
                    time.sleep(1.5)
                    
                    try:
                        wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, 'grid-footer'), 'Total Records'))
                        record_text = driver.find_element(By.CLASS_NAME, 'grid-footer').text
                        match = re.search(r'Total Records: (\d+)', record_text)
                        footer_record_count = int(match.group(1)) if match else 0
                        
                        if footer_record_count > 0:
                            records_to_process = []
                            row_elements_container = driver.find_element(By.CLASS_NAME, 'ag-center-cols-container')
                            row_elements = row_elements_container.find_elements(By.XPATH, "./div")
                            
                            for row in row_elements:
                                record_meta = {
                                    'industry_name': get_element_text(row, "industry_name"),
                                    'address': get_element_text(row, "address"),
                                    'city': get_element_text(row, "city"),
                                    'state_name': get_element_text(row, "state_name"),
                                    'category_name': get_element_text(row, "category_name"),
                                    'has_clickable_action': check_for_clickable_action(row),
                                    'source_name': name_to_search,
                                    'detail_page_url': None
                                }
                                records_to_process.append(record_meta)

                            print(f"Found {len(records_to_process)} records for '{name_to_search}'.")
                            
                            for i, record_to_click in enumerate(records_to_process):
                                if record_to_click['has_clickable_action']:
                                    record_name = record_to_click['industry_name']
                                    
                                    input_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Industry Name Filter Input']")))
                                    input_field.clear()
                                    input_field.send_keys(name_to_search)
                                    time.sleep(1.5)
                                    
                                    eye_icon_locator = f"(//div[@col-id='action']//span[@title='View'])[{i+1}]"
                                    
                                    try:
                                        eye_icon_to_click = wait.until(EC.element_to_be_clickable((By.XPATH, eye_icon_locator)))
                                        print(f"Clicking on eye icon for record {i+1}: '{record_name}'...")
                                        eye_icon_to_click.click()
                                        
                                        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Apply Filters : OCEMS Real Time Data Report'))
                                        
                                        record_to_click['detail_page_url'] = driver.current_url
                                        
                                        print(f"✅ Click successful. URL: {record_to_click['detail_page_url']}")
                                        
                                        driver.back()
                                        
                                        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Central Repository Of OCEMS Data'))

                                    except Exception as e:
                                        print(f"Failed to click on or wait for new page for record {i+1}. Error: {e}")
                                        record_to_click['detail_page_url'] = "Error"
                                
                                final_company_data.append(record_to_click)
                                        
                        else:
                            print(f"No records found for '{name_to_search}'")
                    
                    except Exception as e:
                        print(f"An error occurred while searching for {name_to_search}: {e}")
                
                output_filename = os.path.join(output_directory, f"{original_name.replace(' ', '_')}.json")
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(final_company_data, f, indent=4)
                print(f"\nData for '{original_name}' saved to {output_filename}")


    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()
        print("\nProcess finished. The browser has been closed.")

process_company_names('nift50.txt')