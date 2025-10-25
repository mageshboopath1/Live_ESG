import os
import psycopg2
from psycopg2 import sql
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth
import time
import sys

# --- Database configuration ---
DB_HOST = 'localhost'
DB_NAME = 'Environment'
DB_USER = 'mageshboopathi'
DB_PASSWORD = 'jesus'
TABLE_NAME = 'nift50_companies'

# --- Selenium setup ---
def setup_stealth_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    user_agent = 'Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    options.add_argument(f"user-agent={user_agent}")

    # Create the 'data' folder if it doesn't exist
    download_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Set download preferences for the Chrome browser
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    return driver

def get_company_symbols():
    """
    Connects to the database and retrieves all company symbols.
    """
    conn = None
    symbols = []
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        cursor = conn.cursor()
        
        query = sql.SQL('SELECT symbol FROM {}').format(sql.Identifier(TABLE_NAME))
        cursor.execute(query)
        
        symbols = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(symbols)} symbols in the database.")
        
    except Exception as e:
        print(f"Database connection or query failed: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    
    return symbols

# --- Main execution ---
def main():
    company_symbols = get_company_symbols()
    
    if not company_symbols:
        print("No symbols to process. Exiting.")
        return
        
    url = 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'

    for symbol in company_symbols:
        driver = None
        try:
            if symbol:
                print(f"\nProcessing symbol: {symbol}")

                driver = setup_stealth_driver()
                wait = WebDriverWait(driver, 30)
                
                driver.get(url)

                input_field_locator = (By.CSS_SELECTOR, 'input.form-control.with_radius.companyVal.typeahead.companyAutoComplete.tt-input')
                input_field = wait.until(EC.presence_of_element_located(input_field_locator))

                input_field.send_keys(symbol)
                
                dropdown_locator = (By.CSS_SELECTOR, 'div.tt-menu div.tt-selectable')
                try:
                    first_option = wait.until(EC.element_to_be_clickable(dropdown_locator))
                    print("Dropdown option found. Clicking...")
                    first_option.click()
                    
                    print("Option clicked. Waiting for 10 seconds...")
                    time.sleep(10)
                    
                    # --- Download the CSV file ---
                    print("Attempting to download CSV...")
                    download_link_locator = (By.CSS_SELECTOR, '#CFanncEquity-download')
                    download_link = wait.until(EC.element_to_be_clickable(download_link_locator))
                    download_link.click()
                    
                    # Wait for the download to complete
                    time.sleep(5)
                    print("CSV download initiated.")
                    
                except TimeoutException:
                    print(f"No dropdown option found for '{symbol}'. Skipping.")
            else:
                print("Skipping empty symbol.")

        except Exception as e:
            print(f"An error occurred for symbol {symbol}: {e}")

        finally:
            if driver:
                driver.quit()

    print("\nAll symbols processed. Script finished.")

if __name__ == "__main__":
    main()