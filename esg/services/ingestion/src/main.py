from fetch_links import fetch_nse_report_links
from download_reports import process_all_links

if __name__ == "__main__":
    print("[INFO] Starting ingestion service...")
    print("[INFO] Downloading reports...")
    process_all_links()
    print("[INFO] Reports downloaded.")
