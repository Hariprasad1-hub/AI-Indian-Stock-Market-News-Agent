from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Stock
from ..schemas import StockOut, StockCreate

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("", response_model=List[StockOut])
async def list_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve list of tracked stock instruments."""
    stmt = select(Stock)
    if symbol:
        stmt = stmt.where(Stock.symbol.ilike(f"%{symbol}%"))
    if sector:
        stmt = stmt.where(Stock.sector.ilike(f"%{sector}%"))

    stmt = stmt.order_by(Stock.symbol.asc()).offset(skip).limit(limit)
    res = await session.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=StockOut, status_code=status.HTTP_201_CREATED)
async def create_stock(
    stock_in: StockCreate,
    session: AsyncSession = Depends(get_db),
):
    """Register a new stock instrument to track."""
    existing = await session.scalar(
        select(Stock).where(Stock.symbol == stock_in.symbol.upper())
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock symbol {stock_in.symbol} already exists.",
        )

    stock = Stock(
        symbol=stock_in.symbol.upper(),
        name=stock_in.name,
        exchange=stock_in.exchange.upper(),
        sector=stock_in.sector,
        current_price=stock_in.current_price,
        is_active=stock_in.is_active,
    )
    session.add(stock)
    await session.commit()
    await session.refresh(stock)
    return stock
