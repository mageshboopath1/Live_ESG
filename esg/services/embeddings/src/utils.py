import logging

def setup_logger(name=None, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

def run_ocr_if_needed(page):
    # Placeholder: implement OCR logic if page has no text
    # For now, just return empty or raise?
    return ""
