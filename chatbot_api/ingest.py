#!/usr/bin/env python
"""
ingest.py — Run this script whenever you add new PDFs or update cutoff data.

Usage:
    python ingest.py

It will:
  1. Load all PDFs from data/pdfs/
  2. Load cutoffs from data/cutoffs/cutoffs.csv
  3. Load data/scholarships.md and data/faq.md
  4. Split, embed, and save FAISS index to data/faiss_index/
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from services.rag_chain import RagChain

if __name__ == "__main__":
    import shutil

    index_dir = Path(__file__).parent / "data" / "faiss_index"
    if index_dir.exists():
        logging.info("Removing old FAISS index …")
        shutil.rmtree(index_dir)

    logging.info("Starting ingestion …")
    chain = RagChain()
    chain.load()
    logging.info(f"Done. {chain.doc_count} chunks indexed.")
