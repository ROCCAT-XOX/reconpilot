"""Tests for dashboard stats endpoint."""

from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_header


class TestDashboard:
    async def test_get_stats(self, client: AsyncClient, test_user: User, test_project, test_scan, test_finding):
        resp = await client.get("/api/v1/dashboard/stats", headers=auth_header(test_user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["projects_count"] >= 1
        assert data["total_findings"] >= 1
        assert "recent_scans" in data
        assert "critical_findings" in data
        assert "high_findings" in data

    async def test_stats_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 401

    async def test_stats_empty_db(self, client: AsyncClient, test_user: User):
        resp = await client.get("/api/v1/dashboard/stats", headers=auth_header(test_user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["projects_count"] == 0
        assert data["total_findings"] == 0
