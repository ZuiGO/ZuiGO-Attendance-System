"""Unit tests for Multi-Tenant resolution middleware."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.tenant import extract_subdomain
from app.main import app


def test_extract_subdomain():
    """Test subdomain parsing rules."""
    assert extract_subdomain("acme.attendance.zuigo.ai") == "acme"
    assert extract_subdomain("hospital1.zuigo.ai") == "hospital1"
    assert extract_subdomain("localhost:8000") is None
    assert extract_subdomain("127.0.0.1:8000") is None
    assert extract_subdomain("zuigo.ai") is None


@pytest.mark.asyncio
async def test_tenant_header_resolution():
    """Test that X-Tenant-ID header sets tenant context on request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Request with X-Tenant-ID header
        response = await client.get("/ready", headers={"X-Tenant-ID": "tenant-test-123"})
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "tenant-test-123"
        assert response.headers.get("X-Tenant-ID") == "tenant-test-123"


@pytest.mark.asyncio
async def test_subdomain_tenant_resolution():
    """Test that subdomains in Host header resolve to tenant context."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://acme.attendance.zuigo.ai") as client:
        response = await client.get("/ready", headers={"Host": "acme.attendance.zuigo.ai"})
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "acme"
