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
from backend.app.init_db import initialize_app_database

# Removed async fixture

@pytest.mark.asyncio
async def test_agent_message_broker_persistence_and_idempotency():
    """Verify BAND-conforming message persistence, correlation tracking, and duplicate prevention."""
    async with AsyncSessionLocal() as session:
        broker = AgentMessageBroker(session)
        uid = uuid.uuid4().hex[:6]
        task_id = f"TASK-{uid}"
        corr_id = f"CORR-{uid}"

        # Send message
        msg1 = await broker.send_message(
            sender_role="market_intelligence",
            recipient_role="market_analyst",
            message_type="FINDINGS",
            task_id=task_id,
            correlation_id=corr_id,
            payload={"symbol": "INFY", "summary": "Quarterly surge"},
        )
        assert msg1.id is not None
        assert msg1.status == "DELIVERED"

        # Attempt sending exact duplicate message (same task, roles, and message_type)
        msg2 = await broker.send_message(
            sender_role="market_intelligence",
            recipient_role="market_analyst",
            message_type="FINDINGS",
            task_id=task_id,
            correlation_id=corr_id,
            payload={"symbol": "INFY", "summary": "Quarterly surge duplicate attempt"},
        )
        assert msg1.id == msg2.id # Must be idempotent, returning the existing record

        # Retrieve conversation history
        history = await broker.get_conversation_history(corr_id)
        assert len(history) == 1
        assert history[0].correlation_id == corr_id

@pytest.mark.asyncio
async def test_market_intelligence_agent_entity_extraction():
    """Verify Agent 1 normalizes Indian company names and extracts figures."""
    async with AsyncSessionLocal() as session:
        broker = AgentMessageBroker(session)
        agent = MarketIntelligenceAgent(session, broker)

        uid = uuid.uuid4().hex[:6]
        article = NewsArticle(
            title=f"Tata Consultancy Services wins massive multi-million dollar contract; TCS profit rises 14% to ₹12,000 crore - {uid}",
            summary="Strong quarterly disclosures on BSE",
            source="BSE Announcements",
            url=f"https://bseindia.com/contract-{uid}",
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)

        findings = await agent.process_article(article, task_id=f"T-{uid}", correlation_id=f"C-{uid}")
        assert "TCS" in findings["detected_symbols"]
        assert len(findings["extracted_figures"]["percentages"]) >= 1
        assert "14%" in findings["extracted_figures"]["percentages"][0]
        assert not findings["uncertainty_flag"]

@pytest.mark.asyncio
async def test_market_analyst_agent_scoring():
    """Verify Agent 2 computes evidence-grounded sentiment and confidence scores."""
    async with AsyncSessionLocal() as session:
        broker = AgentMessageBroker(session)
        agent = MarketAnalystAgent(session, broker)

        uid = uuid.uuid4().hex[:6]
        findings = {
            "article_id": 101,
            "title": f"Reliance profit surges to record high led by retail growth - {uid}",
            "detected_symbols": ["RELIANCE"],
            "extracted_figures": {"percentages": ["18%"], "crores": ["15000"]},
        }

        analysis = await agent.analyze_findings(findings, task_id=f"T-{uid}", correlation_id=f"C-{uid}")
        assert analysis["sentiment"] == "BULLISH"
        assert analysis["sentiment_score"] > 0.70
        assert analysis["market_impact"] == "HIGH_POSITIVE"
        assert analysis["confidence_score"] >= 0.80

@pytest.mark.asyncio
async def test_deterministic_risk_rules():
    """Independently verify all individual deterministic risk guardrails."""
    async with AsyncSessionLocal() as session:
        engine = DeterministicRiskEngine(session)
        uid = uuid.uuid4().hex[:6]

        # Setup Stock and Portfolio
        stock = Stock(
            symbol=f"RISK_{uid}",
            name="Risk Test Corp",
            exchange="NSE",
            sector="Technology",
            current_price=Decimal("1000.00"),
            price_status="LIVE",
            price_updated_at=datetime.now(timezone.utc),
        )
        portfolio = Portfolio(
            name=f"Risk_Port_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("10000.00"), # Only ₹10,000 cash available
        )
        session.add_all([stock, portfolio])
        await session.commit()
        await session.refresh(stock)
        await session.refresh(portfolio)

        # 1. Test Insufficient Funds Rule (Buy 15 shares @ ₹1000 = ₹15,000 > ₹10,000 cash)
        dec_insufficient = TradingDecision(
            decision_type="BUY",
            stock_id=stock.id,
            proposed_quantity=15,
            proposed_price=Decimal("1000.00"),
            status="PENDING",
        )
        session.add(dec_insufficient)
        await session.commit()

        res1 = await engine.evaluate_trade_proposal(dec_insufficient, portfolio)
        assert not res1.approved
        assert "RULE_INSUFFICIENT_FUNDS" in res1.rule_ids

        # 2. Test Stale Price Rule (> 15 minutes old)
        stock.price_updated_at = datetime.now(timezone.utc) - timedelta(minutes=25)
        await session.commit()

        dec_stale = TradingDecision(
            decision_type="BUY",
            stock_id=stock.id,
            proposed_quantity=2,
            proposed_price=Decimal("1000.00"),
            status="PENDING",
        )
        session.add(dec_stale)
        await session.commit()

        res2 = await engine.evaluate_trade_proposal(dec_stale, portfolio)
        assert not res2.approved
        assert "RULE_PRICE_STALE" in res2.rule_ids

        # 3. Test Unavailable Price Rule
        stock.price_status = "UNAVAILABLE"
        await session.commit()

        res3 = await engine.evaluate_trade_proposal(dec_stale, portfolio)
        assert not res3.approved
        assert "RULE_PRICE_UNAVAILABLE" in res3.rule_ids

        # Reset stock to live and fresh
        stock.price_status = "LIVE"
        stock.price_updated_at = datetime.now(timezone.utc)
        await session.commit()

        # 4. Test Short Selling Prevention Rule (Sell without holding)
        dec_short = TradingDecision(
            decision_type="SELL",
            stock_id=stock.id,
            proposed_quantity=5,
            proposed_price=Decimal("1000.00"),
            status="PENDING",
        )
        session.add(dec_short)
        await session.commit()

        res4 = await engine.evaluate_trade_proposal(dec_short, portfolio)
        assert not res4.approved
        assert "RULE_INSUFFICIENT_HOLDINGS" in res4.rule_ids

@pytest.mark.asyncio
async def test_paper_trading_execution_and_idempotency():
    """Verify paper trading buy/sell accounting, weighted average price, and duplicate execution prevention."""
    async with AsyncSessionLocal() as session:
        engine = PaperTradingEngine(session)
        uid = uuid.uuid4().hex[:6]

        stock = Stock(
            symbol=f"TRADE_{uid}",
            name="Trade Accounting Corp",
            exchange="NSE",
            current_price=Decimal("2000.00"),
            price_status="LIVE",
            price_updated_at=datetime.now(timezone.utc),
        )
        portfolio = Portfolio(
            name=f"Trade_Port_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
        )
        session.add_all([stock, portfolio])
        await session.commit()
        await session.refresh(stock)
        await session.refresh(portfolio)

        # 1. Execute Approved BUY: 10 shares @ ₹2000 = ₹20,000 + 0.1% fee (₹20) = ₹20,020
        buy_dec = TradingDecision(
            decision_type="BUY",
            stock_id=stock.id,
            proposed_quantity=10,
            proposed_price=Decimal("2000.00"),
            status="APPROVED", # Must be APPROVED
        )
        session.add(buy_dec)
        await session.commit()
        await session.refresh(buy_dec)

        tx1 = await engine.execute_approved_trade(buy_dec.id, portfolio.id)
        assert tx1.transaction_type == "BUY"
        assert tx1.quantity == 10
        assert tx1.total_amount == Decimal("20000.00")
        assert tx1.fee == Decimal("20.00")

        await session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("79980.00") # 100000 - 20020

        holding = await session.scalar(
            select(Holding).where(Holding.portfolio_id == portfolio.id, Holding.stock_id == stock.id)
        )
        assert holding.quantity == 10
        assert holding.average_buy_price == Decimal("2000.00")

        # 2. Test Idempotency: Repeating execution of the same decision must not double-deduct
        tx_repeat = await engine.execute_approved_trade(buy_dec.id, portfolio.id)
        assert tx_repeat.id == tx1.id
        await session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("79980.00") # Untouched

        # 3. Execute Approved SELL: 5 shares @ ₹2200 (realizing gain)
        stock.current_price = Decimal("2200.00")
        await session.commit()

        sell_dec = TradingDecision(
            decision_type="SELL",
            stock_id=stock.id,
            proposed_quantity=5,
            proposed_price=Decimal("2200.00"),
            status="APPROVED",
        )
        session.add(sell_dec)
        await session.commit()
        await session.refresh(sell_dec)

        tx2 = await engine.execute_approved_trade(sell_dec.id, portfolio.id)
        assert tx2.transaction_type == "SELL"
        assert tx2.quantity == 5
        assert tx2.total_amount == Decimal("11000.00")
        assert tx2.fee == Decimal("11.00")

        # Proceeds = 11000 - 11 = 10989. Cash = 79980 + 10989 = 90969.00
        await session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("90969.00")

        await session.refresh(holding)
        assert holding.quantity == 5 # 10 - 5 = 5 remaining
        # Realized P&L = (2200 - 2000) * 5 - 11 = 1000 - 11 = 989.00
        assert holding.realized_pnl == Decimal("989.00")

@pytest.mark.asyncio
async def test_end_to_end_agent_collaboration_and_execution_pipeline():
    """Complete E2E Demonstration Scenario:
    1. News article ingested.
    2. Market Intelligence extracts findings.
    3. Market Analyst scores sentiment.
    4. Trader proposes an intentionally unsafe BUY.
    5. Risk Manager REJECTS unsafe proposal with explicit rule ID.
    6. Trader receives feedback and submits valid compliant proposal.
    7. Risk Manager APPROVES valid proposal.
    8. Paper Trading Engine executes the approved proposal.
    9. Portfolio cash, holding, and transaction ledger verified.
    """
    async with AsyncSessionLocal() as session:
        broker = AgentMessageBroker(session)
        intel_agent = MarketIntelligenceAgent(session, broker)
        analyst_agent = MarketAnalystAgent(session, broker)
        trader_agent = TraderAgent(session, broker)
        risk_agent = RiskManagerAgent(session, broker)
        paper_engine = PaperTradingEngine(session)

        uid = uuid.uuid4().hex[:6]
        task_id = f"TASK_E2E_{uid}"
        corr_id = f"CORR_E2E_{uid}"

        # 1. Fetch or Create Stock & Portfolio fixture
        stock = await session.scalar(select(Stock).where(Stock.symbol == "RELIANCE"))
        if not stock:
            stock = Stock(
                symbol="RELIANCE",
                name="Reliance Industries Ltd",
                exchange="NSE",
                sector="Energy",
                current_price=Decimal("2500.00"),
                price_status="LIVE",
                price_updated_at=datetime.now(timezone.utc),
            )
            session.add(stock)
        else:
            stock.current_price = Decimal("2500.00")
            stock.price_status = "LIVE"
            stock.price_updated_at = datetime.now(timezone.utc)

        portfolio = Portfolio(
            name=f"E2E_Portfolio_{uid}",
            initial_cash=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
        )
        session.add(portfolio)
        await session.commit()
        await session.refresh(stock)
        await session.refresh(portfolio)

        # 2. Ingest Article
        article = NewsArticle(
            title=f"Reliance Industries net profit surges 18% in Q3; retail and telecom post solid revenue growth - {uid}",
            summary="Strong corporate announcements reported on BSE India regulatory portal.",
            source="BSE Announcements",
            url=f"https://bseindia.com/e2e-news-{uid}",
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)

        # 3. Market Intelligence Agent Execution
        findings = await intel_agent.process_article(article, task_id, corr_id)
        assert "RELIANCE" in findings["detected_symbols"]

        # 4. Market Analyst Agent Execution
        analysis = await analyst_agent.analyze_findings(findings, task_id, corr_id)
        assert analysis["sentiment"] == "BULLISH"
        assert analysis["confidence_score"] >= 0.80

        # 5. Trader Agent: Intentionally Unsafe Proposal (Attempting to buy 100 shares @ ₹2500 = ₹2,50,000 > ₹1,00,000 cash)
        unsafe_decision = await trader_agent.evaluate_analysis_and_propose(
            analysis, portfolio, task_id=f"{task_id}_UNSAFE", correlation_id=corr_id, override_quantity=100
        )
        assert unsafe_decision.decision_type == "BUY"
        assert unsafe_decision.status == "PENDING"

        # 6. Risk Manager Agent evaluates unsafe proposal -> REJECTED
        risk_res_unsafe = await risk_agent.evaluate_proposal(
            unsafe_decision.id, portfolio, task_id=f"{task_id}_UNSAFE", correlation_id=corr_id
        )
        assert not risk_res_unsafe.approved
        await session.refresh(unsafe_decision)
        assert unsafe_decision.status == "REJECTED"
        assert "RULE_INSUFFICIENT_FUNDS" in risk_res_unsafe.rule_ids

        # Trader receives feedback
        await trader_agent.handle_risk_feedback(
            {"decision_id": unsafe_decision.id, "status": "REJECTED", "rejection_reasons": risk_res_unsafe.rejection_reasons},
            task_id=f"{task_id}_UNSAFE",
            correlation_id=corr_id,
        )

        # 7. Trader Agent: Compliant Safe Proposal (Buy 4 shares @ ₹2500 = ₹10,000 = 10% of portfolio)
        safe_decision = await trader_agent.evaluate_analysis_and_propose(
            analysis, portfolio, task_id=f"{task_id}_SAFE", correlation_id=corr_id, override_quantity=4
        )
        assert safe_decision.decision_type == "BUY"
        assert safe_decision.proposed_quantity == 4
        assert safe_decision.status == "PENDING"

        # 8. Risk Manager Agent evaluates safe proposal -> APPROVED
        risk_res_safe = await risk_agent.evaluate_proposal(
            safe_decision.id, portfolio, task_id=f"{task_id}_SAFE", correlation_id=corr_id
        )
        assert risk_res_safe.approved
        await session.refresh(safe_decision)
        assert safe_decision.status == "APPROVED"

        # Verify RiskEvent record was saved
        risk_event = await session.scalar(
            select(RiskEvent).where(RiskEvent.decision_id == safe_decision.id)
        )
        assert risk_event is not None
        assert risk_event.status == "APPROVED"

        # 9. Paper Trading Engine Executes the Approved Proposal
        tx = await paper_engine.execute_approved_trade(safe_decision.id, portfolio.id)
        assert tx.transaction_type == "BUY"
        assert tx.quantity == 4
        assert tx.execution_price == Decimal("2500.00")
        assert tx.total_amount == Decimal("10000.00")
        assert tx.fee == Decimal("10.00") # 0.1%

        # 10. Verify Final Ledger State
        await session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("89990.00") # 100000 - 10010

        holding = await session.scalar(
            select(Holding).where(Holding.portfolio_id == portfolio.id, Holding.stock_id == stock.id)
        )
        assert holding is not None
        assert holding.quantity == 4
        assert holding.average_buy_price == Decimal("2500.00")

        # Verify full communication chain in broker
        chain = await broker.get_conversation_history(corr_id)
        assert len(chain) >= 4
        message_types = [m.message_type for m in chain]
        assert "FINDINGS" in message_types
        assert "STRUCTURED_ANALYSIS" in message_types
        assert "TRADE_PROPOSAL" in message_types
        assert "RISK_ASSESSMENT" in message_types
