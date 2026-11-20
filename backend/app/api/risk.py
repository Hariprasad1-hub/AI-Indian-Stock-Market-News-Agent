from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import RiskEvent
from ..schemas import RiskEventOut

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/events", response_model=List[RiskEventOut])
async def list_risk_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by APPROVED, REJECTED, FLAGGED"),
    severity: Optional[str] = Query(None, description="Filter by INFO, WARNING, CRITICAL, BLOCKED"),
    session: AsyncSession = Depends(get_db),
):
    """Return risk management events and audit checks."""
    stmt = select(RiskEvent)

    if status_filter:
        stmt = stmt.where(RiskEvent.status.ilike(status_filter))
    if severity:
        stmt = stmt.where(RiskEvent.severity.ilike(severity))

    stmt = stmt.order_by(desc(RiskEvent.checked_at)).offset(skip).limit(limit)
    res = await session.execute(stmt)
    return res.scalars().all()
