"""Integration tests for core FastAPI endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test /health liveness probe."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "zuigo-attendance-backend"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_readiness_probe_without_tenant():
    """Test /ready without tenant header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["tenant_id"] is None


@pytest.mark.asyncio
async def test_cors_headers():
    """Test that CORS headers are returned properly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
