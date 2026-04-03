from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    google_api_key: str = ""
    vector_store_path: str = "./data/vector_store"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "gemini-1.5-flash"
    llm_temperature: float = 0.2
    max_retrieved_docs: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 100

    # Supported languages
    supported_languages: list[str] = ["en", "gu"]

    class Config:
        env_file = "../.env"
        env_prefix = "CHATBOT_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
