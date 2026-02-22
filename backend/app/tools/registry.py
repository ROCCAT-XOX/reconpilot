from app.tools.base import BaseToolWrapper, ToolCategory
from app.tools.scanning.nmap import NmapWrapper
from app.tools.scanning.nuclei import NucleiWrapper
from app.tools.scanning.ffuf import FfufWrapper
from app.tools.scanning.nikto import NiktoWrapper
from app.tools.recon.subfinder import SubfinderWrapper
from app.tools.recon.httpx import HttpxWrapper
from app.tools.web_analysis.sslyze import SSLyzeWrapper
from app.tools.exploitation.sqlmap import SqlmapWrapper


class ToolRegistry:
    """Central registry for all tool wrappers."""

    def __init__(self):
        self._tools: dict[str, BaseToolWrapper] = {}

    def register(self, wrapper: BaseToolWrapper) -> None:
        self._tools[wrapper.name] = wrapper

    def get(self, name: str) -> BaseToolWrapper | None:
        return self._tools.get(name)

    def get_all(self) -> dict[str, BaseToolWrapper]:
        return self._tools.copy()

    def get_available(self) -> dict[str, BaseToolWrapper]:
        return {
            name: tool for name, tool in self._tools.items()
            if tool.is_available()
        }

    def get_by_category(self, category: str) -> list[BaseToolWrapper]:
        return [
            tool for tool in self._tools.values()
            if tool.category.value == category
        ]

    def list_tools(self) -> list[dict]:
        """Return tool info for the API."""
        return [
            {
                "name": tool.name,
                "category": tool.category.value,
                "available": tool.is_available(),
            }
            for tool in self._tools.values()
        ]


def create_tool_registry() -> ToolRegistry:
    """Factory function to create a fully populated tool registry."""
    registry = ToolRegistry()

    # Wave 1 — Core pipeline
    registry.register(NmapWrapper())
    registry.register(NucleiWrapper())
    registry.register(SubfinderWrapper())
    registry.register(HttpxWrapper())
    registry.register(FfufWrapper())
    registry.register(SSLyzeWrapper())
    registry.register(NiktoWrapper())
    registry.register(SqlmapWrapper())

    return registry


# Global singleton
tool_registry = create_tool_registry()
