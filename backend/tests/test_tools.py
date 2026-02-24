"""Tests for tool registry and profiles."""

from httpx import AsyncClient

from app.models.user import User
from app.orchestrator.profiles import get_profile, list_profiles
from app.tools.registry import tool_registry
from tests.conftest import auth_header


class TestToolRegistry:
    def test_registry_has_tools(self):
        tools = tool_registry.list_tools()
        assert len(tools) >= 10
        names = [t["name"] for t in tools]
        assert "nmap" in names
        assert "nuclei" in names
        assert "subfinder" in names

    def test_get_tool(self):
        nmap = tool_registry.get("nmap")
        assert nmap is not None
        assert nmap.name == "nmap"

    def test_get_nonexistent_tool(self):
        assert tool_registry.get("nonexistent") is None

    def test_get_by_category(self):
        scanning_tools = tool_registry.get_by_category("scanning")
        assert len(scanning_tools) >= 1


class TestProfiles:
    def test_list_profiles(self):
        profiles = list_profiles()
        assert len(profiles) >= 3
        names = [p["key"] for p in profiles]
        assert "quick" in names
        assert "standard" in names
        assert "deep" in names

    def test_get_profile(self):
        profile = get_profile("quick")
        assert profile is not None
        assert profile.name == "Quick Recon"
        assert len(profile.phases) >= 2

    def test_get_nonexistent_profile(self):
        assert get_profile("nonexistent") is None

    def test_profile_has_tools(self):
        profile = get_profile("standard")
        all_tools = [t.tool_name for phase in profile.phases for t in phase.tools]
        assert "subfinder" in all_tools
        assert "nmap" in all_tools


class TestToolsAPI:
    async def test_list_tools_api(self, client: AsyncClient, test_user: User):
        resp = await client.get("/api/v1/scans/tools/available", headers=auth_header(test_user))
        assert resp.status_code == 200
        assert len(resp.json()) >= 10

    async def test_list_profiles_api(self, client: AsyncClient, test_user: User):
        resp = await client.get("/api/v1/scans/profiles/available", headers=auth_header(test_user))
        assert resp.status_code == 200
        keys = [p["key"] for p in resp.json()]
        assert "quick" in keys
