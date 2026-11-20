import uuid
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from backend.app.database import AsyncSessionLocal, engine, Base
from backend.app.models import (
    NewsArticle,
    Stock,
    Agent,
    AgentMessage,
    TradingDecision,
    Portfolio,
    Holding,
    TradeTransaction,
    RiskEvent,
)

@pytest.mark.asyncio
async def test_table_creation():
    """Verify all 9 tables exist in database metadata."""
    expected_tables = {
        "news_articles",
        "stocks",
        "agents",
        "agent_messages",
        "trading_decisions",
        "portfolios",
        "holdings",
        "trade_transactions",
        "risk_events",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"

@pytest.mark.asyncio
async def test_portfolio_initialization_and_financial_precision():
    """Test Decimal financial precision and cash balances (no floating-point drift)."""
    async with AsyncSessionLocal() as session:
        uid = uuid.uuid4().hex[:6]
        # Create virtual portfolio with 1,00,000 INR
        portfolio = Portfolio(
            name=f"Portfolio_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            currency="INR",
        )
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)

        assert portfolio.id is not None
        assert isinstance(portfolio.cash_balance, Decimal)
        assert portfolio.cash_balance == Decimal("100000.00")

        # Simulate purchasing 20 shares of Reliance at 2543.75 INR
        buy_qty = 20
        buy_price = Decimal("2543.75")
        trade_amount = Decimal(buy_qty) * buy_price # Exactly 50875.00
        assert trade_amount == Decimal("50875.00")

        portfolio.cash_balance -= trade_amount
        await session.commit()
        await session.refresh(portfolio)

        assert portfolio.cash_balance == Decimal("49125.00")

@pytest.mark.asyncio
async def test_stock_and_holding_relationship():
    """Verify Stock and Holding relational integrity."""
    async with AsyncSessionLocal() as session:
        uid = uuid.uuid4().hex[:6]
        # Create stock with unique symbol
        stock = Stock(
            symbol=f"TCS_{uid}",
            name="Tata Consultancy Services",
            exchange="NSE",
            sector="IT",
            current_price=Decimal("3850.50"),
        )
        session.add(stock)
        await session.commit()
        await session.refresh(stock)

        # Create portfolio
        portfolio = Portfolio(
            name=f"Holding_Port_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("61495.00"),
        )
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)

        # Create holding
        holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=10,
            average_buy_price=Decimal("3850.50"),
            current_price=Decimal("3850.50"),
            realized_pnl=Decimal("0.00"),
        )
        session.add(holding)
        await session.commit()

        # Query with relationship
        stmt = (
            select(Holding)
            .where(Holding.id == holding.id)
            .options(selectinload(Holding.stock), selectinload(Holding.portfolio))
        )
        result = await session.execute(stmt)
        queried_holding = result.scalar_one()

        assert queried_holding.stock.symbol == f"TCS_{uid}"
        assert queried_holding.portfolio.name == f"Holding_Port_{uid}"
        assert queried_holding.quantity == 10
        assert queried_holding.average_buy_price == Decimal("3850.50")

@pytest.mark.asyncio
async def test_agent_and_agent_messages():
    """Verify Agent creation and structured AgentMessage collaboration relationships."""
    async with AsyncSessionLocal() as session:
        uid = uuid.uuid4().hex[:6]
        # Create 2 agents with unique names
        analyst = Agent(
            name=f"Analyst_{uid}",
            role="market_analyst",
            status="IDLE",
        )
        trader = Agent(
            name=f"Trader_{uid}",
            role="trader",
            status="WORKING",
        )
        session.add_all([analyst, trader])
        await session.commit()
        await session.refresh(analyst)
        await session.refresh(trader)

        # Send structured findings message from Analyst to Trader
        msg = AgentMessage(
            sender_id=analyst.id,
            recipient_id=trader.id,
            message_type="FINDINGS",
            task_id=f"TASK_{uid}",
            correlation_id=f"CORR_{uid}",
            payload='{"symbol": "INFY", "sentiment": "BULLISH", "confidence": 0.88}',
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        assert msg.message_id is not None
        assert msg.timestamp.tzinfo is not None # UTC verified

        # Query messages for trader
        stmt = select(AgentMessage).where(AgentMessage.recipient_id == trader.id).options(selectinload(AgentMessage.sender))
        res = await session.execute(stmt)
        received_msgs = res.scalars().all()
        assert len(received_msgs) >= 1
        assert received_msgs[0].sender.name == f"Analyst_{uid}"
        assert "INFY" in received_msgs[0].payload

@pytest.mark.asyncio
async def test_news_decision_and_risk_event():
    """Verify full end-to-end relational audit trail from News -> Decision -> RiskEvent."""
    async with AsyncSessionLocal() as session:
        uid = uuid.uuid4().hex[:6]
        # Ingest news article
        article = NewsArticle(
            title=f"Q3 Results: Infy reports 12% profit growth - {uid}",
            source="BSE Announcements",
            url=f"https://bseindia.com/news-{uid}",
            sentiment="BULLISH",
            sentiment_score=Decimal("0.8500"),
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)

        # Stock
        stock = Stock(symbol=f"INFY_{uid}", name="Infosys Ltd", exchange="NSE", current_price=Decimal("1520.00"))
        session.add(stock)
        await session.commit()
        await session.refresh(stock)

        # Trading Decision (Proposal)
        decision = TradingDecision(
            decision_type="BUY",
            stock_id=stock.id,
            article_id=article.id,
            proposed_quantity=50,
            proposed_price=Decimal("1520.00"),
            confidence_score=Decimal("0.8500"),
            reasoning="Strong earnings growth reported on BSE",
            status="PENDING",
        )
        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        # Risk assessment event
        risk_check = RiskEvent(
            decision_id=decision.id,
            event_type="CAPITAL_LIMIT",
            severity="INFO",
            description="Proposed amount 76000.00 is within 80% portfolio limit",
            status="APPROVED",
        )
        session.add(risk_check)
        await session.commit()

        # Query decision with relationships
        stmt = select(TradingDecision).where(TradingDecision.id == decision.id).options(
            selectinload(TradingDecision.article),
            selectinload(TradingDecision.stock),
            selectinload(TradingDecision.risk_events),
        )
        res = await session.execute(stmt)
        loaded_decision = res.scalar_one()

        assert loaded_decision.article.title.startswith("Q3 Results")
        assert loaded_decision.stock.symbol == f"INFY_{uid}"
        assert len(loaded_decision.risk_events) == 1
        assert loaded_decision.risk_events[0].status == "APPROVED"
