import os
import fitz  # PyMuPDF
from config import s3, BUCKET_NAME, logger
from utils import run_ocr_if_needed  # optional, can keep blank or integrate tesseract

def download_file(object_key: str, local_path: str):
    logger.info(f"Downloading {object_key} to {local_path}")
    s3.download_file(BUCKET_NAME, object_key, local_path)

def extract_text_pages(local_path: str, use_ocr: bool=False):
    pages = []
    with fitz.open(local_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if not text and use_ocr:
                text = run_ocr_if_needed(page)
            pages.append((page_num, text))
    return pages

def process_download(object_key: str, use_ocr: bool=False):
    basename = os.path.basename(object_key)
    local_path = f"/tmp/{basename}"
    download_file(object_key, local_path)
    try:
        pages = extract_text_pages(local_path, use_ocr=use_ocr)
    finally:
        try:
            os.remove(local_path)
        except OSError:
            logger.warning(f"Could not remove local file {local_path}")
    return pages
