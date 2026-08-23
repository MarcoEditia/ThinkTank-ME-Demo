from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class Settings(BaseSettings):
    anthropic_api_key: str | None = None
    claude_model: str = "sonnet"
    embedding_model_path: str | None = None
    embedding_model: str = "BAAI/bge-m3"
    request_timeout_seconds: float = 20.0
    research_timeout_seconds: float = 90.0
    vector_index_storage: str | Path
    forecast_cache_db: str | Path = Path("storage/forecast_cache.db")
    forecast_cache_ttl_seconds: int = 21_600
    forecast_cache_version: str = "v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()


if settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
