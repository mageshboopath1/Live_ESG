import pandas as pd
import requests
import sqlalchemy
import os
from io import StringIO
from sqlalchemy import bindparam, text

print("[INFO] Loading environment variables...")
# Specify the path to your .env file


NSE_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"

DB_URL = f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB')}"

print(f"[INFO] DB_URL: {DB_URL}")

def fetch_nse_data():
    print("[INFO] Fetching NSE data from:", NSE_URL)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(NSE_URL, timeout=15, headers=headers)
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response headers: {response.headers}")
        print(f"[DEBUG] Response content (first 200 chars): {response.text[:200]}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        raise
    print("[INFO] NSE data fetched, parsing CSV...")
    df = pd.read_csv(StringIO(response.text))
    print("[INFO] CSV parsed.")
    return df

def upsert_to_db(df, engine):
    print("[INFO] Syncing only the current 50 NIFTY companies...")

    current_symbols = df["Symbol"].tolist()

    with engine.begin() as conn:
        # Step 1: Delete old entries not in the current NIFTY 50
        print("[INFO] Removing companies not in the latest NIFTY 50...")
        delete_stmt = text("""
            DELETE FROM company_catalog
            WHERE symbol NOT IN :symbols
        """).bindparams(bindparam("symbols", expanding=True))

        conn.execute(delete_stmt, {"symbols": current_symbols})

        # Step 2: Upsert current companies
        print("[INFO] Upserting the latest 50 companies...")
        for idx, row in df.iterrows():
            print(f"[DEBUG] Upserting row {idx+1}/{len(df)}: {row['Company Name']}")
            conn.execute(
                text("""
                INSERT INTO company_catalog (company_name, industry, symbol, series, isin_code)
                VALUES (:name, :industry, :symbol, :series, :isin)
                ON CONFLICT (symbol, isin_code)
                DO UPDATE SET
                  company_name = EXCLUDED.company_name,
                  industry = EXCLUDED.industry,
                  series = EXCLUDED.series,
                  updated_at = NOW();
                """),
                {
                    "name": row["Company Name"],
                    "industry": row["Industry"],
                    "symbol": row["Symbol"],
                    "series": row["Series"],
                    "isin": row["ISIN Code"]
                }
            )

    print("[INFO] Upsert complete — now only 50 companies remain.")
    
import time

def wait_for_db(db_url, retries=10, delay=3):
    for attempt in range(retries):
        try:
            engine = sqlalchemy.create_engine(db_url)
            # Try connecting
            with engine.connect() as conn:
                print(f"[INFO] Connected to DB on attempt {attempt+1}")
                return engine
        except Exception as e:
            print(f"[WARN] DB connection failed (attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to database after retries.")

if __name__ == "__main__":
    print("[INFO] Starting company catalog sync...")
    df = fetch_nse_data()
    print("[INFO] Fetched data sample:\n", df.head())
    print("[INFO] Connecting to database...")
    engine = wait_for_db(DB_URL)
    print("[INFO] Connected. Beginning upsert...")
    upsert_to_db(df, engine)
    print("[INFO] Company catalog synced.")
