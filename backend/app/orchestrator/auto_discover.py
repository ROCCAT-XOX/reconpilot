"""Auto-discovery service for pre-scan target enrichment.

When scan config includes auto_discover options, this service runs
additional tools before the main scan to enrich the target list.
"""

import logging
from dataclasses import dataclass

from app.tools.base import ToolResult, ToolStatus
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class AutoDiscoverConfig:
    """Configuration for auto-discovery."""
    subdomains: bool = False
    technologies: bool = False
    ports: bool = False


@dataclass
class AutoDiscoverResult:
    """Results from auto-discovery phase."""
    subdomains: set[str]
    urls: set[str]
    hosts: set[str]
    technologies: dict[str, list[str]]  # url -> [tech1, tech2, ...]
    full_port_scan: bool

    @classmethod
    def empty(cls) -> "AutoDiscoverResult":
        return cls(
            subdomains=set(),
            urls=set(),
            hosts=set(),
            technologies={},
            full_port_scan=False,
        )


class AutoDiscoverService:
    """Runs pre-scan auto-discovery based on scan configuration."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tools = tool_registry

    def parse_config(self, scan_config: dict) -> AutoDiscoverConfig:
        """Extract auto_discover settings from scan config."""
        ad = scan_config.get("auto_discover", {})
        return AutoDiscoverConfig(
            subdomains=ad.get("subdomains", False),
            technologies=ad.get("technologies", False),
            ports=ad.get("ports", False),
        )

    async def run(
        self,
        targets: list[str],
        config: AutoDiscoverConfig,
        scope_targets: list[str] | None = None,
    ) -> AutoDiscoverResult:
        """Execute auto-discovery and return enriched target data."""
        result = AutoDiscoverResult.empty()

        if not any([config.subdomains, config.technologies, config.ports]):
            return result

        # Step 1: Subdomain discovery
        if config.subdomains:
            logger.info("Auto-discover: running subdomain enumeration")
            discovered = await self._discover_subdomains(targets, scope_targets)
            result.subdomains = discovered
            logger.info(
                "Auto-discover: found %d subdomains", len(discovered)
            )

        # Step 2: HTTP probing on all known targets
        all_targets = list(set(targets) | result.subdomains)
        if config.technologies or config.subdomains:
            logger.info("Auto-discover: running HTTP probing on %d targets", len(all_targets))
            urls, hosts = await self._probe_http(all_targets, scope_targets)
            result.urls = urls
            result.hosts = hosts

        # Step 3: Technology detection
        if config.technologies and result.urls:
            logger.info("Auto-discover: running technology detection on %d URLs", len(result.urls))
            result.technologies = await self._detect_technologies(
                list(result.urls), scope_targets
            )

        # Step 4: Flag full port scan
        if config.ports:
            result.full_port_scan = True
            logger.info("Auto-discover: full port scan enabled (-p-)")

        return result

    async def _discover_subdomains(
        self, targets: list[str], scope_targets: list[str] | None
    ) -> set[str]:
        """Run subfinder against all targets."""
        subdomains: set[str] = set()
        subfinder = self.tools.get("subfinder")
        if subfinder is None:
            logger.warning("Auto-discover: subfinder not available, skipping subdomain discovery")
            return subdomains

        for target in targets:
            tool_result: ToolResult = await subfinder.run(
                target=target,
                config={"threads": 30, "timeout": 30},
                scope_targets=scope_targets,
            )
            if tool_result.status == ToolStatus.COMPLETED:
                for host in tool_result.hosts:
                    if hostname := host.get("hostname"):
                        subdomains.add(hostname)

        return subdomains

    async def _probe_http(
        self, targets: list[str], scope_targets: list[str] | None
    ) -> tuple[set[str], set[str]]:
        """Run httpx to find live HTTP services."""
        urls: set[str] = set()
        hosts: set[str] = set()
        httpx = self.tools.get("httpx")
        if httpx is None:
            logger.warning("Auto-discover: httpx not available, skipping HTTP probing")
            return urls, hosts

        for target in targets:
            tool_result = await httpx.run(
                target=target,
                config={"tech_detect": True, "threads": 50},
                scope_targets=scope_targets,
            )
            if tool_result.status == ToolStatus.COMPLETED:
                for host in tool_result.hosts:
                    if url := host.get("url"):
                        urls.add(url)
                hosts.add(target)

        return urls, hosts

    async def _detect_technologies(
        self, urls: list[str], scope_targets: list[str] | None
    ) -> dict[str, list[str]]:
        """Run whatweb for technology detection."""
        technologies: dict[str, list[str]] = {}
        whatweb = self.tools.get("whatweb")
        if whatweb is None:
            logger.warning("Auto-discover: whatweb not available, skipping tech detection")
            return technologies

        for url in urls:
            tool_result = await whatweb.run(
                target=url,
                config={"aggression": 1},
                scope_targets=scope_targets,
            )
            if tool_result.status == ToolStatus.COMPLETED:
                techs = tool_result.metadata.get("technologies", [])
                if techs:
                    technologies[url] = techs

        return technologies
