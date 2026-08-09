from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / backend/.env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "TripAI"
    API_PREFIX: str = "/api"

    # Defaults to a local SQLite file so the project runs with zero setup.
    # For deployment set DATABASE_URL to PostgreSQL (e.g. Supabase).
    DATABASE_URL: str = "sqlite:///./tripai.db"

    # Auth
    JWT_SECRET_KEY: str = "tripai-dev-secret-change-me-0123456789abcdef"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # 演示项目：允许任意前端来源（配合 Bearer Token 认证，无 Cookie 风险）。
    # 正式商用时可收紧为具体域名列表。
    CORS_ORIGINS: List[str] = ["*"]

    # LLM provider (OpenAI-compatible /chat/completions)
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT_SECONDS: int = 240

    # AMap Web Service API (server-side POI search; personal quota is free)
    AMAP_WEB_KEY: str = ""
    AMAP_SEARCH_URL: str = "https://restapi.amap.com/v3/place/text"

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return a URL the SQLAlchemy engine can load without ambiguity.

        We ship psycopg3, so a plain `postgresql://` URL (which SQLAlchemy
        maps to psycopg2 by default) is normalized to `postgresql+psycopg://`.
        """
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()
