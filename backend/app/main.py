import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Centralized settings import – uses the shared Settings in config.py
from .config import settings
from .api import api_router
from .init_db import initialize_app_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan: seeds initial database records once on startup."""
    try:
        await initialize_app_database()
    except Exception as exc:
        print(f"Warning: Database initialization during startup: {exc}")
    yield
    # Cleanup on shutdown if needed

# ----------------------------------------------------------------------
# FastAPI application
# ----------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-agent financial intelligence and paper trading platform for Indian stock markets.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – origins can be overridden via ALLOWED_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------
# Health endpoint (includes DB ping)
# ----------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    """Return health status and database connectivity.

    - "ok"  – FastAPI is running and a DB ping succeeded.
    - "degraded" – FastAPI is running but DB ping failed.
    """
    db_ok = False
    try:
        from .database import get_db
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            db_ok = True
            break
    except Exception as exc:
        print(f"Database health check failed: {exc}")

    return {
        "status": "ok" if db_ok else "degraded",
        "project": settings.PROJECT_NAME,
        "db_connected": db_ok,
    }

# ----------------------------------------------------------------------
# API Routers mounted under prefix /api
# ----------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)
