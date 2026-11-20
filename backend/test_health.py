import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_health_check_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["project"] == "TRADEMIND AI"
        assert data["db_connected"] is True

@pytest.mark.asyncio
async def test_docs_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower() or "html" in response.headers.get("content-type", "")

@pytest.mark.asyncio
async def test_health_check_db_failure(monkeypatch):
    from backend.app import database

    # Simulate DB failure in get_db generator
    async def mock_failing_get_db():
        raise ConnectionError("Simulated DB connection failure")
        yield  # make it a generator

    monkeypatch.setattr(database, "get_db", mock_failing_get_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["project"] == "TRADEMIND AI"
        assert data["db_connected"] is False
