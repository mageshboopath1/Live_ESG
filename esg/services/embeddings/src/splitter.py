# splitter.py
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from typing import List, Tuple, Dict

def pages_to_chunks(
    text_pages: List[Tuple[int, str]],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict]:
    """
    Split pages using LangChain's RecursiveCharacterTextSplitter for better chunking.
    Returns list of dicts: { page_num, chunk_index, chunk_text }.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # default separators: ["\n\n", "\n", " ", ""]
        separators=None,
        keep_separator=True
    )

    all_chunks = []
    for page_num, page_text in text_pages:
        if not page_text or not page_text.strip():
            continue
        # Create "Document" style list
        # But we only have raw text, so we use split_text directly
        chunk_texts = splitter.split_text(page_text)
        for idx, chunk in enumerate(chunk_texts):
            all_chunks.append({
                "page_num": page_num,
                "chunk_index": idx,
                "chunk_text": chunk
            })
    return all_chunks
