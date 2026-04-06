#!/usr/bin/env python
"""
ingest.py — Run this to (re)build the vector embedding cache.

Usage:
    python ingest.py

Run this whenever you:
  • Add new PDF brochures to data/pdfs/
  • Add new CSV cutoff files to data/cutoffs/
  • Update data/faq/*.md files

The script will:
  1. Load built-in cutoff data + FAQ (always available)
  2. Load any extra CSVs from data/cutoffs/
  3. Load any .md/.txt files from data/faq/
  4. Load PDFs from data/pdfs/ (requires: pip install pypdf)
  5. Embed everything via Gemini text-embedding-004
  6. Save to data/vector_cache.pkl
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from config import get_settings
from services.ingest import build_corpus

if __name__ == "__main__":
    s = get_settings()
    if not s.google_api_key:
        print("\nERROR: CHATBOT_GOOGLE_API_KEY is not set.")
        print("Add it to your .env file:\n  CHATBOT_GOOGLE_API_KEY=AIza...")
        sys.exit(1)

    import shutil
    cache = Path(s.vector_cache_path)
    if cache.exists():
        logging.info(f"Removing old cache: {cache}")
        cache.unlink()

    logging.info("Starting ingestion...")
    chunks = build_corpus(
        cutoff_dir=s.cutoff_data_dir,
        faq_dir=s.faq_data_dir,
        pdf_dir=s.pdf_data_dir,
        api_key=s.google_api_key,
        embedding_model=s.embedding_model,
        cache_path=s.vector_cache_path,
    )
    embedded = sum(1 for c in chunks if c.embedding)
    print(f"\nDone! {len(chunks)} chunks total, {embedded} embedded.")
    print(f"Cache saved to: {s.vector_cache_path}")