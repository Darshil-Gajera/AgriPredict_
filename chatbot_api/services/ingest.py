"""
Ingestion pipeline:
  PDF brochures + notification PDFs  →  PyPDFLoader
  Cutoff CSV / Excel                 →  CSVLoader / pandas
  FAQ markdown                       →  TextLoader
  All chunks → HuggingFace embeddings → FAISS vector store
"""

import os
import glob
import asyncio
import logging
from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _load_pdfs(pdf_dir: str) -> list[Document]:
    docs = []
    for pdf_path in glob.glob(f"{pdf_dir}/**/*.pdf", recursive=True):
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            # Tag each page with its source filename
            for page in pages:
                page.metadata["doc_type"] = "brochure_or_notification"
                page.metadata["filename"] = Path(pdf_path).name
            docs.extend(pages)
            logger.info(f"Loaded PDF: {pdf_path} ({len(pages)} pages)")
        except Exception as e:
            logger.warning(f"Failed to load {pdf_path}: {e}")
    return docs


def _load_cutoffs_csv(csv_dir: str) -> list[Document]:
    """Convert cutoff CSV rows into human-readable Document chunks."""
    docs = []
    for csv_path in glob.glob(f"{csv_dir}/**/*.csv", recursive=True):
        try:
            df = pd.read_csv(csv_path)
            # Expected columns: college_code, college_name, course, year,
            #                   round, student_category, last_merit
            for _, row in df.iterrows():
                text = (
                    f"College: {row.get('college_name', '')} "
                    f"(Code: {row.get('college_code', '')}) | "
                    f"Course: {row.get('course', '')} | "
                    f"Year: {row.get('year', '')} | "
                    f"Round: {row.get('round', '')} | "
                    f"Category: {row.get('student_category', '')} | "
                    f"Last admitted merit: {row.get('last_merit', '')}"
                )
                docs.append(Document(
                    page_content=text,
                    metadata={
                        "doc_type": "cutoff_data",
                        "source": Path(csv_path).name,
                        "college_code": str(row.get("college_code", "")),
                        "year": str(row.get("year", "")),
                        "student_category": str(row.get("student_category", "")),
                    },
                ))
            logger.info(f"Loaded CSV cutoffs: {csv_path} ({len(df)} rows)")
        except Exception as e:
            logger.warning(f"Failed to load CSV {csv_path}: {e}")
    return docs


def _load_text_files(text_dir: str) -> list[Document]:
    """Load FAQ / markdown / plain text files."""
    docs = []
    for pattern in ["*.md", "*.txt"]:
        for path in glob.glob(f"{text_dir}/{pattern}"):
            try:
                loader = TextLoader(path, encoding="utf-8")
                loaded = loader.load()
                for doc in loaded:
                    doc.metadata["doc_type"] = "faq_or_guide"
                    doc.metadata["filename"] = Path(path).name
                docs.extend(loaded)
                logger.info(f"Loaded text file: {path}")
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")
    return docs


def _load_scholarship_text(text_dir: str) -> list[Document]:
    """Load scholarship info markdown."""
    docs = []
    for path in glob.glob(f"{text_dir}/scholarship*.md"):
        try:
            loader = TextLoader(path, encoding="utf-8")
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["doc_type"] = "scholarship"
            docs.extend(loaded)
        except Exception as e:
            logger.warning(f"Failed to load scholarship file {path}: {e}")
    return docs


def build_vector_store(
    pdf_dir: str = "./data/pdfs",
    cutoff_dir: str = "./data/cutoffs",
    faq_dir: str = "./data/faq",
    save_path: str = None,
) -> FAISS:
    """Load all source documents, split, embed, and build FAISS index."""
    save_path = save_path or settings.vector_store_path

    logger.info("Starting document ingestion...")

    all_docs: list[Document] = []
    all_docs.extend(_load_pdfs(pdf_dir))
    all_docs.extend(_load_cutoffs_csv(cutoff_dir))
    all_docs.extend(_load_text_files(faq_dir))
    all_docs.extend(_load_scholarship_text(faq_dir))

    logger.info(f"Total raw documents loaded: {len(all_docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(all_docs)
    logger.info(f"Total chunks after splitting: {len(chunks)}")

    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    vector_store = FAISS.from_documents(chunks, embeddings)

    os.makedirs(save_path, exist_ok=True)
    vector_store.save_local(save_path)
    logger.info(f"Vector store saved to {save_path} with {len(chunks)} chunks.")

    return vector_store


def load_vector_store(path: str = None) -> FAISS:
    """Load an existing FAISS index from disk."""
    path = path or settings.vector_store_path
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    store = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    logger.info(f"Vector store loaded from {path}")
    return store


if __name__ == "__main__":
    # Run directly to (re)build the index:  python ingest.py
    logging.basicConfig(level=logging.INFO)
    build_vector_store()
