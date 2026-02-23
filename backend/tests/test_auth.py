"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_header


class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user: User):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "testuser@example.com",
            "password": "TestPassword123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "testuser@example.com",
            "password": "WrongPassword123!",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "nobody@example.com",
            "password": "TestPassword123!",
        })
        assert resp.status_code == 401

    async def test_login_json(self, client: AsyncClient, test_user: User):
        resp = await client.post("/api/v1/auth/login/json", json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()


class TestMe:
    async def test_get_me(self, client: AsyncClient, test_user: User):
        resp = await client.get("/api/v1/auth/me", headers=auth_header(test_user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "testuser@example.com"
        assert data["role"] == "pentester"

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestPasswordChange:
    async def test_change_password(self, client: AsyncClient, test_user: User):
        resp = await client.put("/api/v1/auth/password", headers=auth_header(test_user), json={
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!",
        })
        assert resp.status_code == 200

        # Login with new password
        resp2 = await client.post("/api/v1/auth/login", data={
            "username": "testuser@example.com",
            "password": "NewPassword456!",
        })
        assert resp2.status_code == 200

    async def test_change_password_wrong_current(self, client: AsyncClient, test_user: User):
        resp = await client.put("/api/v1/auth/password", headers=auth_header(test_user), json={
            "current_password": "WrongPassword!",
            "new_password": "NewPassword456!",
        })
        assert resp.status_code == 400


class TestRefresh:
    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        # First login
        login_resp = await client.post("/api/v1/auth/login", data={
            "username": "testuser@example.com",
            "password": "TestPassword123!",
        })
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert resp.status_code == 401
