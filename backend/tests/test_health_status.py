"""Tests for health and status endpoints."""

from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "checks" in data

    async def test_health_has_checks(self, client: AsyncClient):
        resp = await client.get("/health")
        data = resp.json()
        assert "database" in data["checks"]
        assert "redis" in data["checks"]


class TestStatusEndpoint:
    async def test_status_returns_200(self, client: AsyncClient):
        resp = await client.get("/api/v1/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "uptime_seconds" in data
        assert "app" in data

    async def test_root_endpoint(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "app" in data
        assert "docs" in data
