from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    aws_s3_bucket: str
    aws_s3_prefix: str = "documents/"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "enterprise_documents"

    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    rag_top_k: int = 5
    rag_score_threshold: float = 0.2
    agent_max_steps: int = 8

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
