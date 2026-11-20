from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import TradeTransaction, Stock
from ..schemas import TradeTransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("", response_model=List[TradeTransactionOut])
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    transaction_type: Optional[str] = Query(None, description="Filter by BUY or SELL"),
    session: AsyncSession = Depends(get_db),
):
    """Return paper-trading transaction history."""
    stmt = (
        select(TradeTransaction)
        .options(selectinload(TradeTransaction.stock))
    )

    if transaction_type:
        stmt = stmt.where(TradeTransaction.transaction_type.ilike(transaction_type))

    stmt = stmt.order_by(desc(TradeTransaction.executed_at)).offset(skip).limit(limit)
    res = await session.execute(stmt)
    txs = res.scalars().all()

    output = []
    for t in txs:
        output.append(
            TradeTransactionOut(
                id=t.id,
                portfolio_id=t.portfolio_id,
                stock_id=t.stock_id,
                stock_symbol=t.stock.symbol if t.stock else "UNKNOWN",
                decision_id=t.decision_id,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                execution_price=t.execution_price,
                total_amount=t.total_amount,
                fee=t.fee,
                executed_at=t.executed_at,
            )
        )
    return output
