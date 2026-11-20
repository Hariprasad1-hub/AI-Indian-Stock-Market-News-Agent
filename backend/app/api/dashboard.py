from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import (
    Portfolio,
    Holding,
    TradeTransaction,
    Agent,
    NewsArticle,
    TradingDecision,
    RiskEvent,
)
from ..schemas import DashboardSummaryOut, ActivityItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

async def get_default_portfolio(session: AsyncSession) -> Portfolio:
    """Read default virtual portfolio without mutating the database."""
    stmt = select(Portfolio).order_by(Portfolio.id.asc()).limit(1)
    res = await session.execute(stmt)
    portfolio = res.scalar_one_or_none()
    if not portfolio:
        # Return read-only transient object without modifying database
        return Portfolio(
            id=0,
            name="TRADEMIND Virtual Portfolio",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            currency="INR",
        )
    return portfolio

@router.get("/summary", response_model=DashboardSummaryOut)
async def get_dashboard_summary(session: AsyncSession = Depends(get_db)):
    """Return live aggregated metrics for the dashboard summary cards (strictly read-only)."""
    portfolio = await get_default_portfolio(session)

    # Fetch holdings with stock details to calculate current value and unrealized P&L
    holdings_stmt = (
        select(Holding)
        .where(Holding.portfolio_id == portfolio.id)
        .options(selectinload(Holding.stock))
    )
    holdings_res = await session.execute(holdings_stmt)
    holdings = holdings_res.scalars().all()

    invested_value = Decimal("0.00")
    total_unrealized_pnl = Decimal("0.00")
    total_realized_pnl = Decimal("0.00")

    for h in holdings:
        cost = Decimal(h.quantity) * h.average_buy_price
        # Explicit price status check
        effective_price = h.current_price if (h.stock and h.stock.price_status != "UNAVAILABLE" and h.current_price > 0) else h.average_buy_price
        curr_val = Decimal(h.quantity) * effective_price
        invested_value += curr_val
        total_unrealized_pnl += (curr_val - cost)
        total_realized_pnl += h.realized_pnl

    total_portfolio_value = portfolio.cash_balance + invested_value

    # Aggregate counts
    trades_count = await session.scalar(
        select(func.count(TradeTransaction.id)).where(TradeTransaction.portfolio_id == portfolio.id)
    ) or 0

    active_agents = await session.scalar(
        select(func.count(Agent.id)).where(Agent.status != "OFFLINE")
    ) or 0

    total_news = await session.scalar(select(func.count(NewsArticle.id))) or 0

    pending_decisions = await session.scalar(
        select(func.count(TradingDecision.id)).where(TradingDecision.status == "PENDING")
    ) or 0

    # Build recent activity feed
    activity_items: List[ActivityItem] = []

    # Recent transactions
    recent_trades_stmt = (
        select(TradeTransaction)
        .where(TradeTransaction.portfolio_id == portfolio.id)
        .options(selectinload(TradeTransaction.stock))
        .order_by(desc(TradeTransaction.executed_at))
        .limit(5)
    )
    recent_trades = (await session.execute(recent_trades_stmt)).scalars().all()
    for t in recent_trades:
        sym = t.stock.symbol if t.stock else "STOCK"
        activity_items.append(
            ActivityItem(
                type="TRANSACTION",
                id=t.id,
                title=f"{t.transaction_type} {t.quantity} shares of {sym}",
                description=f"Executed at ₹{t.execution_price} (Total: ₹{t.total_amount})",
                status="EXECUTED",
                timestamp=t.executed_at,
            )
        )

    # Recent decisions
    recent_decisions_stmt = (
        select(TradingDecision)
        .options(selectinload(TradingDecision.stock))
        .order_by(desc(TradingDecision.created_at))
        .limit(5)
    )
    recent_decisions = (await session.execute(recent_decisions_stmt)).scalars().all()
    for d in recent_decisions:
        sym = d.stock.symbol if d.stock else "MARKET"
        activity_items.append(
            ActivityItem(
                type="DECISION",
                id=d.id,
                title=f"Trade Proposal: {d.decision_type} {sym}",
                description=d.reasoning or f"Confidence: {d.confidence_score}",
                status=d.status,
                timestamp=d.created_at,
            )
        )

    # Sort combined activity by timestamp descending
    activity_items.sort(key=lambda x: x.timestamp, reverse=True)
    activity_items = activity_items[:10]

    return DashboardSummaryOut(
        portfolio_value=total_portfolio_value,
        available_cash=portfolio.cash_balance,
        invested_value=invested_value,
        total_realized_pnl=total_realized_pnl,
        total_unrealized_pnl=total_unrealized_pnl,
        total_trades=trades_count,
        active_agents_count=active_agents,
        total_news_count=total_news,
        pending_decisions_count=pending_decisions,
        recent_activity=activity_items,
    )
