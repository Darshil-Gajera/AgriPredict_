"""
config.py — AgriPredict Chatbot Configuration
Uses environment variables with prefix CHATBOT_

Example (.env):
CHATBOT_GOOGLE_API_KEY=your_key
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# ✅ Explicitly load .env (important for Docker)
load_dotenv(dotenv_path="/app/.env", override=True)


class Settings(BaseSettings):
    # ── Gemini / Google ──────────────────────────────────────────────────────
    google_api_key: str = "AIzaSyAx7lJw5mz4SQwvS9m2iiGUqC4aufRKHM0"
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"
    llm_temperature: float = 0.2

    # ── Retrieval ────────────────────────────────────────────────────────────
    max_retrieved_docs: int = 6
    similarity_threshold: float = 0.30

    # ── Data paths ───────────────────────────────────────────────────────────
    cutoff_data_dir: str = "/app/data/cutoffs"
    faq_data_dir: str = "/app/data/faq"
    pdf_data_dir: str = "/app/data/pdfs"
    vector_cache_path: str = "/app/data/vector_cache.pkl"

    # ── Security ─────────────────────────────────────────────────────────────
    ingest_secret: str = "change-me-in-production"

    # ── Supported languages ──────────────────────────────────────────────────
    supported_languages: list[str] = ["en", "gu"]

    class Config:
        env_prefix = "CHATBOT_"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()