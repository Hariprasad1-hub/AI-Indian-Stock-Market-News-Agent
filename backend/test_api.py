import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from decimal import Decimal

from backend.app.main import app
from backend.app.database import AsyncSessionLocal
from backend.app.models import Stock, Portfolio, Holding

@pytest.mark.asyncio
async def test_dashboard_summary_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/dashboard/summary")
        assert res.status_code == 200
        data = res.json()
        assert "portfolio_value" in data
        assert "available_cash" in data
        assert "total_trades" in data
        assert "active_agents_count" in data
        assert "recent_activity" in data
        assert float(data["available_cash"]) >= 0

@pytest.mark.asyncio
async def test_news_crud_and_duplicate_prevention():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_url = f"https://economictimes.indiatimes.com/news-{uuid.uuid4().hex}"
        article_payload = {
            "title": "BSE Sensex rallies 450 points led by banking stocks",
            "content": "Indian equity benchmarks logged solid gains...",
            "summary": "Sensex surges 450 points",
            "source": "Economic Times Markets",
            "url": unique_url,
            "sentiment": "BULLISH",
            "sentiment_score": 0.75,
        }
        # Ingest
        post_res = await client.post("/api/news", json=article_payload)
        assert post_res.status_code == 201
        created = post_res.json()
        assert created["url"] == unique_url
        assert created["sentiment"] == "BULLISH"

        # Duplicate ingestion check
        dup_res = await client.post("/api/news", json=article_payload)
        assert dup_res.status_code == 409
        assert "already been ingested" in dup_res.json()["detail"]

        # Fetch news list
        list_res = await client.get("/api/news?limit=10&sentiment=BULLISH")
        assert list_res.status_code == 200
        articles = list_res.json()
        assert isinstance(articles, list)
        assert any(a["url"] == unique_url for a in articles)

@pytest.mark.asyncio
async def test_stocks_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sym = f"STK_{uuid.uuid4().hex[:5].upper()}"
        stock_payload = {
            "symbol": sym,
            "name": "State Bank of India Test",
            "exchange": "NSE",
            "sector": "Banking",
            "current_price": 780.25,
            "is_active": True,
        }
        res = await client.post("/api/stocks", json=stock_payload)
        assert res.status_code == 201
        created = res.json()
        assert created["symbol"] == sym
        assert float(created["current_price"]) == 780.25

        # Query stocks
        get_res = await client.get(f"/api/stocks?symbol={sym}")
        assert get_res.status_code == 200
        stocks = get_res.json()
        assert len(stocks) >= 1
        assert stocks[0]["symbol"] == sym

@pytest.mark.asyncio
async def test_agents_and_messages_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get agents (seeds the 4 canonical agents)
        agents_res = await client.get("/api/agents")
        assert agents_res.status_code == 200
        agents = agents_res.json()
        assert len(agents) >= 4
        agent_names = {a["name"] for a in agents}
        assert "Market Intelligence Agent" in agent_names
        assert "Market Analyst Agent" in agent_names
        assert "Trader Agent" in agent_names
        assert "Risk Manager Agent" in agent_names

        # Send message between first two agents
        sender_id = agents[0]["id"]
        recipient_id = agents[1]["id"]
        task_id = f"TASK-{uuid.uuid4().hex[:6]}"
        corr_id = f"CORR-{uuid.uuid4().hex[:6]}"

        msg_payload = {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message_type": "FINDINGS",
            "task_id": task_id,
            "correlation_id": corr_id,
            "payload": '{"entities": ["TCS"], "sentiment": "BULLISH"}',
        }
        post_msg_res = await client.post("/api/agents/messages", json=msg_payload)
        assert post_msg_res.status_code == 201
        msg_data = post_msg_res.json()
        assert msg_data["message_type"] == "FINDINGS"
        assert msg_data["task_id"] == task_id

        # Query messages with filter
        get_msgs_res = await client.get(f"/api/agents/messages?task_id={task_id}")
        assert get_msgs_res.status_code == 200
        fetched_msgs = get_msgs_res.json()
        assert len(fetched_msgs) >= 1
        assert fetched_msgs[0]["correlation_id"] == corr_id

@pytest.mark.asyncio
async def test_decisions_and_proposal_creation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a stock first
        sym = f"DEC_{uuid.uuid4().hex[:5].upper()}"
        stk_res = await client.post(
            "/api/stocks",
            json={"symbol": sym, "name": "Decision Test Stock", "current_price": 500.00},
        )
        stk_id = stk_res.json()["id"]

        proposal_payload = {
            "decision_type": "BUY",
            "stock_id": stk_id,
            "proposed_quantity": 25,
            "proposed_price": 500.00,
            "confidence_score": 0.82,
            "reasoning": "Strong corporate quarterly results",
            "evidence": "Q2 revenue up 18% YoY",
        }
        create_res = await client.post("/api/decisions", json=proposal_payload)
        assert create_res.status_code == 201
        created_dec = create_res.json()
        assert created_dec["decision_type"] == "BUY"
        assert created_dec["status"] == "PENDING"
        assert created_dec["stock_symbol"] == sym

        # List decisions
        list_res = await client.get("/api/decisions?decision_type=BUY")
        assert list_res.status_code == 200
        decisions = list_res.json()
        assert any(d["id"] == created_dec["id"] for d in decisions)

@pytest.mark.asyncio
async def test_portfolio_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/portfolio")
        assert res.status_code == 200
        data = res.json()
        assert "cash_balance" in data
        assert "total_portfolio_value" in data
        assert "holdings" in data
        assert isinstance(data["holdings"], list)
        assert float(data["initial_cash"]) == 100000.0

@pytest.mark.asyncio
async def test_transactions_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/transactions?limit=10")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_risk_events_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/risk/events?limit=10")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_query_param_validation_errors():
    """Verify validation of query parameters like pagination limits."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Limit > 100 must fail with 422
        bad_limit_res = await client.get("/api/news?limit=500")
        assert bad_limit_res.status_code == 422

        # Negative skip must fail with 422
        bad_skip_res = await client.get("/api/news?skip=-5")
        assert bad_skip_res.status_code == 422
