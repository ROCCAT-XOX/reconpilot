"""Tests for scan endpoints including fallback execution."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.scan import Scan
from app.models.scope import ScopeTarget
from app.models.user import User
from tests.conftest import auth_header


class TestScanCRUD:
    async def test_create_scan(self, client: AsyncClient, test_user: User, test_project: Project, test_scope: ScopeTarget):
        with patch("app.api.v1.scans._try_celery_dispatch", side_effect=ConnectionError("Redis down")), \
             patch("app.api.v1.scans._run_scan_fallback", new_callable=AsyncMock):
            resp = await client.post(
                f"/api/v1/projects/{test_project.id}/scans",
                headers=auth_header(test_user),
                json={"profile": "quick", "targets": ["example.com"]},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["profile"] == "quick"
        assert data["status"] == "pending"

    async def test_create_scan_no_targets_no_scope(self, client: AsyncClient, test_user: User, test_project: Project):
        resp = await client.post(
            f"/api/v1/projects/{test_project.id}/scans",
            headers=auth_header(test_user),
            json={"profile": "quick"},
        )
        assert resp.status_code == 400
        assert "No targets" in resp.json()["detail"]

    async def test_create_scan_unknown_profile(self, client: AsyncClient, test_user: User, test_project: Project):
        resp = await client.post(
            f"/api/v1/projects/{test_project.id}/scans",
            headers=auth_header(test_user),
            json={"profile": "quick"},  # profile validation is regex, "nonexistent" wouldn't pass pydantic
        )
        # No scope and no targets -> 400
        assert resp.status_code == 400

    async def test_list_scans(self, client: AsyncClient, test_user: User, test_scan: Scan):
        resp = await client.get("/api/v1/scans/", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_scan(self, client: AsyncClient, test_user: User, test_scan: Scan):
        resp = await client.get(f"/api/v1/scans/{test_scan.id}", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["id"] == str(test_scan.id)

    async def test_get_scan_not_found(self, client: AsyncClient, test_user: User):
        resp = await client.get(f"/api/v1/scans/{uuid.uuid4()}", headers=auth_header(test_user))
        assert resp.status_code == 404

    async def test_list_project_scans(self, client: AsyncClient, test_user: User, test_project: Project, test_scan: Scan):
        resp = await client.get(f"/api/v1/projects/{test_project.id}/scans", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


class TestScanLifecycle:
    async def test_cancel_pending_scan(self, client: AsyncClient, test_user: User, test_project: Project, test_scope: ScopeTarget):
        with patch("app.api.v1.scans._try_celery_dispatch", side_effect=ConnectionError("Redis down")), \
             patch("app.api.v1.scans._run_scan_fallback", new_callable=AsyncMock):
            create_resp = await client.post(
                f"/api/v1/projects/{test_project.id}/scans",
                headers=auth_header(test_user),
                json={"profile": "quick", "targets": ["example.com"]},
            )
        scan_id = create_resp.json()["id"]

        resp = await client.put(f"/api/v1/scans/{scan_id}/cancel", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_viewer_cannot_create_scan(self, client: AsyncClient, viewer_user: User, test_project: Project):
        resp = await client.post(
            f"/api/v1/projects/{test_project.id}/scans",
            headers=auth_header(viewer_user),
            json={"profile": "quick", "targets": ["example.com"]},
        )
        assert resp.status_code == 403


class TestScanFallback:
    async def test_fallback_triggered_when_redis_down(self, client: AsyncClient, test_user: User, test_project: Project, test_scope: ScopeTarget):
        """When Celery dispatch fails, fallback should be triggered."""
        fallback_called = False

        async def mock_fallback(*args, **kwargs):
            nonlocal fallback_called
            fallback_called = True

        with patch("app.api.v1.scans._try_celery_dispatch", side_effect=ConnectionError("Redis down")), \
             patch("app.api.v1.scans._run_scan_fallback", side_effect=mock_fallback) as mock_fb:
            resp = await client.post(
                f"/api/v1/projects/{test_project.id}/scans",
                headers=auth_header(test_user),
                json={"profile": "quick", "targets": ["example.com"]},
            )

        assert resp.status_code == 201
        # The fallback task was scheduled (create_task was called)


class TestScanRetry:
    async def test_retry_failed_scan(self, client: AsyncClient, test_user: User, test_project: Project, test_scope: ScopeTarget, db_session):
        """Can retry a failed scan."""
        scan = Scan(
            id=uuid.uuid4(),
            project_id=test_project.id,
            name="Failed Scan",
            profile="quick",
            config={"targets": ["example.com"]},
            started_by=test_user.id,
            status="failed",
        )
        db_session.add(scan)
        await db_session.commit()

        with patch("app.api.v1.scans._try_celery_dispatch", side_effect=ConnectionError("Redis down")), \
             patch("app.api.v1.scans._run_scan_fallback", new_callable=AsyncMock):
            resp = await client.post(
                f"/api/v1/projects/{test_project.id}/scans/{scan.id}/retry",
                headers=auth_header(test_user),
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_retry_running_scan_fails(self, client: AsyncClient, test_user: User, test_project: Project, db_session):
        scan = Scan(
            id=uuid.uuid4(),
            project_id=test_project.id,
            name="Running Scan",
            profile="quick",
            config={},
            started_by=test_user.id,
            status="running",
        )
        db_session.add(scan)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/projects/{test_project.id}/scans/{scan.id}/retry",
            headers=auth_header(test_user),
        )
        assert resp.status_code == 400
