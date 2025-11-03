import os
import re
import json
import zipfile
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import subprocess
import boto3
from botocore.client import Config
import pika
import psycopg2
from psycopg2.extras import RealDictCursor
from tqdm import tqdm

# --- MinIO Config ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = "esg_minio"
MINIO_SECRET_KEY = "esg_secret"
BUCKET_NAME = "esg-reports"

# --- Database Config ---
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "moz")
DB_USER = os.getenv("POSTGRES_USER", "drfitz")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "h4i1hydr4")

# --- Directories ---
LINKS_DIR = Path("links")
DOWNLOADS_DIR = Path("downloads")
LEDGER_FILE = Path("download_ledger.json")

DOWNLOADS_DIR.mkdir(exist_ok=True)

# --- Initialize MinIO client ---
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

# --- Load or init ledger ---
if LEDGER_FILE.exists():
    with open(LEDGER_FILE, "r") as f:
        LEDGER = json.load(f)
else:
    LEDGER = {}

def save_ledger():
    with open(LEDGER_FILE, "w") as f:
        json.dump(LEDGER, f, indent=2)

def update_ledger(key: str, status: str):
    LEDGER[key] = {
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    save_ledger()

def ensure_bucket_exists():
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass
    except s3.exceptions.BucketAlreadyExists:
        pass

def get_db_connection():
    """Create and return a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def ensure_company_exists(company_name: str, symbol: str = None) -> int:
    """
    Ensure company exists in company_catalog table.
    Returns the company_id.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Use symbol if provided, otherwise use company_name as symbol
            company_symbol = symbol if symbol else company_name
            
            # Try to find existing company
            cur.execute(
                "SELECT id FROM company_catalog WHERE symbol = %s",
                (company_symbol,)
            )
            result = cur.fetchone()
            
            if result:
                return result['id']
            
            # Insert new company if not exists
            # Generate a placeholder ISIN code if not available
            isin_code = f"INE{company_symbol[:6].upper()}01"
            
            cur.execute(
                """
                INSERT INTO company_catalog (company_name, symbol, isin_code)
                VALUES (%s, %s, %s)
                ON CONFLICT (symbol, isin_code) DO UPDATE 
                SET company_name = EXCLUDED.company_name
                RETURNING id
                """,
                (company_name, company_symbol, isin_code)
            )
            result = cur.fetchone()
            conn.commit()
            print(f"✅ Ensured company exists: {company_name} (ID: {result['id']})", flush=True)
            return result['id']
    finally:
        conn.close()

def insert_ingestion_metadata(company_id: int, object_key: str, file_type: str) -> int:
    """
    Insert record into ingestion_metadata table.
    Returns the metadata record id.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO ingestion_metadata (company_id, source, file_path, file_type, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (company_id, source, file_path) DO UPDATE
                SET status = EXCLUDED.status, ingested_at = NOW()
                RETURNING id
                """,
                (company_id, "NSE", object_key, file_type, "SUCCESS")
            )
            result = cur.fetchone()
            conn.commit()
            print(f"✅ Inserted ingestion metadata: {object_key} (ID: {result['id']})", flush=True)
            return result['id']
    finally:
        conn.close()


# --- Utilities ---

def parse_years_from_url(url: str):
    current_year = datetime.now().year
    match = re.search(r"(20\d{2})_(20\d{2})", url)
    if match:
        y1, y2 = int(match.group(1)), int(match.group(2))
        if 2008 <= y1 <= current_year and 2008 <= y2 <= current_year and y1 <= y2:
            return f"{y1}_{y2}"
    return "unknown_year"

def get_filename_from_url(url: str):
    return os.path.basename(urlparse(url).path)

def build_object_key(company_name: str, years: str, filename: str):
    return f"{company_name}/{years}/{filename}"

def upload_to_minio(file_path: Path, object_key: str):
    normalized_key = re.sub(r"(/?[^/]+/)\1+", r"\1", object_key)
    s3.upload_file(str(file_path), BUCKET_NAME, normalized_key)
    print(f"✅ Uploaded to MinIO: s3://{BUCKET_NAME}/{normalized_key}", flush=True)

def publish_queue_message(queue_name: str, message_data: dict, delay_seconds: int = 0, max_retries: int = 5, base_delay: int = 3):
    """
    Publish JSON message to RabbitMQ queue with retry and exponential backoff.
    
    Args:
        queue_name: Name of the queue to publish to
        message_data: Dictionary containing message data
        delay_seconds: Optional delay in seconds before message becomes available
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    """
    attempt = 0
    while attempt < max_retries:
        try:
            credentials = pika.PlainCredentials("esg_rabbitmq", "esg_secret")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host="rabbitmq",
                    credentials=credentials,
                    heartbeat=30,
                    blocked_connection_timeout=300
                )
            )
            channel = connection.channel()
            
            # Declare queue as durable
            channel.queue_declare(queue=queue_name, durable=True)
            
            # Prepare message properties
            properties = pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
            
            # Add delay if specified (using message TTL and dead letter exchange)
            if delay_seconds > 0:
                # Create delay queue with TTL
                delay_queue_name = f"{queue_name}-delay"
                channel.queue_declare(
                    queue=delay_queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': delay_seconds * 1000,  # Convert to milliseconds
                        'x-dead-letter-exchange': '',
                        'x-dead-letter-routing-key': queue_name
                    }
                )
                # Publish to delay queue
                channel.basic_publish(
                    exchange='',
                    routing_key=delay_queue_name,
                    body=json.dumps(message_data),
                    properties=properties
                )
                print(f"✅ Sent to RabbitMQ {queue_name} (delayed {delay_seconds}s): {message_data.get('object_key', message_data)}", flush=True)
            else:
                # Publish directly to target queue
                channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message_data),
                    properties=properties
                )
                print(f"✅ Sent to RabbitMQ {queue_name}: {message_data.get('object_key', message_data)}", flush=True)
            
            connection.close()
            return True
            
        except Exception as e:
            attempt += 1
            wait_time = base_delay * (2 ** (attempt - 1))
            print(f"⚠️ Retry {attempt}/{max_retries} - Failed to send to RabbitMQ {queue_name}: {e}", flush=True)
            if attempt < max_retries:
                print(f"   ⏳ Retrying in {wait_time} seconds...", flush=True)
                time.sleep(wait_time)
            else:
                print(f"❌ Giving up after {max_retries} attempts. Could not send to {queue_name}: {message_data}", flush=True)
                return False

def send_to_embedding_queue(object_key: str, company_name: str, report_year: int):
    """Send message to embedding-tasks queue."""
    message_data = {
        "object_key": object_key,
        "company_name": company_name,
        "report_year": report_year
    }
    return publish_queue_message("embedding-tasks", message_data)

def send_to_extraction_queue(object_key: str, company_name: str, report_year: int, delay_seconds: int = 300):
    """
    Send message to extraction-tasks queue with delay.
    Default delay is 5 minutes (300 seconds) to allow embeddings to be generated.
    """
    message_data = {
        "object_key": object_key,
        "company_name": company_name,
        "report_year": report_year
    }
    return publish_queue_message("extraction-tasks", message_data, delay_seconds=delay_seconds)

def download_with_aria(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Referer": "https://www.nseindia.com/market-data/live-equity-market"
    }

    cmd = [
        "aria2c", "-x", "4", "-s", "4", "-k", "1M",
        "--retry-wait=5", "--max-tries=5",
        "-d", str(dest.parent), "-o", dest.name,
    ]
    for key, value in headers.items():
        cmd.extend(["--header", f"{key}: {value}"])
    cmd.append(url)
    subprocess.run(cmd, check=True)

# --- Main Logic ---

def extract_report_year(years_str: str) -> int:
    """
    Extract the starting year from a year string like '2023_2024'.
    Returns the first year as an integer.
    """
    if '_' in years_str:
        return int(years_str.split('_')[0])
    # Try to extract any 4-digit year
    match = re.search(r'20\d{2}', years_str)
    if match:
        return int(match.group(0))
    # Default to current year if unable to parse
    return datetime.now().year

def download_and_process(url: str, company_name: str):
    if not url.strip():
        return

    filename = get_filename_from_url(url)
    years = parse_years_from_url(url)
    ledger_key = f"{company_name}/{years}/{filename}"

    # Skip if already successful
    if ledger_key in LEDGER and LEDGER[ledger_key]["status"] == "success":
        print(f"⏩ Skipping already processed: {ledger_key}", flush=True)
        return

    company_dir = DOWNLOADS_DIR / company_name / years
    file_path = company_dir / filename
    print(f"⬇️ Downloading (aria2c): {url}", flush=True)

    update_ledger(ledger_key, "pending")

    try:
        # Ensure company exists in database before processing
        company_id = ensure_company_exists(company_name)
        
        download_with_aria(url, file_path)

        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(file_path, "r") as z:
                z.extractall(company_dir)
                print(f"📦 Extracted ZIP → {company_dir}", flush=True)
                for extracted_file in company_dir.rglob("*"):
                    if extracted_file.is_file() and not extracted_file.name.startswith("__"):
                        object_key = build_object_key(company_name, years, extracted_file.name)
                        upload_to_minio(extracted_file, object_key)
                        
                        # Determine file type
                        file_type = extracted_file.suffix.lstrip('.').lower() or 'unknown'
                        
                        # Insert metadata after successful upload
                        insert_ingestion_metadata(company_id, object_key, file_type)

                        # Publish to queues only for PDFs from recent years
                        if object_key.endswith(".pdf") and years in ["2023_2024", "2024_2025"]:
                            report_year = extract_report_year(years)
                            # Send to both embedding and extraction queues
                            send_to_embedding_queue(object_key, company_name, report_year)
                            send_to_extraction_queue(object_key, company_name, report_year, delay_seconds=300)
        else:
            object_key = build_object_key(company_name, years, filename)
            upload_to_minio(file_path, object_key)
            
            # Determine file type
            file_type = Path(filename).suffix.lstrip('.').lower() or 'unknown'
            
            # Insert metadata after successful upload
            insert_ingestion_metadata(company_id, object_key, file_type)
            
            # Publish to queues only for PDFs from recent years
            if object_key.endswith(".pdf") and years in ["2023_2024", "2024_2025"]:
                report_year = extract_report_year(years)
                # Send to both embedding and extraction queues
                send_to_embedding_queue(object_key, company_name, report_year)
                send_to_extraction_queue(object_key, company_name, report_year, delay_seconds=300)

        update_ledger(ledger_key, "success")

    except subprocess.CalledProcessError as e:
        print(f"❌ aria2c failed for {url}: {e}", flush=True)
        update_ledger(ledger_key, "failed")
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}", flush=True)
        update_ledger(ledger_key, "failed")

def process_all_links():
    ensure_bucket_exists()

    all_urls = []
    for file in LINKS_DIR.glob("*.txt"):
        company_name = file.stem.split("_")[0]
        with open(file, "r", encoding="utf-8") as f:
            for url in f:
                url = url.strip()
                if url:
                    all_urls.append((url, company_name))

    for url, company_name in tqdm(all_urls, desc="Total progress", unit="file"):
        download_and_process(url, company_name)

    # Retry loop for failed downloads every 2 minutes
    while True:
        failed_items = [k for k, v in LEDGER.items() if v["status"] == "failed"]
        if not failed_items:
            print("✅ All files processed successfully!", flush=True)
            break

        print(f"🔁 Retrying {len(failed_items)} failed downloads in 2 minutes...", flush=True)
        time.sleep(120)

        for ledger_key in failed_items:
            company_name, years, filename = ledger_key.split("/", 2)
            # Try to re-fetch original URL from link files
            # (Brute-force find URL matching filename)
            for file in LINKS_DIR.glob("*.txt"):
                if not file.stem.startswith(company_name):
                    continue
                with open(file, "r", encoding="utf-8") as f:
                    for url in f:
                        if filename in url:
                            print(f"♻️ Retrying {ledger_key}", flush=True)
                            download_and_process(url.strip(), company_name)
                            break

if __name__ == "__main__":
    process_all_links()
