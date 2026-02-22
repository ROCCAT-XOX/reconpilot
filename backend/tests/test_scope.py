"""Tests for scope validation."""
import pytest

from app.services.scope_validator import ScopeValidator


@pytest.fixture
def validator():
    allowed = [
        {"type": "domain", "value": "example.com"},
        {"type": "ip", "value": "10.0.0.1"},
        {"type": "ip_range", "value": "192.168.1.0/24"},
        {"type": "url", "value": "https://api.example.com"},
    ]
    excluded = [
        {"type": "domain", "value": "admin.example.com"},
        {"type": "ip", "value": "192.168.1.1"},
    ]
    return ScopeValidator(allowed_targets=allowed, excluded_targets=excluded)


class TestDomainScope:
    def test_exact_domain_match(self, validator):
        result = validator.validate("example.com")
        assert result.is_valid

    def test_subdomain_match(self, validator):
        result = validator.validate("sub.example.com")
        assert result.is_valid

    def test_excluded_domain(self, validator):
        result = validator.validate("admin.example.com")
        assert not result.is_valid
        assert "excluded" in result.reason

    def test_unrelated_domain_rejected(self, validator):
        result = validator.validate("evil.com")
        assert not result.is_valid


class TestIPScope:
    def test_exact_ip_match(self, validator):
        result = validator.validate("10.0.0.1")
        assert result.is_valid

    def test_ip_range_match(self, validator):
        result = validator.validate("192.168.1.50")
        assert result.is_valid

    def test_excluded_ip_in_range(self, validator):
        result = validator.validate("192.168.1.1")
        assert not result.is_valid

    def test_ip_outside_range(self, validator):
        result = validator.validate("10.10.10.10")
        assert not result.is_valid


class TestURLScope:
    def test_exact_url_match(self, validator):
        result = validator.validate("https://api.example.com")
        assert result.is_valid

    def test_url_prefix_match(self, validator):
        result = validator.validate("https://api.example.com/v1/data")
        assert result.is_valid


class TestMultipleTargets:
    def test_validate_multiple(self, validator):
        results = validator.validate_multiple(["example.com", "evil.com", "10.0.0.1"])
        assert results["example.com"].is_valid
        assert not results["evil.com"].is_valid
        assert results["10.0.0.1"].is_valid

    def test_get_allowed_values(self, validator):
        values = validator.get_allowed_values()
        assert "example.com" in values
        assert "10.0.0.1" in values
