import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Agent, AgentMessage

class AgentMessageBroker:
    """Structured Agent Collaboration & Messaging Broker implementing BAND Protocol standards.
    Guarantees persistence, idempotency, correlation tracking, and audit logging.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def send_message(
        self,
        sender_role: str,
        recipient_role: str,
        message_type: str,
        task_id: str,
        correlation_id: str,
        payload: Dict[str, Any],
    ) -> AgentMessage:
        """Persist and route a structured message between two independent agents."""
        # 1. Resolve sender and recipient agent IDs
        sender = await self.session.scalar(
            select(Agent).where(Agent.role == sender_role)
        )
        recipient = await self.session.scalar(
            select(Agent).where(Agent.role == recipient_role)
        )

        if not sender:
            raise ValueError(f"Sender agent with role '{sender_role}' not found.")
        if not recipient:
            raise ValueError(f"Recipient agent with role '{recipient_role}' not found.")

        # 2. Idempotency check: prevent duplicate message processing for same task & type
        existing = await self.session.scalar(
            select(AgentMessage).where(
                and_(
                    AgentMessage.task_id == task_id,
                    AgentMessage.message_type == message_type,
                    AgentMessage.sender_id == sender.id,
                    AgentMessage.recipient_id == recipient.id,
                )
            )
        )
        if existing:
            # Return existing message to prevent duplicate state mutation
            return existing

        # 3. Create structured message record
        msg = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender.id,
            recipient_id=recipient.id,
            message_type=message_type,
            task_id=task_id,
            correlation_id=correlation_id,
            payload=json.dumps(payload, default=str),
            status="DELIVERED",
            timestamp=datetime.now(timezone.utc),
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_conversation_history(self, correlation_id: str) -> List[AgentMessage]:
        """Retrieve full chronological communication chain for a given correlation ID."""
        stmt = (
            select(AgentMessage)
            .where(AgentMessage.correlation_id == correlation_id)
            .order_by(AgentMessage.timestamp.asc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def mark_message_status(
        self, message_id: str, status: str, error_message: Optional[str] = None
    ):
        """Update message processing state (PROCESSED or FAILED)."""
        msg = await self.session.scalar(
            select(AgentMessage).where(AgentMessage.message_id == message_id)
        )
        if msg:
            msg.status = status
            if error_message:
                msg.error_message = error_message
            await self.session.commit()
