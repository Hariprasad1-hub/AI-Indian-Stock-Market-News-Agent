from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..models import Stock, Portfolio, Holding, TradingDecision, TradeTransaction

@dataclass
class RiskValidationResult:
    """Structured deterministic risk evaluation result."""
    approved: bool
    rejection_reasons: List[str] = field(default_factory=list)
    rule_ids: List[str] = field(default_factory=list)
    evaluated_price: Optional[Decimal] = None
    proposed_amount: Decimal = Decimal("0.00")
    fee: Decimal = Decimal("0.00")
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class DeterministicRiskEngine:
    """Deterministic financial risk validation engine.
    Final authority for financial safety – AI agents cannot override or bypass these rules.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def evaluate_trade_proposal(
        self,
        decision: TradingDecision,
        portfolio: Portfolio,
    ) -> RiskValidationResult:
        """Run all deterministic risk rules against proposed trade decision."""
        reasons: List[str] = []
        rule_ids: List[str] = []
        now = datetime.now(timezone.utc)

        # 1. Decision Type Validation
        if decision.decision_type not in ("BUY", "SELL"):
            return RiskValidationResult(
                approved=False,
                rejection_reasons=[f"Invalid or non-executable decision type: {decision.decision_type}"],
                rule_ids=["RULE_TYPE_UNEXECUTABLE"],
                evaluated_at=now,
            )

        if decision.proposed_quantity <= 0:
            return RiskValidationResult(
                approved=False,
                rejection_reasons=["Proposed quantity must be strictly greater than 0."],
                rule_ids=["RULE_QUANTITY_INVALID"],
                evaluated_at=now,
            )

        # 2. Stock & Market Price Validation
        if not decision.stock_id:
            return RiskValidationResult(
                approved=False,
                rejection_reasons=["Trade proposal must specify a target stock instrument."],
                rule_ids=["RULE_STOCK_MISSING"],
                evaluated_at=now,
            )

        stock = await self.session.get(Stock, decision.stock_id)
        if not stock:
            return RiskValidationResult(
                approved=False,
                rejection_reasons=[f"Stock ID {decision.stock_id} does not exist."],
                rule_ids=["RULE_STOCK_NOT_FOUND"],
                evaluated_at=now,
            )

        # Rule 5 & 6: Price Status and Freshness
        if stock.price_status == "UNAVAILABLE" or stock.current_price is None or stock.current_price <= Decimal("0.00"):
            return RiskValidationResult(
                approved=False,
                rejection_reasons=[f"Market quote for {stock.symbol} is unavailable."],
                rule_ids=["RULE_PRICE_UNAVAILABLE"],
                evaluated_at=now,
            )

        if stock.price_updated_at:
            staleness_cutoff = now - timedelta(minutes=settings.PRICE_MAX_STALENESS_MINUTES)
            if stock.price_updated_at < staleness_cutoff:
                return RiskValidationResult(
                    approved=False,
                    rejection_reasons=[
                        f"Market quote for {stock.symbol} is stale (> {settings.PRICE_MAX_STALENESS_MINUTES} minutes old)."
                    ],
                    rule_ids=["RULE_PRICE_STALE"],
                    evaluated_price=stock.current_price,
                    evaluated_at=now,
                )

        eval_price = stock.current_price
        proposed_amount = Decimal(decision.proposed_quantity) * eval_price
        fee = proposed_amount * Decimal(str(settings.TRANSACTION_FEE_PCT))
        total_buy_required = proposed_amount + fee

        # 3. Rule 7: Duplicate Proposal Prevention (5-minute correlation window)
        dup_cutoff = now - timedelta(minutes=settings.DUPLICATE_PROPOSAL_WINDOW_MINUTES)
        recent_dup = await self.session.scalar(
            select(TradingDecision).where(
                and_(
                    TradingDecision.id != decision.id,
                    TradingDecision.stock_id == stock.id,
                    TradingDecision.decision_type == decision.decision_type,
                    TradingDecision.created_at >= dup_cutoff,
                    TradingDecision.status.in_(["PENDING", "APPROVED"]),
                )
            )
        )
        if recent_dup:
            reasons.append(
                f"Duplicate proposal for {stock.symbol} detected within {settings.DUPLICATE_PROPOSAL_WINDOW_MINUTES} minutes."
            )
            rule_ids.append("RULE_DUPLICATE_PROPOSAL")

        # 4. Fetch Portfolio Holdings & Total Valuation
        holdings_res = await self.session.execute(
            select(Holding)
            .where(Holding.portfolio_id == portfolio.id)
            .options(selectinload(Holding.stock))
        )
        holdings = holdings_res.scalars().all()

        current_invested = Decimal("0.00")
        stock_holding_val = Decimal("0.00")
        stock_holding_qty = 0
        sector_holding_val = Decimal("0.00")

        for h in holdings:
            h_price = h.current_price if (h.stock and h.stock.price_status != "UNAVAILABLE" and h.current_price > 0) else h.average_buy_price
            val = Decimal(h.quantity) * h_price
            current_invested += val

            if h.stock_id == stock.id:
                stock_holding_val += val
                stock_holding_qty += h.quantity

            if h.stock and stock.sector and h.stock.sector and (h.stock.sector.lower() == stock.sector.lower()):
                sector_holding_val += val

        total_portfolio_value = portfolio.cash_balance + current_invested

        # 5. Rule 8: Daily Loss Protection (Max 5% drop against initial cash)
        max_daily_loss = portfolio.initial_cash * Decimal(str(settings.MAX_DAILY_LOSS_PCT))
        current_loss = portfolio.initial_cash - total_portfolio_value
        if current_loss > max_daily_loss and decision.decision_type == "BUY":
            reasons.append(
                f"Daily loss limit reached (Current loss: ₹{current_loss:.2f} > Max allowed: ₹{max_daily_loss:.2f}). New purchases halted."
            )
            rule_ids.append("RULE_DAILY_LOSS_EXCEEDED")

        # 6. Specific Rules for BUY Orders
        if decision.decision_type == "BUY":
            # Rule 1 & 9: Available Cash and Fee Sufficiency
            if total_buy_required > portfolio.cash_balance:
                reasons.append(
                    f"Insufficient funds: Required ₹{total_buy_required:.2f} (Trade: ₹{proposed_amount:.2f} + Fee: ₹{fee:.2f}), Available: ₹{portfolio.cash_balance:.2f}."
                )
                rule_ids.append("RULE_INSUFFICIENT_FUNDS")

            # Rule 2: Single Stock Exposure Limit (Max 20%)
            max_position_limit = total_portfolio_value * Decimal(str(settings.MAX_POSITION_PCT))
            projected_stock_val = stock_holding_val + proposed_amount
            if projected_stock_val > max_position_limit:
                reasons.append(
                    f"Position concentration limit exceeded: Projected ₹{projected_stock_val:.2f} exceeds 20% limit (₹{max_position_limit:.2f})."
                )
                rule_ids.append("RULE_POSITION_LIMIT_EXCEEDED")

            # Rule 3: Sector Exposure Limit (Max 35%)
            if stock.sector:
                max_sector_limit = total_portfolio_value * Decimal(str(settings.MAX_SECTOR_PCT))
                projected_sector_val = sector_holding_val + proposed_amount
                if projected_sector_val > max_sector_limit:
                    reasons.append(
                        f"Sector exposure limit exceeded for '{stock.sector}': Projected ₹{projected_sector_val:.2f} exceeds 35% limit (₹{max_sector_limit:.2f})."
                    )
                    rule_ids.append("RULE_SECTOR_LIMIT_EXCEEDED")

        # 7. Specific Rules for SELL Orders
        elif decision.decision_type == "SELL":
            # Rule 4: No Short Selling
            if decision.proposed_quantity > stock_holding_qty:
                reasons.append(
                    f"Short selling prohibited: Attempting to sell {decision.proposed_quantity} shares of {stock.symbol}, but only {stock_holding_qty} are held."
                )
                rule_ids.append("RULE_INSUFFICIENT_HOLDINGS")

        approved = len(reasons) == 0
        return RiskValidationResult(
            approved=approved,
            rejection_reasons=reasons,
            rule_ids=rule_ids,
            evaluated_price=eval_price,
            proposed_amount=proposed_amount,
            fee=fee,
            evaluated_at=now,
        )
