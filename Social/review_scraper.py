import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime, date
from tqdm import tqdm

# --- Database Configuration ---
# IMPORTANT: This should be the same as your other script.
DB_CONFIG = {
    "dbname": "Environment",
    "user": "mageshboopathi",
    "password": "jesus",
    "host": "localhost",
    "port": "5432"
}

def setup_employee_reviews_table(conn):
    """Creates the employee_reviews table if it doesn't exist."""
    try:
        cur = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS employee_reviews (
            id SERIAL PRIMARY KEY,
            company_name TEXT,
            url TEXT,
            job_title TEXT,
            job_type TEXT,
            rating REAL,
            updated_date DATE,
            department TEXT,
            review_text TEXT
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        cur.close()
        print("Database setup complete. 'employee_reviews' table is ready.")
    except psycopg2.Error as e:
        print(f"Error during database setup: {e}")
        conn.rollback()

def save_review_to_db(conn, review_data):
    """Saves a single review's data to the database."""
    try:
        cur = conn.cursor()
        insert_query = """
        INSERT INTO employee_reviews (
            company_name, url, job_title, job_type, rating, 
            updated_date, department, review_text
        ) VALUES (
            %(company_name)s, %(url)s, %(job_title)s, %(job_type)s, %(rating)s, 
            %(updated_date)s, %(department)s, %(review_text)s
        );
        """
        cur.execute(insert_query, review_data)
        conn.commit()
        cur.close()
    except psycopg2.Error as e:
        print(f"\nError saving data to DB: {e}")
        conn.rollback()


def get_review_urls_from_db(conn):
    """Fetches valid URLs from the nift50_social_links table."""
    urls_to_scrape = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT company_name, url FROM nift50_social_links WHERE url IS NOT NULL;')
        rows = cur.fetchall()
        urls_to_scrape = [(row[0], row[1]) for row in rows]
        cur.close()
        if urls_to_scrape:
            print(f"Found {len(urls_to_scrape)} URLs to process.")
        else:
            print("No valid URLs found in 'nift50_social_links' to scrape.")
    except psycopg2.Error as e:
        print(f"Error fetching URLs from DB: {e}")
    return urls_to_scrape

def extract_text(element, xpath_selector, default="N/A"):
    """Safely extracts text from an element using an XPath selector."""
    try:
        return element.find_element(By.XPATH, xpath_selector).text.strip()
    except NoSuchElementException:
        return default

def main():
    """Main function to orchestrate the review scraping process."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        setup_employee_reviews_table(conn)
        company_data = get_review_urls_from_db(conn)

        if not company_data:
            print("No URLs to process. Exiting.")
            return

        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 10) 
        
        company_progress = tqdm(company_data, desc="Companies")
        for company_name, url in company_progress:
            
            base_company_url = f"{url}?sort_by=latest"
            
            stop_scraping_for_this_company = False
            page_num = 1

            while not stop_scraping_for_this_company:
                if page_num == 1:
                    current_url = base_company_url
                else:
                    current_url = f"{base_company_url}&page={page_num}"
                
                company_progress.set_description(f"{company_name} | Page {page_num}")

                try:
                    driver.get(current_url)
                    reviews_section_xpath = "//*[@id='reviews-section' or @id='detailed-reviews-section']"
                    
                    reviews_container = wait.until(
                        EC.visibility_of_element_located((By.XPATH, reviews_section_xpath))
                    )
                    
                    review_cards = reviews_container.find_elements(By.XPATH, "./div")

                    if not review_cards:
                        break

                    for card in review_cards:
                        try:
                            read_more_link = card.find_element(By.XPATH, ".//span[contains(text(), 'Read More')]")
                            read_more_link.click()
                            time.sleep(0.5)
                        except NoSuchElementException:
                            pass
                        
                        updated_time_str = extract_text(card, ".//span[contains(@class, 'text-secondary-text')]")
                        updated_date = None
                        if "updated on" in updated_time_str:
                            date_part = updated_time_str.replace("updated on", "").strip()
                            try:
                                updated_date_obj = datetime.strptime(date_part, "%d %b %Y").date()
                                if updated_date_obj.year < 2024:
                                    stop_scraping_for_this_company = True
                                    break
                                updated_date = updated_date_obj
                            except ValueError:
                                pass # Keep updated_date as None
                        
                        company_progress.set_description(f"{company_name} | Page {page_num} | Date: {updated_date or 'N/A'}")

                        rating_str = extract_text(card, ".//span[contains(@class, 'text-primary-text') and contains(@class, 'font-pn-700')]")
                        try:
                            rating = float(rating_str)
                        except (ValueError, TypeError):
                            rating = None

                        review_data = {
                            "company_name": company_name,
                            "url": current_url,
                            "job_title": extract_text(card, ".//div[contains(@class, 'mb-1')]/h2"),
                            "job_type": extract_text(card, ".//p[contains(@class, 'bg-grey-200')]"),
                            "rating": rating,
                            "updated_date": updated_date,
                            "department": extract_text(card, ".//p[contains(@class, 'font-pn-400') and not(contains(@class, 'bg-grey-200'))]"),
                            "review_text": extract_text(card, ".//div[@class='relative']")
                        }
                        save_review_to_db(conn, review_data)

                    if stop_scraping_for_this_company:
                        break
                    
                    page_num += 1
                    time.sleep(1) # Small delay between page loads

                except TimeoutException:
                    break
                except Exception as e:
                    tqdm.write(f"\nAn unexpected error occurred for '{company_name}' on page {page_num}: {e}")
                    break
            
            time.sleep(3)

        driver.quit()
        print("\nReview scraping process completed.")

    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()