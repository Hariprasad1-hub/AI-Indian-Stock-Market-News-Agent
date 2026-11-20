
"""Application configuration for TRADEMIND AI."""

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_PATH = (PROJECT_ROOT / "trademind.db").as_posix()
DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"


class Settings(BaseSettings):
    PROJECT_NAME: str = "TRADEMIND AI"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = DEFAULT_SQLITE_URL

    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
    )

    WEBHOOK_SECRET: str | None = None

    MAX_POSITION_PCT: float = 0.20
    MAX_SECTOR_PCT: float = 0.35
    PRICE_MAX_STALENESS_MINUTES: int = 15
    MAX_DAILY_LOSS_PCT: float = 0.05
    TRANSACTION_FEE_PCT: float = 0.001
    DUPLICATE_PROPOSAL_WINDOW_MINUTES: int = 5

    BAND_API_KEY: str | None = None
    LYZR_API_KEY: str | None = None
    FINCH_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        url = str(value).strip()

        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://"):]

        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://"):]

        return url

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        if isinstance(value, (list, tuple)):
            return [
                str(origin).strip()
                for origin in value
                if str(origin).strip()
            ]

        return value


settings = Settings()
