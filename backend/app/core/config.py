"""Application configuration, loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Runtime settings. Every value can be overridden via the environment."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "InsightAI"
    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+psycopg://insightai:insightai@localhost:5432/insightai"

    # Where uploaded CSV files are stored. Raw rows never go into PostgreSQL.
    storage_dir: Path = BACKEND_DIR / "storage"

    max_upload_bytes: int = 20 * 1024 * 1024  # 20 MB
    preview_rows: int = 20
    max_analysis_rows: int = 500_000

    # AI is optional. With no key the assistant is disabled but everything else works.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: float = 30.0

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Identity is deliberately minimal: a header names the user, and datasets are
    # scoped to that user. Real authentication is out of scope for this project.
    default_user_email: str = "demo@insightai.local"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
