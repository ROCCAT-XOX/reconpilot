from dataclasses import dataclass
from typing import Callable
import logging

from app.tools.base import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ChainRule:
    """A chaining rule: condition met → action triggered."""
    name: str
    source_tool: str
    condition: Callable[[ToolResult], bool]
    action: Callable[[ToolResult, dict], dict[str, set]]
    description: str = ""


class ChainLogicEngine:
    """
    Evaluates scan results and triggers follow-up actions automatically.

    Examples:
    - nmap finds port 80/443 → nikto + nuclei
    - subfinder finds subdomains → add to scan targets
    - httpx detects WordPress → flag for wpscan
    - ffuf finds login pages → flag for auth testing
    """

    def __init__(self):
        self.rules: list[ChainRule] = []
        self._register_default_rules()

    def _register_default_rules(self):
        # Rule 1: Subdomains found → add to targets
        self.rules.append(ChainRule(
            name="subdomain_to_targets",
            source_tool="subfinder",
            condition=lambda result: len(result.hosts) > 0,
            action=self._action_add_subdomains,
            description="Discovered subdomains added as new scan targets",
        ))

        # Rule 2: Web servers found → create URLs
        self.rules.append(ChainRule(
            name="webserver_to_urls",
            source_tool="nmap",
            condition=lambda result: any(
                p.get("service") in ("http", "https", "http-proxy")
                for h in result.hosts
                for p in h.get("ports", [])
                if p.get("state") == "open"
            ),
            action=self._action_create_urls_from_nmap,
            description="Open web ports converted to URLs for web scanners",
        ))

        # Rule 3: httpx detects WordPress
        self.rules.append(ChainRule(
            name="wordpress_detected",
            source_tool="httpx",
            condition=lambda result: any(
                "wordpress" in str(f.get("raw_evidence", {})).lower()
                for f in result.findings
            ),
            action=self._action_flag_wordpress,
            description="WordPress detected → WPScan target flagged",
        ))

        # Rule 4: Login pages found
        self.rules.append(ChainRule(
            name="login_page_found",
            source_tool="ffuf",
            condition=lambda result: any(
                any(keyword in f.get("title", "").lower()
                    for keyword in ["login", "admin", "signin", "auth"])
                for f in result.findings
            ),
            action=self._action_flag_login_pages,
            description="Login pages found → auth testing targets",
        ))

        # Rule 5: httpx finds live URLs → add to URL targets
        self.rules.append(ChainRule(
            name="httpx_urls_to_targets",
            source_tool="httpx",
            condition=lambda result: len(result.hosts) > 0,
            action=self._action_add_httpx_urls,
            description="Live URLs from httpx added as scan targets",
        ))

    async def evaluate(
        self,
        result: ToolResult,
        discovered_targets: dict[str, set],
    ) -> dict[str, set]:
        """Evaluate a tool result against all matching rules."""
        new_targets: dict[str, set] = {}

        for rule in self.rules:
            if rule.source_tool != result.tool_name:
                continue

            try:
                if rule.condition(result):
                    action_targets = rule.action(result, discovered_targets)
                    for target_type, values in action_targets.items():
                        new_targets.setdefault(target_type, set()).update(values)
                    logger.info(
                        f"Chain rule '{rule.name}' triggered: "
                        f"added {sum(len(v) for v in action_targets.values())} new targets"
                    )
            except Exception as e:
                logger.error(f"Chain rule '{rule.name}' failed: {e}")

        return new_targets

    # === Action Methods ===

    def _action_add_subdomains(self, result: ToolResult, discovered: dict) -> dict[str, set]:
        new_domains = set()
        for host in result.hosts:
            if hostname := host.get("hostname"):
                new_domains.add(hostname)
        for finding in result.findings:
            if target := finding.get("target_host"):
                new_domains.add(target)
        return {"domains": new_domains}

    def _action_create_urls_from_nmap(self, result: ToolResult, discovered: dict) -> dict[str, set]:
        urls = set()
        for host in result.hosts:
            ip = host.get("ip", "")
            for port in host.get("ports", []):
                if port.get("state") != "open":
                    continue
                service = port.get("service", "")
                port_num = port.get("port", 0)

                if service in ("https", "ssl/http") or port_num == 443:
                    urls.add(f"https://{ip}:{port_num}")
                elif service in ("http", "http-proxy") or port_num in (80, 8080, 8443):
                    urls.add(f"http://{ip}:{port_num}")
        return {"urls": urls}

    def _action_flag_wordpress(self, result: ToolResult, discovered: dict) -> dict[str, set]:
        wp_urls = set()
        for finding in result.findings:
            if "wordpress" in str(finding.get("raw_evidence", {})).lower():
                if url := finding.get("target_url"):
                    wp_urls.add(url)
        return {"wordpress_targets": wp_urls}

    def _action_flag_login_pages(self, result: ToolResult, discovered: dict) -> dict[str, set]:
        login_urls = set()
        for finding in result.findings:
            if url := finding.get("target_url"):
                login_urls.add(url)
        return {"login_targets": login_urls}

    def _action_add_httpx_urls(self, result: ToolResult, discovered: dict) -> dict[str, set]:
        urls = set()
        for host in result.hosts:
            if url := host.get("url"):
                urls.add(url)
        return {"urls": urls}
