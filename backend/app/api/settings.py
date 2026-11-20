from fastapi import APIRouter
from ..integrations.status import get_sponsor_integrations_status
from ..config import settings

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/integrations")
def get_integrations():
    """Return verifiable status of sponsor integrations."""
    return get_sponsor_integrations_status()

@router.get("/status")
def get_app_status():
    """Return application configuration and environment settings."""
    return {
        "project": settings.PROJECT_NAME,
        "database_engine": "SQLite (Async aiosqlite)" if "sqlite" in settings.DATABASE_URL else "PostgreSQL (Async asyncpg)",
        "risk_limits": {
            "max_position_pct": settings.MAX_POSITION_PCT,
            "max_sector_pct": settings.MAX_SECTOR_PCT,
            "price_max_staleness_minutes": settings.PRICE_MAX_STALENESS_MINUTES,
            "max_daily_loss_pct": settings.MAX_DAILY_LOSS_PCT,
            "transaction_fee_pct": settings.TRANSACTION_FEE_PCT,
            "duplicate_proposal_window_minutes": settings.DUPLICATE_PROPOSAL_WINDOW_MINUTES,
        },
        "integrations": get_sponsor_integrations_status(),
    }
