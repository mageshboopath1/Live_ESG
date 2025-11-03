import os
import psycopg2
from urllib.parse import urljoin
import time

from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== CONFIG ==========
PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")


# ========== POSTGRES ==========
def fetch_companies():
    conn = psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS)
    cur = conn.cursor()
    cur.execute("SELECT symbol, company_name FROM company_catalog;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ========== SELENIUM STEALTH SCRAPER ==========
def setup_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    
    driver = webdriver.Remote(
        command_executor='http://esg-selenium:4444/wd/hub',
        options=options
    )

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        webdriver=False,
    )
    return driver


def scrape_annual_reports(symbol: str, company_name: str):
    base_url = "https://www.nseindia.com/companies-listing/corporate-filings-annual-reports"
    driver = setup_driver()
    driver.get(base_url)

    wait = WebDriverWait(driver, 20)
    try:
        # --- Enter company name ---
        input_box = wait.until(EC.presence_of_element_located((By.ID, "ARCompanyInput")))
        input_box.clear()
        input_box.send_keys(symbol)
        time.sleep(2)

        # --- Retry selecting the first suggestion robustly ---
        suggestion_clicked = False
        for attempt in range(5):
            try:
                suggestions = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#ARCompanyInput_listbox p.line1"))
                )
                if suggestions:
                    driver.execute_script("arguments[0].click();", suggestions[0])
                    suggestion_clicked = True
                    break
            except Exception as e:
                print(f"⚠️ Attempt {attempt+1}: Failed to click suggestion ({e})")
                time.sleep(1)
        if not suggestion_clicked:
            print(f"❌ No valid suggestion found for {symbol}")
            return

        # --- Click GO button ---
        go_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@onclick,"annualReportFilter")]'))
        )
        driver.execute_script("arguments[0].click();", go_button)

        # --- Wait for table load ---
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        time.sleep(2)

        # --- Extract report links safely ---
        report_links = []
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        for i in range(len(rows)):
            try:
                # Re-fetch row each time to avoid stale elements
                row = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")[i]
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 4:
                    continue
                file_anchor = cols[3].find_element(By.TAG_NAME, "a")
                file_url = file_anchor.get_attribute("href")
                if file_url and file_url.startswith("https://nsearchives.nseindia.com/annual_reports"):
                    report_links.append(urljoin(base_url, file_url))
            except Exception as e:
                print(f"⚠️ Error processing row {i}: {e}")
                continue

        # --- Save links ---
        if report_links:
            filename = f"links/{symbol}_{company_name.replace(' ', '_')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(report_links))
            print(f"✅ Saved {len(report_links)} links for {symbol} as {filename}")
        else:
            print(f"❌ No report links found for {symbol}")

    except Exception as e:
        print(f"⚠️ Error for {symbol}: {e}")
    finally:
        driver.quit()


# ========== MAIN PIPELINE ==========
def fetch_nse_report_links():
    companies = fetch_companies()
    all_results = []

    for symbol, company_name in companies:
        cname = company_name.replace("Ltd", "Limited").strip()
        print(f"🔍 Fetching: {symbol} / {cname}")
        scrape_annual_reports(symbol, cname)


if __name__ == "__main__":
    fetch_nse_report_links()
