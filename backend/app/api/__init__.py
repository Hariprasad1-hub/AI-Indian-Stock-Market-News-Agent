from fastapi import APIRouter
from .dashboard import router as dashboard_router
from .news import router as news_router
from .stocks import router as stocks_router
from .agents import router as agents_router
from .decisions import router as decisions_router
from .portfolio import router as portfolio_router
from .transactions import router as transactions_router
from .risk import router as risk_router
from .settings import router as settings_router

api_router = APIRouter()

api_router.include_router(dashboard_router)
api_router.include_router(news_router)
api_router.include_router(stocks_router)
api_router.include_router(agents_router)
api_router.include_router(decisions_router)
api_router.include_router(portfolio_router)
api_router.include_router(transactions_router)
api_router.include_router(risk_router)
api_router.include_router(settings_router)

__all__ = ["api_router"]
