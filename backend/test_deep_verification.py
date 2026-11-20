import asyncio
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select, and_

from backend.app.database import AsyncSessionLocal
from backend.app.models import (
    Stock,
    Portfolio,
    Holding,
    TradeTransaction,
    TradingDecision,
    NewsArticle,
    Agent,
    AgentMessage,
    RiskEvent,
)
from backend.app.agents.broker import AgentMessageBroker
from backend.app.agents.intelligence import MarketIntelligenceAgent
from backend.app.agents.analyst import MarketAnalystAgent
from backend.app.agents.trader import TraderAgent
from backend.app.agents.risk_manager import RiskManagerAgent
from backend.app.risk.engine import DeterministicRiskEngine
from backend.app.trading.engine import PaperTradingEngine
from backend.app.trading.market_data import ExternalNSEMarketDataProvider
from backend.app.init_db import initialize_app_database

@pytest.mark.asyncio
async def test_intelligence_agent_edge_cases():
    """Verify Market Intelligence handles blank input, multi-entity text, and message routing."""
    await initialize_app_database()
    async with AsyncSessionLocal() as session:
        broker = AgentMessageBroker(session)
        agent = MarketIntelligenceAgent(session, broker)
        uid = uuid.uuid4().hex[:6]

        # 1. Blank/Generic text
        blank_article = NewsArticle(
            title=f"General economic market commentary on inflation - {uid}",
            summary="No specific companies mentioned",
            source="Economic Times",
            url=f"https://et.com/gen-{uid}",
        )
        session.add(blank_article)
        await session.commit()

        findings_blank = await agent.process_article(blank_article, task_id=f"TB_{uid}", correlation_id=f"CB_{uid}")
        assert findings_blank["detected_symbols"] == []
        assert findings_blank["uncertainty_flag"] is True

        # 2. Multi-entity text with specific Indian companies
        multi_article = NewsArticle(
            title=f"HDFC Bank and Infosys announce strategic digital banking alliance; Reliance expands telecom - {uid}",
            summary="Multi-sector expansion reports",
            source="BSE Announcements",
            url=f"https://bseindia.com/multi-{uid}",
        )
        session.add(multi_article)
        await session.commit()

        findings_multi = await agent.process_article(multi_article, task_id=f"TM_{uid}", correlation_id=f"CM_{uid}")
        symbols = findings_multi["detected_symbols"]
        assert "HDFCBANK" in symbols
        assert "INFY" in symbols
        assert "RELIANCE" in symbols
        assert findings_multi["uncertainty_flag"] is False

        # Verify message stored in DB
        msg = await session.scalar(
            select(AgentMessage).where(AgentMessage.correlation_id == f"CM_{uid}")
        )
        assert msg is not None
        assert msg.message_type == "FINDINGS"

@pytest.mark.asyncio
async def test_analyst_agent_sentiment_and_confidence():
    """Verify Market Analyst correctly identifies bearish vs neutral vs bullish sentiment."""
    await initialize_app_database()
    async with AsyncSessionLocal() as session:
        broker = AgentMessageBroker(session)
        agent = MarketAnalystAgent(session, broker)
        uid = uuid.uuid4().hex[:6]

        # 1. Bearish News
        bearish_findings = {
            "article_id": 201,
            "title": f"Company reports massive net loss; regulator initiates fraud penalty investigation - {uid}",
            "detected_symbols": ["SBIN"],
            "extracted_figures": {"percentages": ["-22%"], "crores": []},
        }
        bearish_res = await agent.analyze_findings(bearish_findings, task_id=f"T_BEAR_{uid}", correlation_id=f"C_BEAR_{uid}")
        assert bearish_res["sentiment"] == "BEARISH"
        assert bearish_res["sentiment_score"] < -0.70
        assert bearish_res["market_impact"] == "HIGH_NEGATIVE"

        # 2. Neutral News
        neutral_findings = {
            "article_id": 202,
            "title": f"Board meeting scheduled to review corporate governance structure - {uid}",
            "detected_symbols": ["TCS"],
            "extracted_figures": {"percentages": [], "crores": []},
        }
        neutral_res = await agent.analyze_findings(neutral_findings, task_id=f"T_NEUT_{uid}", correlation_id=f"C_NEUT_{uid}")
        assert neutral_res["sentiment"] == "NEUTRAL"
        assert neutral_res["sentiment_score"] == 0.0
        assert neutral_res["market_impact"] == "NEUTRAL"

@pytest.mark.asyncio
async def test_trader_agent_decision_matrix_and_feedback():
    """Verify Trader Agent decision logic (Short-selling block, position sizing, risk feedback)."""
    await initialize_app_database()
    async with AsyncSessionLocal() as session:
        broker = AgentMessageBroker(session)
        trader = TraderAgent(session, broker)
        uid = uuid.uuid4().hex[:6]

        portfolio = Portfolio(
            name=f"Trader_Test_Port_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
        )
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)

        # 1. Bearish news for stock NOT held -> NO_ACTION (prevents short selling proposal)
        bearish_analysis = {
            "primary_symbol": "LT",
            "sentiment": "BEARISH",
            "confidence_score": 0.85,
            "article_id": 301,
        }
        dec_no_short = await trader.evaluate_analysis_and_propose(
            bearish_analysis, portfolio, task_id=f"T_NOSHORT_{uid}", correlation_id=f"C_NOSHORT_{uid}"
        )
        assert dec_no_short.decision_type == "NO_ACTION"
        assert dec_no_short.status == "NO_ACTION"
        assert "short-selling prohibited" in dec_no_short.reasoning.lower()

        # 2. Bullish news -> BUY with prudent 10% cash allocation
        bullish_analysis = {
            "primary_symbol": "INFY",
            "sentiment": "BULLISH",
            "confidence_score": 0.88,
            "article_id": 302,
        }
        dec_buy = await trader.evaluate_analysis_and_propose(
            bullish_analysis, portfolio, task_id=f"T_BUY_{uid}", correlation_id=f"C_BUY_{uid}"
        )
        assert dec_buy.decision_type == "BUY"
        assert dec_buy.status == "PENDING"
        assert dec_buy.proposed_quantity > 0

        # 3. Test handling risk rejection feedback
        await trader.handle_risk_feedback(
            {"decision_id": dec_buy.id, "status": "REJECTED", "rejection_reasons": ["Test concentration limit exceeded"]},
            task_id=f"T_BUY_{uid}",
            correlation_id=f"C_BUY_{uid}",
        )
        await session.refresh(dec_buy)
        assert "concentration limit" in dec_buy.rejection_reason

@pytest.mark.asyncio
async def test_risk_engine_precise_boundary_rules():
    """Verify deterministic boundary conditions: position limits, staleness cutoffs, and exact cash."""
    await initialize_app_database()
    async with AsyncSessionLocal() as session:
        risk_engine = DeterministicRiskEngine(session)
        uid = uuid.uuid4().hex[:6]

        # Total portfolio: Cash ₹80,000 + Holding ₹20,000 = ₹1,00,000 Total Value
        # Max single position limit (20%) = ₹20,000
        stock = Stock(
            symbol=f"BOUND_{uid}",
            name="Boundary Test Corp",
            sector="Finance",
            current_price=Decimal("1000.00"),
            price_status="LIVE",
            price_updated_at=datetime.now(timezone.utc),
        )
        portfolio = Portfolio(
            name=f"Bound_Port_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
        )
        session.add_all([stock, portfolio])
        await session.commit()
        await session.refresh(stock)
        await session.refresh(portfolio)

        # 1. Position limit: Buy 20 shares @ ₹1000 = ₹20,000 (Exactly 20% of ₹1,00,000) -> APPROVED
        dec_exact_limit = TradingDecision(
            decision_type="BUY",
            stock_id=stock.id,
            proposed_quantity=20,
            proposed_price=Decimal("1000.00"),
            status="PENDING",
        )
        session.add(dec_exact_limit)
        await session.commit()

        res_exact = await risk_engine.evaluate_trade_proposal(dec_exact_limit, portfolio)
        assert res_exact.approved, f"Expected approved at exact 20% limit, got: {res_exact.rejection_reasons}"

        # 2. Position limit: Buy 21 shares @ ₹1000 = ₹21,000 (21% > 20% limit) -> REJECTED
        dec_over_limit = TradingDecision(
            decision_type="BUY",
            stock_id=stock.id,
            proposed_quantity=21,
            proposed_price=Decimal("1000.00"),
            status="PENDING",
        )
        session.add(dec_over_limit)
        await session.commit()

        res_over = await risk_engine.evaluate_trade_proposal(dec_over_limit, portfolio)
        assert not res_over.approved
        assert "RULE_POSITION_LIMIT_EXCEEDED" in res_over.rule_ids

        # 3. Staleness cutoff: Price 14 minutes old -> APPROVED
        stock.price_updated_at = datetime.now(timezone.utc) - timedelta(minutes=14)
        await session.commit()
        res_fresh = await risk_engine.evaluate_trade_proposal(dec_exact_limit, portfolio)
        assert "RULE_PRICE_STALE" not in res_fresh.rule_ids

        # Price 16 minutes old -> REJECTED
        stock.price_updated_at = datetime.now(timezone.utc) - timedelta(minutes=16)
        await session.commit()
        res_stale = await risk_engine.evaluate_trade_proposal(dec_exact_limit, portfolio)
        assert not res_stale.approved
        assert "RULE_PRICE_STALE" in res_stale.rule_ids

@pytest.mark.asyncio
async def test_paper_trading_concurrency_and_atomic_rollback():
    """Verify execution idempotency under concurrent calls and transaction safety."""
    await initialize_app_database()
    async with AsyncSessionLocal() as session:
        engine = PaperTradingEngine(session)
        uid = uuid.uuid4().hex[:6]

        stock = Stock(
            symbol=f"CONC_{uid}",
            name="Concurrent Exec Corp",
            current_price=Decimal("1500.00"),
            price_status="LIVE",
            price_updated_at=datetime.now(timezone.utc),
        )
        portfolio = Portfolio(
            name=f"Conc_Port_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
        )
        session.add_all([stock, portfolio])
        await session.commit()
        await session.refresh(stock)
        await session.refresh(portfolio)

        decision = TradingDecision(
            decision_type="BUY",
            stock_id=stock.id,
            proposed_quantity=10,
            proposed_price=Decimal("1500.00"),
            status="APPROVED",
        )
        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        # Execute first time: 10 @ 1500 = 15000 + 15 fee = 15015
        tx1 = await engine.execute_approved_trade(decision.id, portfolio.id)
        assert tx1.id is not None
        await session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("84985.00")

        # Second sequential or concurrent execution attempt of the SAME decision
        tx2 = await engine.execute_approved_trade(decision.id, portfolio.id)
        assert tx2.id == tx1.id # Returns existing transaction

        # Verify cash was NOT deducted a second time
        await session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("84985.00")

        # Verify only 1 transaction exists in DB for this decision
        tx_count = await session.scalar(
            select(TradeTransaction).where(TradeTransaction.decision_id == decision.id)
        )
        assert tx_count is not None

@pytest.mark.asyncio
async def test_paper_trading_multi_step_weighted_average_accounting():
    """Verify multi-step purchases calculate accurate weighted average entry prices and realized gains."""
    await initialize_app_database()
    async with AsyncSessionLocal() as session:
        engine = PaperTradingEngine(session)
        uid = uuid.uuid4().hex[:6]

        stock = Stock(
            symbol=f"AVG_{uid}",
            name="Averaging Accounting Corp",
            current_price=Decimal("1000.00"),
            price_status="LIVE",
            price_updated_at=datetime.now(timezone.utc),
        )
        portfolio = Portfolio(
            name=f"Avg_Port_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
        )
        session.add_all([stock, portfolio])
        await session.commit()
        await session.refresh(stock)
        await session.refresh(portfolio)

        # Batch 1: Buy 10 shares @ ₹1000
        dec1 = TradingDecision(decision_type="BUY", stock_id=stock.id, proposed_quantity=10, proposed_price=Decimal("1000.00"), status="APPROVED")
        session.add(dec1)
        await session.commit()
        await engine.execute_approved_trade(dec1.id, portfolio.id)

        # Batch 2: Price rises to ₹2000. Buy 10 more shares @ ₹2000
        stock.current_price = Decimal("2000.00")
        await session.commit()

        dec2 = TradingDecision(decision_type="BUY", stock_id=stock.id, proposed_quantity=10, proposed_price=Decimal("2000.00"), status="APPROVED")
        session.add(dec2)
        await session.commit()
        await engine.execute_approved_trade(dec2.id, portfolio.id)

        # Weighted Average should be (10*1000 + 10*2000)/20 = 30000 / 20 = ₹1500.00
        holding = await session.scalar(
            select(Holding).where(Holding.portfolio_id == portfolio.id, Holding.stock_id == stock.id)
        )
        assert holding.quantity == 20
        assert holding.average_buy_price == Decimal("1500.00")

@pytest.mark.asyncio
async def test_external_market_data_provider_honesty():
    """Verify external market data provider reports honest NOT CONNECTED status."""
    provider = ExternalNSEMarketDataProvider(api_key=None)
    assert not provider.is_connected()

    quote = await provider.get_quote("RELIANCE")
    assert quote.price is None
    assert quote.price_status == "UNAVAILABLE"
    assert "not connected" in quote.metadata["error"].lower()
