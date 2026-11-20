import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Agent, AgentMessage
from ..schemas import AgentOut, AgentMessageOut, AgentMessageBase

router = APIRouter(prefix="/agents", tags=["agents"])

CANONICAL_AGENTS = [
    {
        "name": "Market Intelligence Agent",
        "role": "market_intelligence",
        "status": "IDLE",
        "description": "Monitors regulatory filings (BSE) and news (ET), normalizes articles, and extracts symbols.",
        "capabilities": "RSS Ingestion, Entity Normalization, Deduplication",
    },
    {
        "name": "Market Analyst Agent",
        "role": "market_analyst",
        "status": "IDLE",
        "description": "Performs sentiment analysis, evaluates evidence, estimates market impact, and scores confidence.",
        "capabilities": "Sentiment Scoring, Impact Estimation, Risk Categorization",
    },
    {
        "name": "Trader Agent",
        "role": "trader",
        "status": "IDLE",
        "description": "Evaluates findings against portfolio capital, determines BUY/SELL/HOLD, and generates trade proposals.",
        "capabilities": "Position Planning, Opportunity Assessment, Proposal Generation",
    },
    {
        "name": "Risk Manager Agent",
        "role": "risk_manager",
        "status": "IDLE",
        "description": "Validates proposed trades against cash, concentration, and position limits with deterministic rules.",
        "capabilities": "Deterministic Rule Validation, Capital Guardrails, Compliance Enforcement",
    },
]

@router.get("", response_model=List[AgentOut])
async def list_agents(session: AsyncSession = Depends(get_db)):
    """Return the four independent agent profiles and execution status (strictly read-only)."""
    stmt = select(Agent).order_by(Agent.id.asc())
    res = await session.execute(stmt)
    agents = res.scalars().all()
    if not agents:
        # Transient in-memory representation if DB was not yet seeded
        return [
            AgentOut(
                id=idx + 1,
                name=a["name"],
                role=a["role"],
                status=a["status"],
                description=a["description"],
                capabilities=a["capabilities"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for idx, a in enumerate(CANONICAL_AGENTS)
        ]
    return agents

@router.get("/messages", response_model=List[AgentMessageOut])
async def list_agent_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve persisted agent communication messages (strictly read-only)."""
    stmt = (
        select(AgentMessage)
        .options(selectinload(AgentMessage.sender), selectinload(AgentMessage.recipient))
    )

    if task_id:
        stmt = stmt.where(AgentMessage.task_id == task_id)
    if correlation_id:
        stmt = stmt.where(AgentMessage.correlation_id == correlation_id)
    if message_type:
        stmt = stmt.where(AgentMessage.message_type == message_type)

    stmt = stmt.order_by(desc(AgentMessage.timestamp)).offset(skip).limit(limit)
    res = await session.execute(stmt)
    messages = res.scalars().all()

    output = []
    for m in messages:
        output.append(
            AgentMessageOut(
                id=m.id,
                message_id=m.message_id,
                sender_id=m.sender_id,
                recipient_id=m.recipient_id,
                sender_name=m.sender.name if m.sender else None,
                recipient_name=m.recipient.name if m.recipient else None,
                message_type=m.message_type,
                task_id=m.task_id,
                correlation_id=m.correlation_id,
                payload=m.payload,
                status=m.status,
                error_message=m.error_message,
                timestamp=m.timestamp,
            )
        )
    return output

@router.post("/messages", response_model=AgentMessageOut, status_code=status.HTTP_201_CREATED)
async def post_agent_message(
    msg_in: AgentMessageBase,
    session: AsyncSession = Depends(get_db),
):
    """Record an agent-to-agent collaboration message."""
    sender = await session.get(Agent, msg_in.sender_id)
    recipient = await session.get(Agent, msg_in.recipient_id)
    if not sender or not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender or recipient agent does not exist.",
        )

    msg = AgentMessage(
        message_id=str(uuid.uuid4()),
        sender_id=msg_in.sender_id,
        recipient_id=msg_in.recipient_id,
        message_type=msg_in.message_type,
        task_id=msg_in.task_id,
        correlation_id=msg_in.correlation_id,
        payload=msg_in.payload,
        status="DELIVERED",
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)

    return AgentMessageOut(
        id=msg.id,
        message_id=msg.message_id,
        sender_id=msg.sender_id,
        recipient_id=msg.recipient_id,
        sender_name=sender.name,
        recipient_name=recipient.name,
        message_type=msg.message_type,
        task_id=msg.task_id,
        correlation_id=msg.correlation_id,
        payload=msg.payload,
        status=msg.status,
        error_message=msg.error_message,
        timestamp=msg.timestamp,
    )
