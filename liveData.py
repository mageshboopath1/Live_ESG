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
import pandas as pd
from tqdm import tqdm

pd.set_option('display.max_columns', None)

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

def unify_json_data(directory):
    """
    Reads all JSON files from a specified directory, unifies them into a single pandas
    DataFrame.
    """
    all_records = []
    
    if not os.path.exists(directory):
        tqdm.write(f"Directory not found: {directory}")
        return pd.DataFrame()

    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    
    if not json_files:
        tqdm.write(f"No JSON files found in {directory}.")
        return pd.DataFrame()

    tqdm.write(f"Found {len(json_files)} JSON files to process.")

    for filename in json_files:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if data:
                    df = pd.DataFrame(data)
                    all_records.append(df)
            except json.JSONDecodeError as e:
                tqdm.write(f"Error decoding JSON from {filename}: {e}. Skipping.")

    if not all_records:
        tqdm.write("All JSON files were empty or invalid. Returning an empty DataFrame.")
        return pd.DataFrame()

    master_df = pd.concat(all_records, ignore_index=True)
    
    return master_df

def process_state(driver, wait, state_name, industries):
    """
    Handles the search and nested industry search for a given state, checking for clickable elements.
    """
    state_data_to_save = []
    
    try:
        state_input_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.ant-select-selection-search-input')))
        state_input_field.clear()
        
        tqdm.write(f"\nProcessing state: {state_name}")
        state_input_field.send_keys(state_name)
        
        time.sleep(1)
        
        dropdown_option_locator = (By.XPATH, f"//div[@class='ant-select-item-option-content'][text()='{state_name}']")
        
        try:
            dropdown_option = wait.until(EC.element_to_be_clickable(dropdown_option_locator))
            dropdown_option.click()
            tqdm.write(f"Selected '{state_name}' from dropdown.")
        except Exception:
            tqdm.write(f"Warning: Could not find/select '{state_name}' from dropdown. Proceeding to submit.")

        submit_button_locator = (By.CSS_SELECTOR, 'button.form-submit-btn[type="submit"]')
        submit_button = wait.until(EC.element_to_be_clickable(submit_button_locator))
        submit_button.click()
        tqdm.write("Clicked Submit button.")

        results_footer_locator = (By.CLASS_NAME, 'grid-footer')
        wait.until(EC.visibility_of_element_located(results_footer_locator))
        wait.until(EC.text_to_be_present_in_element(results_footer_locator, 'Total Records'))
        
        tqdm.write("SUCCESS: Search results page loaded (Total Records footer found).")
        
        try:
            for industry_name in industries:
                industry_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Industry Name Filter Input']")))
                
                tqdm.write(f"\n\t > Searching for industry: {industry_name}")
                industry_input_field.clear()
                industry_input_field.send_keys(industry_name)
                
                time.sleep(2) 
                
                try:
                    records_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'ag-center-cols-container')))
                    row_elements = records_container.find_elements(By.XPATH, "./div")
                    
                    found_clickable_record = False
                    for row in row_elements:
                        if check_for_clickable_action(row):
                            found_clickable_record = True
                            
                            eye_icon = row.find_element(By.XPATH, ".//div[@col-id='action']//span[@title='View']")
                            eye_icon.click()
                            
                            wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), industry_name))
                            
                            tqdm.write(f"\t >>> Redirect successful. Found '{industry_name}' on the new page.")
                            
                            record_data = {
                                'industry_name': industry_name,
                                'url': driver.current_url
                            }
                            state_data_to_save.append(record_data)
                            
                            tqdm.write(f"\t >>> Redirected URL: {driver.current_url}")

                            tqdm.write("\t >>> Waiting for 5 seconds...")
                            time.sleep(5)
                            
                            driver.back()

                            tqdm.write("\t >>> Waiting for 3 seconds...")
                            time.sleep(3)
                            
                            wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Online Emission and Effluent Monitoring System for 17 Categories of Industries'))
                            tqdm.write("Main page text confirmed. Proceeding with next search.")
                            
                            break
                    
                    if not found_clickable_record:
                        tqdm.write("\t >>> No clickable records found after filtering by industry.")
                
                except Exception as e:
                    tqdm.write(f"\t >>> Could not find records container. Error: {e}")
                
        except Exception as e:
            tqdm.write(f"Warning: Could not locate industry filter on redirected page. Error: {e}")

        driver.back()
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Central Pollution Control Board'))
    
    except Exception as e:
        tqdm.write(f"An error occurred while processing state '{state_name}': {e}")
        driver.get('https://rtdms.cpcb.gov.in/data/#/l/public-filters')
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Central Pollution Control Board'))

    finally:
        if state_data_to_save:
            output_directory = "data/liveLinks"
            output_filename = os.path.join(output_directory, f"{state_name.replace(' ', '_')}.json")
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(state_data_to_save, f, indent=4)
            tqdm.write(f"\nData for '{state_name}' saved to {output_filename}")


def main():
    unified_data = unify_json_data('data/recordLinks')

    if unified_data.empty:
        tqdm.write("No data to process. Exiting.")
        return

    service = Service()
    driver = webdriver.Chrome(service=service)

    url = 'https://rtdms.cpcb.gov.in/data/#/l/public-filters'
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 30)
        
        tqdm.write("Waiting for 'Central Pollution Control Board' text to appear...")
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Central Pollution Control Board'))
        tqdm.write("Text found. Proceeding with actions.")
        
        industries_by_state = unified_data.groupby('state_name')['industry_name'].apply(list).to_dict()

        states_to_process = [
            state for state in industries_by_state.keys() 
            if not pd.isna(state) and state != "Orissa"
        ]

        with tqdm(total=len(states_to_process), desc="Overall Progress") as pbar:
            for state_name in states_to_process:
                industries = industries_by_state[state_name]
                process_state(driver, wait, state_name, industries)
                pbar.update(1)

    except Exception as e:
        tqdm.write(f"An error occurred in the main script: {e}")

    finally:
        driver.quit()
        tqdm.write("Browser closed.")

if __name__ == "__main__":
    main()