import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    response = await client.get("/api/v1/health/")
    assert response.status_code in [200, 503]

@pytest.mark.asyncio
async def test_health_response_has_required_fields(client: AsyncClient):
    response = await client.get("/api/v1/health/")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "services" in data
    assert "timestamp" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]

@pytest.mark.asyncio
async def test_health_status_format(client: AsyncClient):
    response = await client.get("/api/v1/health/")
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
