from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import TradingDecision, Stock, Agent
from ..schemas import TradingDecisionOut, TradingDecisionBase

router = APIRouter(prefix="/decisions", tags=["decisions"])

@router.get("", response_model=List[TradingDecisionOut])
async def list_trading_decisions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    decision_type: Optional[str] = Query(None, description="Filter by BUY, SELL, HOLD, NO_ACTION"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by PENDING, APPROVED, REJECTED, EXECUTED"),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve trading decisions and their approval statuses."""
    stmt = (
        select(TradingDecision)
        .options(selectinload(TradingDecision.stock), selectinload(TradingDecision.agent))
    )

    if decision_type:
        stmt = stmt.where(TradingDecision.decision_type.ilike(decision_type))
    if status_filter:
        stmt = stmt.where(TradingDecision.status.ilike(status_filter))

    stmt = stmt.order_by(desc(TradingDecision.created_at)).offset(skip).limit(limit)
    res = await session.execute(stmt)
    decisions = res.scalars().all()

    output = []
    for d in decisions:
        output.append(
            TradingDecisionOut(
                id=d.id,
                decision_type=d.decision_type,
                stock_id=d.stock_id,
                stock_symbol=d.stock.symbol if d.stock else None,
                agent_id=d.agent_id,
                agent_name=d.agent.name if d.agent else None,
                article_id=d.article_id,
                proposed_quantity=d.proposed_quantity,
                proposed_price=d.proposed_price,
                confidence_score=d.confidence_score,
                reasoning=d.reasoning,
                evidence=d.evidence,
                status=d.status,
                created_at=d.created_at,
            )
        )
    return output

@router.post("", response_model=TradingDecisionOut, status_code=status.HTTP_201_CREATED)
async def create_trade_proposal(
    proposal_in: TradingDecisionBase,
    session: AsyncSession = Depends(get_db),
):
    """Create a new trade proposal from the Trader agent."""
    if proposal_in.stock_id:
        stock = await session.get(Stock, proposal_in.stock_id)
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")

    decision = TradingDecision(
        decision_type=proposal_in.decision_type.upper(),
        stock_id=proposal_in.stock_id,
        agent_id=proposal_in.agent_id,
        article_id=proposal_in.article_id,
        proposed_quantity=proposal_in.proposed_quantity,
        proposed_price=proposal_in.proposed_price,
        confidence_score=proposal_in.confidence_score,
        reasoning=proposal_in.reasoning,
        evidence=proposal_in.evidence,
        status="PENDING",
    )
    session.add(decision)
    await session.commit()
    await session.refresh(decision)

    stock_sym = None
    if decision.stock_id:
        stk = await session.get(Stock, decision.stock_id)
        if stk:
            stock_sym = stk.symbol

    return TradingDecisionOut(
        id=decision.id,
        decision_type=decision.decision_type,
        stock_id=decision.stock_id,
        stock_symbol=stock_sym,
        agent_id=decision.agent_id,
        article_id=decision.article_id,
        proposed_quantity=decision.proposed_quantity,
        proposed_price=decision.proposed_price,
        confidence_score=decision.confidence_score,
        reasoning=decision.reasoning,
        evidence=decision.evidence,
        status=decision.status,
        created_at=decision.created_at,
    )
