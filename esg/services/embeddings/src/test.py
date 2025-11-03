from extractor import process_download
from splitter import pages_to_chunks

pages = process_download("ADANIENT/2024_2025/AR_26463_ADANIENT_2024_2025_A_29052025234750.pdf")
chunks = pages_to_chunks(pages)
print(len(chunks), chunks[0])
