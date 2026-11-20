from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Portfolio, Holding
from ..schemas import PortfolioOut, HoldingOut
from .dashboard import get_default_portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("", response_model=PortfolioOut)
async def get_portfolio(session: AsyncSession = Depends(get_db)):
    """Return cash balance, holdings, portfolio value and P&L for virtual trading (read-only)."""
    portfolio = await get_default_portfolio(session)

    stmt = (
        select(Holding)
        .where(Holding.portfolio_id == portfolio.id)
        .options(selectinload(Holding.stock))
        .order_by(Holding.id.asc())
    )
    res = await session.execute(stmt)
    holdings = res.scalars().all()

    invested_value = Decimal("0.00")
    total_unrealized_pnl = Decimal("0.00")
    total_realized_pnl = Decimal("0.00")
    holdings_out: List[HoldingOut] = []

    for h in holdings:
        cost = Decimal(h.quantity) * h.average_buy_price
        effective_price = h.current_price if (h.stock and h.stock.price_status != "UNAVAILABLE" and h.current_price > 0) else h.average_buy_price
        curr_val = Decimal(h.quantity) * effective_price
        unrealized = curr_val - cost

        invested_value += curr_val
        total_unrealized_pnl += unrealized
        total_realized_pnl += h.realized_pnl

        holdings_out.append(
            HoldingOut(
                id=h.id,
                portfolio_id=h.portfolio_id,
                stock_id=h.stock_id,
                stock_symbol=h.stock.symbol if h.stock else "UNKNOWN",
                quantity=h.quantity,
                average_buy_price=h.average_buy_price,
                current_price=effective_price,
                invested_amount=cost,
                current_value=curr_val,
                unrealized_pnl=unrealized,
                realized_pnl=h.realized_pnl,
                updated_at=h.updated_at,
            )
        )

    total_portfolio_value = portfolio.cash_balance + invested_value

    return PortfolioOut(
        id=portfolio.id,
        name=portfolio.name,
        initial_cash=portfolio.initial_cash,
        cash_balance=portfolio.cash_balance,
        invested_value=invested_value,
        total_portfolio_value=total_portfolio_value,
        unrealized_pnl=total_unrealized_pnl,
        realized_pnl=total_realized_pnl,
        currency=portfolio.currency,
        holdings_count=len(holdings_out),
        holdings=holdings_out,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )
