import os
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

# Centralized settings import
from .config import settings

class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.x models."""
    pass

# Async engine based on the shared DATABASE_URL
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    future=True,
)

# async_sessionmaker from sqlalchemy.ext.asyncio
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async DB session.
    Using async generator for proper cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
