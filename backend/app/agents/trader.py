from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Stock, Portfolio, Holding, TradingDecision, Agent
from .broker import AgentMessageBroker

class TraderAgent:
    """Agent 3: Trader Agent.
    Evaluates Analyst findings against live virtual portfolio capital,
    calculates prudent position sizing, creates PENDING trade proposals,
    and submits them to the Risk Manager.
    """
    ROLE = "trader"

    def __init__(self, session: AsyncSession, broker: AgentMessageBroker):
        self.session = session
        self.broker = broker

    async def evaluate_analysis_and_propose(
        self,
        analysis: Dict[str, Any],
        portfolio: Portfolio,
        task_id: str,
        correlation_id: str,
        override_quantity: Optional[int] = None, # Used for testing unsafe proposals
    ) -> TradingDecision:
        """Create trade proposal and send to Risk Manager for validation."""
        primary_symbol = analysis.get("primary_symbol")
        sentiment = analysis.get("sentiment", "NEUTRAL")
        confidence = Decimal(str(analysis.get("confidence_score", 0.5)))
        article_id = analysis.get("article_id")

        trader_agent = await self.session.scalar(
            select(Agent).where(Agent.role == self.ROLE)
        )
        agent_id = trader_agent.id if trader_agent else None

        if not primary_symbol:
            decision = TradingDecision(
                decision_type="NO_ACTION",
                agent_id=agent_id,
                article_id=article_id,
                confidence_score=confidence,
                reasoning="No recognized Indian equity ticker identified in news.",
                status="NO_ACTION",
            )
            self.session.add(decision)
            await self.session.commit()
            return decision

        # Fetch or verify stock instrument
        stock = await self.session.scalar(
            select(Stock).where(Stock.symbol == primary_symbol)
        )
        if not stock:
            # Create a tracked stock record with default price if missing
            stock = Stock(
                symbol=primary_symbol,
                name=f"{primary_symbol} Ltd",
                exchange="NSE",
                current_price=Decimal("1500.00"),
                price_status="LIVE",
            )
            self.session.add(stock)
            await self.session.commit()
            await self.session.refresh(stock)

        # Inspect current holding
        holding = await self.session.scalar(
            select(Holding).where(
                and_(
                    Holding.portfolio_id == portfolio.id,
                    Holding.stock_id == stock.id,
                )
            )
        )
        held_qty = holding.quantity if holding else 0

        decision_type = "HOLD"
        proposed_qty = 0
        reasoning = ""

        if sentiment == "BULLISH" and confidence >= Decimal("0.60"):
            decision_type = "BUY"
            if override_quantity is not None:
                proposed_qty = override_quantity
                reasoning = f"Test proposal: BUY {override_quantity} shares of {stock.symbol}."
            else:
                # Prudent position sizing: target 10% of available cash
                target_allocation = portfolio.cash_balance * Decimal("0.10")
                if stock.current_price and stock.current_price > Decimal("0.00"):
                    calc_qty = int(target_allocation / stock.current_price)
                    proposed_qty = max(calc_qty, 1)
                else:
                    proposed_qty = 1
                reasoning = (
                    f"Strong bullish catalyst identified for {stock.symbol} (Confidence: {confidence}). "
                    f"Allocating 10% of cash for {proposed_qty} shares."
                )

        elif sentiment == "BEARISH":
            if held_qty > 0:
                decision_type = "SELL"
                proposed_qty = override_quantity if override_quantity is not None else held_qty
                reasoning = f"Bearish signals detected for {stock.symbol}. Liquidating {proposed_qty} held shares."
            else:
                decision_type = "NO_ACTION"
                proposed_qty = 0
                reasoning = f"Bearish signal for {stock.symbol}, but stock is not in portfolio. Short-selling prohibited."

        else:
            decision_type = "NO_ACTION"
            proposed_qty = 0
            reasoning = f"Neutral market signals for {stock.symbol}. No trade recommended."

        decision = TradingDecision(
            decision_type=decision_type,
            stock_id=stock.id,
            agent_id=agent_id,
            article_id=article_id,
            proposed_quantity=proposed_qty,
            proposed_price=stock.current_price,
            confidence_score=confidence,
            reasoning=reasoning,
            evidence=str(analysis.get("evidence", "")),
            status="PENDING" if decision_type in ("BUY", "SELL") else "NO_ACTION",
        )
        self.session.add(decision)
        await self.session.commit()
        await self.session.refresh(decision)

        # If trade proposed, dispatch structured message to Risk Manager
        if decision.decision_type in ("BUY", "SELL"):
            proposal_payload = {
                "decision_id": decision.id,
                "decision_type": decision.decision_type,
                "stock_symbol": stock.symbol,
                "stock_id": stock.id,
                "proposed_quantity": decision.proposed_quantity,
                "proposed_price": float(decision.proposed_price) if decision.proposed_price else 0.0,
                "confidence": float(confidence),
                "reasoning": decision.reasoning,
            }
            await self.broker.send_message(
                sender_role=self.ROLE,
                recipient_role="risk_manager",
                message_type="TRADE_PROPOSAL",
                task_id=task_id,
                correlation_id=correlation_id,
                payload=proposal_payload,
            )

        return decision

    async def handle_risk_feedback(
        self,
        feedback: Dict[str, Any],
        task_id: str,
        correlation_id: str,
    ):
        """Record and acknowledge feedback from Risk Manager."""
        decision_id = feedback.get("decision_id")
        if decision_id:
            decision = await self.session.get(TradingDecision, decision_id)
            if decision and feedback.get("status") == "REJECTED":
                # Feedback acknowledged and logged
                decision.rejection_reason = "; ".join(feedback.get("rejection_reasons", []))
                await self.session.commit()
