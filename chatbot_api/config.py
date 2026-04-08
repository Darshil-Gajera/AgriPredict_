"""
config.py — AgriPredict Chatbot Configuration
Set environment variables with prefix CHATBOT_ in your .env file.

Required:
    CHATBOT_GOOGLE_API_KEY=your-gemini-api-key-here

Optional (defaults shown):
    CHATBOT_LLM_MODEL=gemini-1.5-flash
    CHATBOT_LLM_TEMPERATURE=0.2
    CHATBOT_MAX_RETRIEVED_DOCS=6
    CHATBOT_INGEST_SECRET=change-me-in-production
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Gemini / Google ──────────────────────────────────────────────────────
    google_api_key: str = "AIzaSyDyMAGb88PoFnI_59AxUD7BI25yY1ND40I"                          # REQUIRED — set in .env
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"  # Gemini embeddings (free)
    llm_temperature: float = 0.2

    # ── Retrieval ────────────────────────────────────────────────────────────
    max_retrieved_docs: int = 6
    similarity_threshold: float = 0.30               # cosine similarity cutoff

    # ── Data paths ───────────────────────────────────────────────────────────
    cutoff_data_dir: str = "./data/cutoffs"          # place CSV files here
    faq_data_dir: str = "./data/faq"                 # place .md / .txt files here
    pdf_data_dir: str = "./data/pdfs"                # place PDF brochures here
    vector_cache_path: str = "./data/vector_cache.pkl"  # pickled embedding cache

    # ── Security ─────────────────────────────────────────────────────────────
    ingest_secret: str = "change-me-in-production"

    # ── Supported languages ──────────────────────────────────────────────────
    supported_languages: list[str] = ["en", "gu"]

    class Config:
        env_file = ".env"
        env_prefix = "CHATBOT_"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
