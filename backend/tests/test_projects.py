"""Tests for project CRUD and member management."""

from httpx import AsyncClient

from app.models.project import Project
from app.models.user import User
from tests.conftest import auth_header


class TestProjectCRUD:
    async def test_create_project(self, client: AsyncClient, admin_user: User):
        resp = await client.post("/api/v1/projects/", headers=auth_header(admin_user), json={
            "name": "New Project",
            "client_name": "New Client",
            "description": "Test description",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Project"
        assert data["status"] == "active"

    async def test_list_projects(self, client: AsyncClient, test_user: User, test_project: Project):
        resp = await client.get("/api/v1/projects/", headers=auth_header(test_user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_project(self, client: AsyncClient, test_user: User, test_project: Project):
        resp = await client.get(f"/api/v1/projects/{test_project.id}", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Project"

    async def test_update_project(self, client: AsyncClient, admin_user: User, test_project: Project):
        resp = await client.put(f"/api/v1/projects/{test_project.id}", headers=auth_header(admin_user), json={
            "name": "Updated Project",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Project"

    async def test_archive_project(self, client: AsyncClient, admin_user: User, test_project: Project):
        resp = await client.delete(f"/api/v1/projects/{test_project.id}", headers=auth_header(admin_user))
        assert resp.status_code == 200

    async def test_viewer_cannot_create_project(self, client: AsyncClient, viewer_user: User):
        resp = await client.post("/api/v1/projects/", headers=auth_header(viewer_user), json={
            "name": "Forbidden", "client_name": "C",
        })
        assert resp.status_code == 403

    async def test_get_nonexistent_project(self, client: AsyncClient, test_user: User):
        resp = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=auth_header(test_user))
        assert resp.status_code == 404


class TestProjectScope:
    async def test_add_scope_target(self, client: AsyncClient, test_user: User, test_project: Project):
        resp = await client.post(f"/api/v1/projects/{test_project.id}/scope", headers=auth_header(test_user), json={
            "target_type": "domain",
            "target_value": "example.com",
        })
        assert resp.status_code == 201
        assert resp.json()["target_value"] == "example.com"

    async def test_list_scope_targets(self, client: AsyncClient, test_user: User, test_project: Project, test_scope):
        resp = await client.get(f"/api/v1/projects/{test_project.id}/scope", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_validate_scope_in_scope(self, client: AsyncClient, test_user: User, test_project: Project, test_scope):
        resp = await client.post(f"/api/v1/projects/{test_project.id}/scope/validate", headers=auth_header(test_user), json={
            "targets": ["sub.example.com"],
        })
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert results["sub.example.com"]["is_valid"] is True

    async def test_validate_scope_out_of_scope(self, client: AsyncClient, test_user: User, test_project: Project, test_scope):
        resp = await client.post(f"/api/v1/projects/{test_project.id}/scope/validate", headers=auth_header(test_user), json={
            "targets": ["evil.com"],
        })
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert results["evil.com"]["is_valid"] is False

    async def test_delete_scope_target(self, client: AsyncClient, test_user: User, test_project: Project, test_scope):
        resp = await client.delete(
            f"/api/v1/projects/{test_project.id}/scope/{test_scope.id}",
            headers=auth_header(test_user),
        )
        assert resp.status_code == 200
