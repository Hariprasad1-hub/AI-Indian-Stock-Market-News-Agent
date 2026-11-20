import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Compute repository root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_PATH = (PROJECT_ROOT / "trademind.db").as_posix()
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"

class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""
    PROJECT_NAME: str = "TRADEMIND AI"
    API_V1_STR: str = "/api"
    # Use async driver URLs. SQLite uses aiosqlite; PostgreSQL uses asyncpg.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        DEFAULT_DB_URL,
    )
    # CORS origins – configurable via ALLOWED_ORIGINS env var (comma-separated)
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]

    # Webhook Secret for n8n integration
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "trademind-n8n-secret-key-2026")

    # Risk Management Engine Parameters
    MAX_POSITION_PCT: float = 0.20 # Max 20% portfolio value in single stock
    MAX_SECTOR_PCT: float = 0.35   # Max 35% portfolio value in single sector
    PRICE_MAX_STALENESS_MINUTES: int = 15 # Reject quotes older than 15 mins
    MAX_DAILY_LOSS_PCT: float = 0.05 # Max 5% daily loss protection
    TRANSACTION_FEE_PCT: float = 0.001 # 0.1% transaction fee
    DUPLICATE_PROPOSAL_WINDOW_MINUTES: int = 5 # 5-min correlation deduplication

    # Optional Sponsor Platform API Keys (None = unconfigured/not connected)
    BAND_API_KEY: Optional[str] = os.getenv("BAND_API_KEY", None)
    LYZR_API_KEY: Optional[str] = os.getenv("LYZR_API_KEY", None)
    FINCH_API_KEY: Optional[str] = os.getenv("FINCH_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
