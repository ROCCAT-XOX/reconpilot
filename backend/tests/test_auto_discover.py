"""Tests for auto-discovery service."""

from unittest.mock import patch

import pytest

from app.orchestrator.auto_discover import (
    AutoDiscoverConfig,
    AutoDiscoverResult,
    AutoDiscoverService,
)
from app.tools.base import ToolResult, ToolStatus
from app.tools.registry import create_tool_registry


class TestAutoDiscoverConfig:
    def test_parse_config_empty(self):
        svc = AutoDiscoverService(create_tool_registry())
        config = svc.parse_config({})
        assert config.subdomains is False
        assert config.technologies is False
        assert config.ports is False

    def test_parse_config_all_enabled(self):
        svc = AutoDiscoverService(create_tool_registry())
        config = svc.parse_config({
            "auto_discover": {
                "subdomains": True,
                "technologies": True,
                "ports": True,
            }
        })
        assert config.subdomains is True
        assert config.technologies is True
        assert config.ports is True


class TestAutoDiscoverResult:
    def test_empty(self):
        r = AutoDiscoverResult.empty()
        assert len(r.subdomains) == 0
        assert len(r.urls) == 0
        assert r.full_port_scan is False


class TestAutoDiscoverService:
    @pytest.fixture
    def registry(self):
        return create_tool_registry()

    @pytest.fixture
    def service(self, registry):
        return AutoDiscoverService(registry)

    async def test_run_no_options(self, service):
        config = AutoDiscoverConfig()
        result = await service.run(["example.com"], config)
        assert len(result.subdomains) == 0

    async def test_run_subdomains(self, service):
        subfinder_result = ToolResult(
            tool_name="subfinder",
            target="example.com",
            status=ToolStatus.COMPLETED,
            hosts=[
                {"hostname": "api.example.com"},
                {"hostname": "www.example.com"},
            ],
        )
        httpx_result = ToolResult(
            tool_name="httpx",
            target="api.example.com",
            status=ToolStatus.COMPLETED,
            hosts=[{"url": "https://api.example.com"}],
        )

        with (
            patch.object(service.tools.get("subfinder"), "run", return_value=subfinder_result),
            patch.object(service.tools.get("httpx"), "run", return_value=httpx_result),
        ):
            config = AutoDiscoverConfig(subdomains=True)
            result = await service.run(["example.com"], config)

        assert "api.example.com" in result.subdomains
        assert "www.example.com" in result.subdomains

    async def test_run_ports_flag(self, service):
        config = AutoDiscoverConfig(ports=True)
        result = await service.run(["example.com"], config)
        assert result.full_port_scan is True

    async def test_run_technologies(self, service):
        httpx_result = ToolResult(
            tool_name="httpx", target="example.com", status=ToolStatus.COMPLETED,
            hosts=[{"url": "https://example.com"}],
        )
        whatweb_result = ToolResult(
            tool_name="whatweb", target="https://example.com", status=ToolStatus.COMPLETED,
            metadata={"technologies": ["Nginx", "PHP"]},
        )

        with (
            patch.object(service.tools.get("httpx"), "run", return_value=httpx_result),
            patch.object(service.tools.get("whatweb"), "run", return_value=whatweb_result),
        ):
            config = AutoDiscoverConfig(technologies=True)
            result = await service.run(["example.com"], config)

        assert "https://example.com" in result.technologies
        assert "Nginx" in result.technologies["https://example.com"]
