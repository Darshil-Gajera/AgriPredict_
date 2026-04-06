"""
services/ingest.py — Document ingestion & embedding pipeline.

Strategy (PythonAnywhere-friendly, no torch/faiss):
  1. Load CSV cutoff data  →  format as human-readable text chunks
  2. Load FAQ / markdown files  →  split into paragraphs
  3. Load PDF brochures  →  extract text pages
  4. Embed every chunk via Google Gemini text-embedding-004 (free tier)
  5. Cache embeddings to disk as a pickle so restart is instant

Run directly to rebuild:
    python services/ingest.py
"""

import os
import csv
import glob
import pickle
import logging
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import google.generativeai as genai

logger = logging.getLogger(__name__)


# ── Data structure ────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    content: str
    source: str
    doc_type: str          # cutoff_data | faq | pdf | scholarship
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None


# ── CSV cutoff data ───────────────────────────────────────────────────────────

# All cutoff data is also hard-coded here so it's always available even if
# the CSV files are missing (safe fallback for PythonAnywhere).
BUILTIN_CUTOFFS = {
    "1": [
        {"name": "College of Agriculture, JAU, Junagadh", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 80.3833, "SEBC": 80.2500, "SC": 74.5166, "ST": 62.5333, "EWS": 80.8666},
        {"name": "B. A. College of Agriculture, AAU, Anand", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 80.2333, "SEBC": 80.5333, "SC": 74.8833, "ST": 66.8666, "EWS": 79.9666},
        {"name": "N. M. College of Agriculture, NAU, Navsari", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 78.5833, "SEBC": 76.7833, "SC": 69.9833, "ST": 69.5166, "EWS": 76.5666},
        {"name": "CP College of Agriculture, SDAU, Sardarkrushinagar", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 78.1000, "SEBC": 76.7666, "SC": 73.9166, "ST": 58.9666, "EWS": 76.7000},
        {"name": "College of Agriculture, AAU, Vaso", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 74.7166, "SEBC": 73.1666, "SC": 73.5166, "ST": 60.4333, "EWS": 72.0166},
        {"name": "College of Agriculture, Morbi (Currently at Junagadh)", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 75.1166, "SEBC": 73.4166, "SC": 67.7333, "ST": 58.6833, "EWS": 74.8500},
        {"name": "College of Agriculture, JAU, Mota Bhandariya (Amreli)", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 73.9333, "SEBC": 71.4166, "SC": 64.3833, "ST": 56.4666, "EWS": 71.6000},
        {"name": "College of Agriculture, SDAU, Tharad", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 73.5666, "SEBC": 72.0166, "SC": 72.7500, "ST": 57.0833, "EWS": 71.2333},
        {"name": "College of Agriculture, NAU, Bharuch", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 72.8000, "SEBC": 71.6000, "SC": 64.9833, "ST": 64.4666, "EWS": 71.8166},
        {"name": "College of Agriculture, AAU, Jabugam", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 71.4000, "SEBC": 69.9666, "SC": 66.3500, "ST": 59.1666, "EWS": 70.0666},
        {"name": "ASPEE College of Agriculture, JAU, Khapat (Porbandar)", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 71.7666, "SEBC": 69.7333, "SC": 62.6666, "ST": 55.4166, "EWS": 69.9500},
        {"name": "College of Agriculture, JAU, Jamnagar", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 71.7666, "SEBC": 69.7333, "SC": 62.6666, "ST": 55.4166, "EWS": 69.9500},
        {"name": "College of Agriculture, SDAU, Bhuj", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 70.7666, "SEBC": 69.9000, "SC": 65.6000, "ST": 54.2000, "EWS": 69.4000},
        {"name": "College of Agriculture, NAU, Waghai", "course": "B.Sc. (Hons.) Agriculture",
         "GENERAL": 70.0500, "SEBC": 69.4500, "SC": 63.0500, "ST": 66.6500, "EWS": 69.2166},
        {"name": "College of Horticulture, JAU, Junagadh", "course": "B.Sc. (Hons.) Horticulture",
         "GENERAL": 69.2500, "SEBC": 68.2166, "SC": 60.8666, "ST": 56.1000, "EWS": 66.9833},
        {"name": "ASPEE College of Horticulture, NAU, Navsari", "course": "B.Sc. (Hons.) Horticulture",
         "GENERAL": 68.7000, "SEBC": 67.7166, "SC": 61.2833, "ST": 63.0833, "EWS": 67.1500},
        {"name": "College of Horticulture, AAU, Anand", "course": "B.Sc. (Hons.) Horticulture",
         "GENERAL": 68.5500, "SEBC": 67.7833, "SC": 62.8000, "ST": 58.9000, "EWS": 66.4333},
        {"name": "College of Horticulture, SDAU, Jagudan", "course": "B.Sc. (Hons.) Horticulture",
         "GENERAL": 67.7000, "SEBC": 67.0333, "SC": 61.7833, "ST": 54.5830, "EWS": 65.9666},
        {"name": "College of Forestry, NAU, Navsari", "course": "B.Sc. (Hons.) Forestry",
         "GENERAL": 66.7000, "SEBC": 66.0333, "SC": 60.1166, "ST": 58.4666, "EWS": 65.7833},
        {"name": "College of Basic Science & Humanities, SDAU, Sardarkrushinagar", "course": "B.Tech. (Bio Technology)",
         "GENERAL": 67.0000, "SEBC": 66.0000, "SC": 61.5000, "ST": 55.0000, "EWS": 65.7000},
        {"name": "ASPEE Shakilam Biotechnology Institute, NAU, Surat", "course": "B.Tech. (Bio Technology)",
         "GENERAL": 66.5000, "SEBC": 65.9000, "SC": 60.6000, "ST": 57.8666, "EWS": 68.8500},
    ],
    "2": [
        {"name": "College of Agricultural Engineering & Technology, JAU, Junagadh",
         "course": "B.Tech. (Agri. Engineering)",
         "GENERAL": 56.5833, "SEBC": 54.1666, "SC": 52.8833, "ST": 31.6333, "EWS": 52.0333},
        {"name": "College of Agricultural Engineering & Technology, AAU, Godhra",
         "course": "B.Tech. (Agri. Engineering)",
         "GENERAL": 50.9333, "SEBC": 49.4166, "SC": 48.0500, "ST": 32.3500, "EWS": 48.2000},
        {"name": "College of Agricultural Engineering & Technology, NAU, Dediyapada",
         "course": "B.Tech. (Agri. Engineering)",
         "GENERAL": 49.4000, "SEBC": 48.6333, "SC": 47.0000, "ST": 29.7500, "EWS": 47.6333},
        {"name": "College of Agricultural Engineering & Technology, Khedbramha",
         "course": "B.Tech. (Agri. Engineering)",
         "GENERAL": 50.6666, "SEBC": 49.5000, "SC": 47.6166, "ST": 27.7333, "EWS": 49.9500},
        {"name": "College of Food Processing Technology & Bio Energy, AAU, Anand",
         "course": "B.Tech. (Food Technology)",
         "GENERAL": 70.2000, "SEBC": 68.6500, "SC": 54.6000, "ST": 47.3500, "EWS": 68.6666},
        {"name": "College of Food Technology, SDAU, Sardarkrushinagar",
         "course": "B.Tech. (Food Technology)",
         "GENERAL": 64.0666, "SEBC": 60.4000, "SC": 54.2000, "ST": 45.0666, "EWS": 61.4333},
        {"name": "College of R.E. & E.E., SDAU, Sardarkrushinagar",
         "course": "B.Tech. (Renewable Energy & Environmental Engineering)",
         "GENERAL": 52.3000, "SEBC": 50.9666, "SC": 51.8333, "ST": 23.9000, "EWS": 50.3000},
        {"name": "College of Agricultural Information Technology, AAU, Anand",
         "course": "B.Tech. (Agri. IT)",
         "GENERAL": 58.8000, "SEBC": 57.7666, "SC": 54.0166, "ST": 37.9166, "EWS": 55.1000},
    ],
    "3": [
        {"name": "ASPEE College of Nutrition and Community Science, SDAU, Sardarkrushinagar",
         "course": "B.Sc. (Hons) Community Science",
         "GENERAL": 41.7333, "SEBC": 38.3166, "SC": 35.5666, "ST": 28.5166, "EWS": 33.1500},
        {"name": "ASPEE College of Nutrition and Community Science, SDAU, Sardarkrushinagar",
         "course": "B.Sc. (Hons) Food Nutrition & Dietetics",
         "GENERAL": 45.1333, "SEBC": 42.1500, "SC": 59.4833, "ST": 32.3000, "EWS": 33.5000},
    ],
}

BUILTIN_FAQ = """
# AgriPredict FAQ — Gujarat Agriculture University Admissions 2024

## Merit Score Formula
Merit % = (Theory Marks / 300 × 60%) + (GUJCET Marks / 120 × 40%) + Bonus marks
- Theory Marks: PCB or PCM out of 300
- GUJCET: out of 120 marks
- Bonus: 50 marks for Farming certificate (XII-Agri), 25 for International/National/State level prizes
- Students from other boards (CBSE/ICSE) use an adjusted formula

## Categories
- Category 1: B.Sc. Agriculture, Horticulture, Forestry, Biotechnology
- Category 2: B.Tech. Agricultural Engineering, Food Technology, Agri IT, Renewable Energy
- Category 3: B.Sc. Community Science, Food Nutrition & Dietetics

## Universities
- JAU — Junagadh Agricultural University
- AAU — Anand Agricultural University
- NAU — Navsari Agricultural University
- SDAU — Sardarkrushinagar Dantiwada Agricultural University

## Admission Process
1. Appear in GUJCET (Gujarat Common Entrance Test)
2. Register on GSEB admission portal after results
3. Fill online application with marks, category, preference list
4. Merit list published category-wise
5. Seat allotment in 3 rounds
6. Pay token fee within 48 hours of allotment (non-refundable)
7. Report to college with original documents

## Required Documents
- Class 10 & 12 mark sheets (original + 3 copies)
- GUJCET scorecard
- Caste/category certificate (SC/ST/SEBC/EWS)
- Domicile certificate (Gujarat)
- Income certificate (for EWS/scholarship)
- Farming certificate (if applicable, for bonus marks)
- Aadhar card
- Passport-size photos (6)
- Migration certificate (if from other board)

## Reservation Quota
- SEBC (OBC): 27%
- SC: 7%
- ST: 15%
- EWS: 10%
- GENERAL (Open): remaining seats
- PH-VH (Physically Handicapped): 3% horizontal reservation
- Ex-serviceman: 5% horizontal reservation

## Scholarships
### MYSY (Mukhyamantri Yuva Swavalamban Yojana)
- Gujarat domicile required
- Family income < ₹6 lakh per year
- Minimum 80% in Class 12
- Covers tuition fee up to ₹50,000/year

### NSP (National Scholarship Portal)
- For SC/ST/OBC/Minority students
- Apply at scholarships.gov.in
- Income limit: ₹2.5 lakh (SC/ST), ₹1.5 lakh (OBC)

### INSPIRE Scholarship (DST)
- For students in top 1% of their board (Class 12)
- ₹80,000/year for B.Sc./B.Tech.

### ONGC Scholarship
- For SC/ST students in science/engineering
- ₹48,000/year
- Merit-cum-means basis

### Post-Matric Scholarship (State)
- SC/ST/OBC students
- Apply through e-Samaj Kalyan portal (Gujarat)

## Important Dates (Approximate — Check Official Portal)
- GUJCET: March/April
- Result: May
- Online registration: May/June
- Merit list: June/July
- Round 1 seat allotment: July
- Round 2: July/August
- Round 3: August
- College reporting: August/September

## Contact
- GSEB Helpline: 079-26566000
- AgriPredict website: https://gajera06.pythonanywhere.com
"""


def _cutoff_chunks_from_builtin() -> list[Chunk]:
    """Convert built-in cutoff dict to text chunks."""
    chunks = []
    cat_names = {
        "1": "Category 1 (Agriculture, Horticulture, Forestry, Biotechnology)",
        "2": "Category 2 (Agricultural Engineering, Food Technology, Agri IT)",
        "3": "Category 3 (Community Science, Food Nutrition)",
    }
    for cat, colleges in BUILTIN_CUTOFFS.items():
        # One chunk per college with all category cutoffs
        for c in colleges:
            text = (
                f"College: {c['name']}\n"
                f"Course: {c['course']}\n"
                f"Admission Category: {cat_names[cat]}\n"
                f"Last Merit Cutoff (2024, Final Round):\n"
                f"  GENERAL: {c.get('GENERAL', '-')}%\n"
                f"  SEBC: {c.get('SEBC', '-')}%\n"
                f"  SC: {c.get('SC', '-')}%\n"
                f"  ST: {c.get('ST', '-')}%\n"
                f"  EWS: {c.get('EWS', '-')}%\n"
            )
            chunks.append(Chunk(
                content=text,
                source=f"category-{cat}_collegewise_merit.csv",
                doc_type="cutoff_data",
                metadata={"category": cat, "college": c["name"], "course": c["course"]},
            ))
        # Also one summary chunk per category listing all cutoffs for easy comparison
        summary_lines = [f"All {cat_names[cat]} cutoffs (2024 Final Round):"]
        for c in colleges:
            summary_lines.append(
                f"  {c['name']} | {c['course']} — "
                f"GENERAL:{c.get('GENERAL','-')} SEBC:{c.get('SEBC','-')} "
                f"SC:{c.get('SC','-')} ST:{c.get('ST','-')} EWS:{c.get('EWS','-')}"
            )
        chunks.append(Chunk(
            content="\n".join(summary_lines),
            source=f"category-{cat}_summary",
            doc_type="cutoff_data",
            metadata={"category": cat},
        ))
    return chunks


def _cutoff_chunks_from_csv(csv_dir: str) -> list[Chunk]:
    """Load extra CSV files from disk (if present) to supplement built-in data."""
    chunks = []
    for csv_path in glob.glob(f"{csv_dir}/**/*.csv", recursive=True):
        try:
            with open(csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            if not rows:
                continue
            fname = Path(csv_path).name
            for row in rows:
                parts = [f"{k}: {v}" for k, v in row.items() if v and v.strip() not in ("-", "")]
                if parts:
                    chunks.append(Chunk(
                        content=" | ".join(parts),
                        source=fname,
                        doc_type="cutoff_data",
                        metadata={"source_file": fname},
                    ))
            logger.info(f"Loaded CSV: {csv_path} ({len(rows)} rows)")
        except Exception as e:
            logger.warning(f"Failed to load CSV {csv_path}: {e}")
    return chunks


def _faq_chunks_from_builtin() -> list[Chunk]:
    """Split built-in FAQ text into paragraph-sized chunks."""
    chunks = []
    sections = BUILTIN_FAQ.strip().split("\n## ")
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        title = section.split("\n")[0].replace("# ", "").strip()
        text = ("## " if i > 0 else "") + section
        # Further split long sections
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        buffer = []
        for para in paragraphs:
            buffer.append(para)
            if len("\n\n".join(buffer)) > 600:
                chunks.append(Chunk(
                    content="\n\n".join(buffer),
                    source="faq_builtin",
                    doc_type="faq",
                    metadata={"section": title},
                ))
                buffer = []
        if buffer:
            chunks.append(Chunk(
                content="\n\n".join(buffer),
                source="faq_builtin",
                doc_type="faq",
                metadata={"section": title},
            ))
    return chunks


def _faq_chunks_from_files(faq_dir: str) -> list[Chunk]:
    """Load .md and .txt files from disk."""
    chunks = []
    for pattern in ["*.md", "*.txt"]:
        for path in glob.glob(f"{faq_dir}/{pattern}"):
            try:
                text = Path(path).read_text(encoding="utf-8")
                fname = Path(path).name
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                buffer = []
                for para in paragraphs:
                    buffer.append(para)
                    if len("\n\n".join(buffer)) > 800:
                        chunks.append(Chunk(
                            content="\n\n".join(buffer),
                            source=fname,
                            doc_type="faq",
                            metadata={"filename": fname},
                        ))
                        buffer = []
                if buffer:
                    chunks.append(Chunk(
                        content="\n\n".join(buffer),
                        source=fname,
                        doc_type="faq",
                        metadata={"filename": fname},
                    ))
                logger.info(f"Loaded text file: {path}")
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")
    return chunks


def _pdf_chunks(pdf_dir: str) -> list[Chunk]:
    """Load PDFs if pypdf is available (optional)."""
    chunks = []
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.info("pypdf not installed — skipping PDF loading.")
        return chunks
    for pdf_path in glob.glob(f"{pdf_dir}/**/*.pdf", recursive=True):
        try:
            reader = PdfReader(pdf_path)
            fname = Path(pdf_path).name
            for i, page in enumerate(reader.pages):
                text = (page.extract_text() or "").strip()
                if len(text) > 100:
                    chunks.append(Chunk(
                        content=text[:1200],
                        source=fname,
                        doc_type="pdf",
                        metadata={"filename": fname, "page": i + 1},
                    ))
            logger.info(f"Loaded PDF: {pdf_path} ({len(reader.pages)} pages)")
        except Exception as e:
            logger.warning(f"Failed to load PDF {pdf_path}: {e}")
    return chunks


def embed_chunks(chunks: list[Chunk], api_key: str, model: str) -> list[Chunk]:
    """
    Embed all chunks using Gemini text-embedding-004.
    Rate-limited to ~1500 requests/min (free tier).
    """
    genai.configure(api_key=api_key)
    texts = [c.content for c in chunks]
    embedded = []

    BATCH = 100  # embed 100 texts at a time
    for i in range(0, len(texts), BATCH):
        batch_texts = texts[i: i + BATCH]
        try:
            result = genai.embed_content(
                model=model,
                content=batch_texts,
                task_type="retrieval_document",
            )
            for j, emb in enumerate(result["embedding"]):
                chunks[i + j].embedding = emb
            embedded.extend(chunks[i: i + BATCH])
            logger.info(f"Embedded chunks {i}–{i + len(batch_texts) - 1}")
            if i + BATCH < len(texts):
                time.sleep(1)  # small pause to respect rate limit
        except Exception as e:
            logger.error(f"Embedding batch {i} failed: {e}")
            # Still include chunks without embeddings; they'll be skipped at retrieval
            embedded.extend(chunks[i: i + BATCH])

    return embedded


def build_corpus(
    cutoff_dir: str,
    faq_dir: str,
    pdf_dir: str,
    api_key: str,
    embedding_model: str,
    cache_path: str,
) -> list[Chunk]:
    """
    Full ingestion pipeline. Returns list of embedded Chunk objects.
    Saves result to cache_path (pickle).
    """
    logger.info("Starting full ingestion pipeline...")
    chunks: list[Chunk] = []

    # 1. Built-in data (always present)
    chunks.extend(_cutoff_chunks_from_builtin())
    chunks.extend(_faq_chunks_from_builtin())

    # 2. CSV files on disk (supplements built-in)
    if os.path.isdir(cutoff_dir):
        chunks.extend(_cutoff_chunks_from_csv(cutoff_dir))

    # 3. FAQ / markdown files on disk
    if os.path.isdir(faq_dir):
        chunks.extend(_faq_chunks_from_files(faq_dir))

    # 4. PDFs (optional)
    if os.path.isdir(pdf_dir):
        chunks.extend(_pdf_chunks(pdf_dir))

    logger.info(f"Total chunks to embed: {len(chunks)}")

    # 5. Embed
    chunks = embed_chunks(chunks, api_key, embedding_model)

    # 6. Cache to disk
    os.makedirs(Path(cache_path).parent, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(chunks, f)
    logger.info(f"Corpus saved to {cache_path} ({len(chunks)} chunks)")

    return chunks


def load_corpus(cache_path: str) -> list[Chunk]:
    """Load previously cached corpus from disk."""
    with open(cache_path, "rb") as f:
        chunks = pickle.load(f)
    logger.info(f"Corpus loaded from {cache_path} ({len(chunks)} chunks)")
    return chunks


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    from config import get_settings
    s = get_settings()
    if not s.google_api_key:
        print("ERROR: Set CHATBOT_GOOGLE_API_KEY in .env")
        sys.exit(1)
    build_corpus(
        cutoff_dir=s.cutoff_data_dir,
        faq_dir=s.faq_data_dir,
        pdf_dir=s.pdf_data_dir,
        api_key=s.google_api_key,
        embedding_model=s.embedding_model,
        cache_path=s.vector_cache_path,
    )
    print("Done!")