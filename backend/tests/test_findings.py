"""Tests for findings CRUD and deduplication."""


from httpx import AsyncClient

from app.models.finding import Finding
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User
from tests.conftest import auth_header


class TestFindingsCRUD:
    async def test_create_finding(self, client: AsyncClient, test_user: User, test_project: Project, test_scan: Scan):
        resp = await client.post("/api/v1/findings/", headers=auth_header(test_user), json={
            "scan_id": str(test_scan.id),
            "project_id": str(test_project.id),
            "title": "SQL Injection",
            "severity": "critical",
            "source_tool": "sqlmap",
            "target_host": "example.com",
            "target_port": 443,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "SQL Injection"
        assert data["severity"] == "critical"
        assert data["fingerprint"] is not None

    async def test_list_findings(self, client: AsyncClient, test_user: User, test_finding: Finding):
        resp = await client.get("/api/v1/findings/", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_finding(self, client: AsyncClient, test_user: User, test_finding: Finding):
        resp = await client.get(f"/api/v1/findings/{test_finding.id}", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test XSS Vulnerability"

    async def test_update_finding_status(self, client: AsyncClient, test_user: User, test_finding: Finding):
        resp = await client.put(f"/api/v1/findings/{test_finding.id}", headers=auth_header(test_user), json={
            "status": "confirmed",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    async def test_verify_finding(self, client: AsyncClient, test_user: User, test_finding: Finding):
        resp = await client.put(f"/api/v1/findings/{test_finding.id}/verify", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    async def test_filter_by_severity(self, client: AsyncClient, test_user: User, test_finding: Finding):
        resp = await client.get("/api/v1/findings/?severity=high", headers=auth_header(test_user))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["severity"] == "high"

    async def test_project_findings(self, client: AsyncClient, test_user: User, test_project: Project, test_finding: Finding):
        resp = await client.get(f"/api/v1/projects/{test_project.id}/findings", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_finding_stats(self, client: AsyncClient, test_user: User, test_project: Project, test_finding: Finding):
        resp = await client.get(f"/api/v1/projects/{test_project.id}/findings/stats", headers=auth_header(test_user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "by_severity" in data


class TestFindingComments:
    async def test_add_comment(self, client: AsyncClient, test_user: User, test_finding: Finding):
        resp = await client.post(
            f"/api/v1/findings/{test_finding.id}/comments",
            headers=auth_header(test_user),
            json={"content": "This needs immediate attention"},
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "This needs immediate attention"

    async def test_list_comments(self, client: AsyncClient, test_user: User, test_finding: Finding):
        # Add a comment first
        await client.post(
            f"/api/v1/findings/{test_finding.id}/comments",
            headers=auth_header(test_user),
            json={"content": "Test comment"},
        )
        resp = await client.get(f"/api/v1/findings/{test_finding.id}/comments", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestDeduplication:
    async def test_fingerprint_generated(self, client: AsyncClient, test_user: User, test_project: Project, test_scan: Scan):
        resp = await client.post("/api/v1/findings/", headers=auth_header(test_user), json={
            "scan_id": str(test_scan.id),
            "project_id": str(test_project.id),
            "title": "Open Port 22",
            "severity": "info",
            "source_tool": "nmap",
            "target_host": "10.0.0.1",
            "target_port": 22,
        })
        assert resp.status_code == 201
        assert resp.json()["fingerprint"] is not None
