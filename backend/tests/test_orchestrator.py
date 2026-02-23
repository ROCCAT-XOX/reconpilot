"""Tests for orchestrator: chain logic, pipeline engine, scope enforcement."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.chain_logic import ChainLogicEngine
from app.orchestrator.engine import PipelineEngine, ScopeViolationError
from app.orchestrator.profiles import get_profile
from app.services.scope_validator import ScopeValidator
from app.tools.base import ToolResult, ToolStatus


class TestChainLogic:
    @pytest.fixture
    def chain_engine(self):
        return ChainLogicEngine()

    async def test_subdomain_chain_rule(self, chain_engine):
        result = ToolResult(
            tool_name="subfinder",
            target="example.com",
            status=ToolStatus.COMPLETED,
            hosts=[{"hostname": "api.example.com"}, {"hostname": "admin.example.com"}],
        )
        new_targets = await chain_engine.evaluate(result, {"domains": set()})
        assert "domains" in new_targets
        assert "api.example.com" in new_targets["domains"]

    async def test_nmap_web_chain_rule(self, chain_engine):
        result = ToolResult(
            tool_name="nmap",
            target="10.0.0.1",
            status=ToolStatus.COMPLETED,
            hosts=[{
                "ip": "10.0.0.1",
                "ports": [{"port": 443, "state": "open", "service": "https"}],
            }],
        )
        new_targets = await chain_engine.evaluate(result, {"domains": set()})
        assert "urls" in new_targets
        assert "https://10.0.0.1:443" in new_targets["urls"]

    async def test_no_rule_match(self, chain_engine):
        result = ToolResult(
            tool_name="unknown_tool",
            target="example.com",
            status=ToolStatus.COMPLETED,
        )
        new_targets = await chain_engine.evaluate(result, {})
        assert new_targets == {}

    async def test_httpx_url_chain(self, chain_engine):
        result = ToolResult(
            tool_name="httpx",
            target="example.com",
            status=ToolStatus.COMPLETED,
            hosts=[{"url": "https://example.com"}, {"url": "https://api.example.com"}],
        )
        new_targets = await chain_engine.evaluate(result, {"domains": set()})
        assert "urls" in new_targets
        assert "https://example.com" in new_targets["urls"]


class TestScopeEnforcement:
    def test_scope_blocks_out_of_scope_target(self):
        with pytest.raises(ScopeViolationError, match="outside the authorized scope"):
            PipelineEngine._enforce_scope(
                targets=["evil.com"],
                scope_targets=["example.com"],
            )

    def test_scope_allows_in_scope_target(self):
        # Should not raise
        PipelineEngine._enforce_scope(
            targets=["sub.example.com"],
            scope_targets=["example.com"],
        )

    def test_scope_blocks_without_scope(self):
        with pytest.raises(ScopeViolationError, match="No scope defined"):
            PipelineEngine._enforce_scope(
                targets=["example.com"],
                scope_targets=[],
            )

    def test_scope_allows_ip_in_range(self):
        PipelineEngine._enforce_scope(
            targets=["10.0.0.5"],
            scope_targets=["10.0.0.0/24"],
        )

    def test_scope_blocks_ip_outside_range(self):
        with pytest.raises(ScopeViolationError):
            PipelineEngine._enforce_scope(
                targets=["192.168.1.1"],
                scope_targets=["10.0.0.0/24"],
            )


class TestScopeValidator:
    def test_domain_match(self):
        v = ScopeValidator(allowed_targets=[{"type": "domain", "value": "example.com"}])
        assert v.validate("example.com").is_valid is True
        assert v.validate("sub.example.com").is_valid is True
        assert v.validate("evil.com").is_valid is False

    def test_ip_match(self):
        v = ScopeValidator(allowed_targets=[{"type": "ip", "value": "10.0.0.1"}])
        assert v.validate("10.0.0.1").is_valid is True
        assert v.validate("10.0.0.2").is_valid is False

    def test_ip_range_match(self):
        v = ScopeValidator(allowed_targets=[{"type": "ip_range", "value": "10.0.0.0/24"}])
        assert v.validate("10.0.0.100").is_valid is True
        assert v.validate("10.0.1.1").is_valid is False

    def test_exclusion(self):
        v = ScopeValidator(
            allowed_targets=[{"type": "domain", "value": "example.com"}],
            excluded_targets=[{"type": "domain", "value": "admin.example.com"}],
        )
        assert v.validate("www.example.com").is_valid is True
        assert v.validate("admin.example.com").is_valid is False

    def test_validate_multiple(self):
        v = ScopeValidator(allowed_targets=[{"type": "domain", "value": "example.com"}])
        results = v.validate_multiple(["example.com", "evil.com"])
        assert results["example.com"].is_valid is True
        assert results["evil.com"].is_valid is False
