"""Tests for authentication and security utilities."""
import pytest

from app.api.deps import has_permission
from app.core.security import (
    InvalidTokenError,
    WrongTokenTypeError,
    create_access_token,
    create_refresh_token,
    get_token_ttl_seconds,
    hash_password,
    verify_password,
    verify_token,
)


class TestTokenCreation:
    def test_create_access_token_returns_string(self):
        token = create_access_token("user-123", "admin")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_access_token_has_correct_claims(self):
        token = create_access_token("user-456", "pentester")
        payload = verify_token(token)
        assert payload["sub"] == "user-456"
        assert payload["role"] == "pentester"
        assert payload["type"] == "access"

    def test_refresh_token_has_correct_type(self):
        token = create_refresh_token("user-789")
        payload = verify_token(token, expected_type="refresh")
        assert payload["sub"] == "user-789"
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self):
        token = create_access_token("user-1", "admin")
        with pytest.raises(WrongTokenTypeError):
            verify_token(token, expected_type="refresh")

    def test_refresh_token_rejected_as_access(self):
        token = create_refresh_token("user-1")
        with pytest.raises(WrongTokenTypeError):
            verify_token(token, expected_type="access")


class TestTokenVerification:
    def test_invalid_token_raises(self):
        with pytest.raises(InvalidTokenError):
            verify_token("not.a.valid.token")

    def test_token_ttl_is_positive(self):
        token = create_access_token("user-1", "admin")
        ttl = get_token_ttl_seconds(token)
        assert ttl > 0

    def test_garbage_token_ttl_is_zero(self):
        ttl = get_token_ttl_seconds("garbage")
        assert ttl == 0


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("mysecretpass")
        assert verify_password("mysecretpass", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestRBAC:
    def test_admin_has_all_permissions(self):
        assert has_permission("admin", "users.manage")
        assert has_permission("admin", "scans.manage")
        assert has_permission("admin", "findings.view")

    def test_viewer_limited(self):
        assert has_permission("viewer", "findings.view")
        assert has_permission("viewer", "reports.view")
        assert not has_permission("viewer", "scans.manage")
        assert not has_permission("viewer", "users.manage")

    def test_pentester_can_scan(self):
        assert has_permission("pentester", "scans.manage")
        assert has_permission("pentester", "findings.edit")
        assert not has_permission("pentester", "users.manage")

    def test_unknown_role_has_no_permissions(self):
        assert not has_permission("unknown_role", "findings.view")
