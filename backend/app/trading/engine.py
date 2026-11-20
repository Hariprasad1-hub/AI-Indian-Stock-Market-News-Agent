from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import Portfolio, Holding, TradeTransaction, TradingDecision, Stock

class PaperTradingEngine:
    """Simulated Paper-Trading Execution Engine.
    Executes approved trades atomically and calculates weighted average entry prices,
    cash deductions, realized P&L, and transaction fees.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_approved_trade(
        self,
        decision_id: int,
        portfolio_id: int,
    ) -> TradeTransaction:
        """Atomically execute an approved trade decision."""
        # 1. Fetch Decision and verify approval status
        decision = await self.session.get(TradingDecision, decision_id)
        if not decision:
            raise ValueError(f"Trading decision ID {decision_id} not found.")

        # Idempotency check: A decision must never be executed twice
        if decision.status == "EXECUTED":
            existing_tx = await self.session.scalar(
                select(TradeTransaction).where(TradeTransaction.decision_id == decision.id)
            )
            if existing_tx:
                return existing_tx
            raise ValueError(f"Decision {decision_id} is already marked EXECUTED.")

        if decision.status != "APPROVED":
            raise ValueError(
                f"Cannot execute unapproved trade. Decision status is '{decision.status}' (Must be 'APPROVED')."
            )

        if decision.decision_type not in ("BUY", "SELL"):
            raise ValueError(
                f"Cannot execute decision type '{decision.decision_type}'. Only BUY and SELL are executable."
            )

        # 2. Fetch Portfolio and Stock
        portfolio = await self.session.get(Portfolio, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio ID {portfolio_id} not found.")

        stock = await self.session.get(Stock, decision.stock_id)
        if not stock:
            raise ValueError(f"Stock ID {decision.stock_id} not found.")

        if stock.current_price is None or stock.current_price <= Decimal("0.00"):
            raise ValueError(f"Execution failed: Market price for {stock.symbol} is unavailable.")

        exec_price = stock.current_price
        quantity = decision.proposed_quantity
        total_amount = Decimal(quantity) * exec_price
        fee = total_amount * Decimal(str(settings.TRANSACTION_FEE_PCT))
        now = datetime.now(timezone.utc)

        # 3. Retrieve or create Holding record
        holding = await self.session.scalar(
            select(Holding).where(
                and_(
                    Holding.portfolio_id == portfolio.id,
                    Holding.stock_id == stock.id,
                )
            )
        )

        # 4. Execute BUY logic
        if decision.decision_type == "BUY":
            total_cost = total_amount + fee
            if total_cost > portfolio.cash_balance:
                raise ValueError(
                    f"Execution failed: Insufficient cash balance (Required ₹{total_cost:.2f}, Available: ₹{portfolio.cash_balance:.2f})."
                )

            # Deduct cash
            portfolio.cash_balance -= total_cost

            if not holding:
                holding = Holding(
                    portfolio_id=portfolio.id,
                    stock_id=stock.id,
                    quantity=quantity,
                    average_buy_price=exec_price,
                    current_price=exec_price,
                    realized_pnl=Decimal("0.00"),
                    updated_at=now,
                )
                self.session.add(holding)
            else:
                # Weighted average entry price calculation
                current_total_cost = Decimal(holding.quantity) * holding.average_buy_price
                new_total_cost = current_total_cost + total_amount
                new_qty = holding.quantity + quantity
                holding.average_buy_price = new_total_cost / Decimal(new_qty)
                holding.quantity = new_qty
                holding.current_price = exec_price
                holding.updated_at = now

        # 5. Execute SELL logic
        elif decision.decision_type == "SELL":
            if not holding or holding.quantity < quantity:
                held = holding.quantity if holding else 0
                raise ValueError(
                    f"Execution failed: Insufficient holdings to sell (Attempted: {quantity}, Held: {held})."
                )

            net_proceeds = total_amount - fee
            # Add proceeds to cash balance
            portfolio.cash_balance += net_proceeds

            # Calculate realized P&L
            cost_basis = Decimal(quantity) * holding.average_buy_price
            realized_pnl = total_amount - cost_basis - fee
            holding.realized_pnl += realized_pnl
            holding.quantity -= quantity
            holding.current_price = exec_price
            holding.updated_at = now

        # 6. Record Immutable Trade Transaction
        tx = TradeTransaction(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            decision_id=decision.id,
            transaction_type=decision.decision_type,
            quantity=quantity,
            execution_price=exec_price,
            total_amount=total_amount,
            fee=fee,
            executed_at=now,
        )
        self.session.add(tx)

        # 7. Update Decision status to EXECUTED
        decision.status = "EXECUTED"

        # Commit atomically with safe rollback on failure
        try:
            await self.session.commit()
            await self.session.refresh(tx)
            await self.session.refresh(portfolio)
            return tx
        except Exception as exc:
            await self.session.rollback()
            # Check if concurrent execution already succeeded
            existing_tx = await self.session.scalar(
                select(TradeTransaction).where(TradeTransaction.decision_id == decision.id)
            )
            if existing_tx:
                return existing_tx
            raise exc
