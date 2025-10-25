import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from fuzzywuzzy import fuzz

# --- Database Configuration ---
# IMPORTANT: Replace these with your actual PostgreSQL credentials.
DB_CONFIG = {
    "dbname": "Environment",
    "user": "mageshboopathi",
    "password": "jesus",
    "host": "localhost",
    "port": "5432"
}

def setup_database(conn):
    """Creates the nift50_social_links table if it doesn't exist."""
    try:
        cur = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS nift50_social_links (
            id SERIAL PRIMARY KEY,
            company_name TEXT UNIQUE,
            url TEXT,
            score INT
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        cur.close()
        print("Database setup complete. 'nift50_social_links' table is ready.")
    except psycopg2.Error as e:
        print(f"Error during database setup: {e}")
        conn.rollback()

def get_unscraped_company_names(conn):
    """
    --- MODIFIED FUNCTION ---
    Fetches company names from the nift50_social_links table where the URL is NULL.
    """
    company_names = []
    try:
        cur = conn.cursor()
        # The SQL query is now changed to select only unscraped companies.
        cur.execute('SELECT company_name FROM nift50_social_links WHERE url IS NULL;')
        rows = cur.fetchall()
        company_names = [row[0] for row in rows]
        cur.close()
        if company_names:
            print(f"Found {len(company_names)} unscraped companies to process.")
        else:
            print("No unscraped companies found in 'nift50_social_links'.")
            
    except psycopg2.Error as e:
        print(f"Error fetching company names from DB: {e}")
    return company_names

def save_data_to_db(conn, company_name, url, score):
    """Saves or updates the scraped data for a given company. Accepts None for url and score."""
    try:
        cur = conn.cursor()
        # Use ON CONFLICT to handle updates if the company already exists
        insert_query = """
        INSERT INTO nift50_social_links (company_name, url, score)
        VALUES (%s, %s, %s)
        ON CONFLICT (company_name) DO UPDATE SET
            url = EXCLUDED.url,
            score = EXCLUDED.score;
        """
        cur.execute(insert_query, (company_name, url, score))
        conn.commit()
        cur.close()
        # Adjust print message based on whether data was found or is a placeholder
        if url:
            print(f"  -> Successfully saved data for '{company_name}'")
        else:
            print(f"  -> Saved placeholder for '{company_name}'")
    except psycopg2.Error as e:
        print(f"  -> Error saving data for {company_name}: {e}")
        conn.rollback()

def main():
    """Main function to orchestrate the scraping process."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        setup_database(conn) # Create the table if it doesn't exist
        
        # --- MODIFIED FUNCTION CALL ---
        # Now calls the updated function to get only unscraped names.
        company_names = get_unscraped_company_names(conn)

        if not company_names:
            print("No companies to process. Exiting.")
            return

        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 10)
        base_url = "https://www.ambitionbox.com/"

        for company in company_names:
            print(f"Processing: {company}...")
            try:
                driver.get(base_url)

                search_input = wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input[data-testid='ab_typeahead_search']"))
                )
                search_input.clear()
                search_input.send_keys(company)
                time.sleep(1)

                suggestion_container_selector = "input[data-testid='ab_typeahead_search'] + div"
                suggestion_container = wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, suggestion_container_selector))
                )
                
                all_divs = suggestion_container.find_elements(By.TAG_NAME, "div")
                clickable_options = [opt for opt in all_divs if opt.text.strip()]

                if clickable_options:
                    best_match_element = None
                    highest_score = -1

                    for option in clickable_options:
                        option_text = option.text.strip().split('|')[0].strip()
                        score = fuzz.ratio(company.lower(), option_text.lower())
                        if score > highest_score:
                            highest_score = score
                            best_match_element = option
                    
                    if best_match_element:
                        best_match_text = best_match_element.text.strip().split('|')[0].strip()
                        print(f"  -> Clicking best match: '{best_match_text}' (Score: {highest_score})")
                        best_match_element.click()

                        reviews_button_selector = "div[data-testid='searchItem-Reviews']"
                        reviews_button = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, reviews_button_selector))
                        )
                        reviews_button.click()

                        wait.until(EC.url_contains("/reviews/"))
                        redirected_url = driver.current_url
                        
                        save_data_to_db(conn, company, redirected_url, highest_score)
                    else:
                        print("  -> Could not determine a best match. Saving placeholder.")
                        save_data_to_db(conn, company, None, None)
                else:
                     print("  -> Suggestion box appeared, but no options were found inside. Saving placeholder.")
                     save_data_to_db(conn, company, None, None)

            except (TimeoutException, NoSuchElementException) as e:
                print(f"  -> A page element was not found for '{company}' ({type(e).__name__}). Saving placeholder.")
                save_data_to_db(conn, company, None, None)
            except Exception as e:
                print(f"  -> An unexpected error occurred for '{company}': {e}. Saving placeholder.")
                save_data_to_db(conn, company, None, None)
            
            time.sleep(5)

        driver.quit()
        print("\nScraping process completed.")

    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
