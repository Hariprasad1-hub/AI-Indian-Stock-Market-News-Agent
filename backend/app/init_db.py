from decimal import Decimal
from sqlalchemy import select
from .database import AsyncSessionLocal
from .models import Portfolio, Agent
from .api.agents import CANONICAL_AGENTS

async def initialize_app_database():
    """Seed default virtual portfolio (₹1,00,000) and canonical agents once on application startup.
    This guarantees GET endpoints remain strictly read-only and idempotent.
    """
    async with AsyncSessionLocal() as session:
        # 1. Default Portfolio
        res = await session.execute(select(Portfolio).order_by(Portfolio.id.asc()).limit(1))
        if not res.scalar_one_or_none():
            portfolio = Portfolio(
                name="TRADEMIND Virtual Portfolio",
                initial_cash=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                currency="INR",
            )
            session.add(portfolio)

        # 2. Canonical Agents
        for a_data in CANONICAL_AGENTS:
            existing = await session.scalar(
                select(Agent).where(Agent.name == a_data["name"])
            )
            if not existing:
                agent = Agent(**a_data)
                session.add(agent)

        await session.commit()
