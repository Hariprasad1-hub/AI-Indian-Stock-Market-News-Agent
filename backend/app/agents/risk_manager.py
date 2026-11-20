from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TradingDecision, Portfolio, RiskEvent
from ..risk.engine import DeterministicRiskEngine, RiskValidationResult
from .broker import AgentMessageBroker

class RiskManagerAgent:
    """Agent 4: Risk Manager Agent.
    Independently evaluates proposed trades against deterministic capital and exposure rules.
    Persists audit RiskEvents and communicates binding decisions back to Trader.
    """
    ROLE = "risk_manager"

    def __init__(self, session: AsyncSession, broker: AgentMessageBroker):
        self.session = session
        self.broker = broker
        self.risk_engine = DeterministicRiskEngine(session)

    async def evaluate_proposal(
        self,
        decision_id: int,
        portfolio: Portfolio,
        task_id: str,
        correlation_id: str,
    ) -> RiskValidationResult:
        """Validate proposed trade with deterministic Python rules and notify Trader."""
        decision = await self.session.get(TradingDecision, decision_id)
        if not decision:
            raise ValueError(f"TradingDecision {decision_id} not found.")

        # Execute deterministic risk engine
        val_result = await self.risk_engine.evaluate_trade_proposal(decision, portfolio)

        # Update decision status
        if val_result.approved:
            decision.status = "APPROVED"
            event_status = "APPROVED"
            severity = "INFO"
            description = (
                f"Trade proposal {decision.decision_type} {decision.proposed_quantity} approved. "
                f"Estimated trade amount: ₹{val_result.proposed_amount:.2f} + Fee ₹{val_result.fee:.2f}."
            )
        else:
            decision.status = "REJECTED"
            decision.rejection_reason = "; ".join(val_result.rejection_reasons)
            event_status = "REJECTED"
            severity = "CRITICAL"
            description = f"Risk Violation: {decision.rejection_reason}"

        # Persist RiskEvent in audit database
        risk_event = RiskEvent(
            decision_id=decision.id,
            event_type=",".join(val_result.rule_ids) if val_result.rule_ids else "RISK_EVALUATION",
            severity=severity,
            description=description,
            status=event_status,
            checked_at=val_result.evaluated_at,
        )
        self.session.add(risk_event)
        await self.session.commit()
        await self.session.refresh(decision)

        # Communicate binding decision back to Trader via BAND message
        feedback_payload = {
            "decision_id": decision.id,
            "status": decision.status,
            "approved": val_result.approved,
            "rejection_reasons": val_result.rejection_reasons,
            "rule_ids": val_result.rule_ids,
            "proposed_amount": float(val_result.proposed_amount),
            "fee": float(val_result.fee),
        }

        await self.broker.send_message(
            sender_role=self.ROLE,
            recipient_role="trader",
            message_type="RISK_ASSESSMENT",
            task_id=task_id,
            correlation_id=correlation_id,
            payload=feedback_payload,
        )

        return val_result
