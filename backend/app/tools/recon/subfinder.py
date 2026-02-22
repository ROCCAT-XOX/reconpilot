import json

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class SubfinderWrapper(BaseToolWrapper):
    """Wrapper for ProjectDiscovery Subfinder subdomain enumeration."""

    @property
    def name(self) -> str:
        return "subfinder"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.RECON

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["subfinder", "-d", target, "-silent", "-json"]

        if "sources" in config:
            cmd.extend(["-sources", ",".join(config["sources"])])

        if "exclude_sources" in config:
            cmd.extend(["-exclude-sources", ",".join(config["exclude_sources"])])

        threads = config.get("threads", 30)
        cmd.extend(["-t", str(threads)])

        timeout = config.get("timeout", 30)
        cmd.extend(["-timeout", str(timeout)])

        if config.get("recursive", False):
            cmd.append("-recursive")

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        subdomains = set()

        for line in raw_output.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                host = data.get("host", "").strip()
                if host:
                    subdomains.add(host)
                    source = data.get("source", "unknown")
                    result.hosts.append({
                        "hostname": host,
                        "source": source,
                    })
            except json.JSONDecodeError:
                # Plain text output (one subdomain per line)
                subdomain = line.strip()
                if subdomain and "." in subdomain:
                    subdomains.add(subdomain)
                    result.hosts.append({"hostname": subdomain, "source": "subfinder"})

        for subdomain in sorted(subdomains):
            result.findings.append({
                "title": f"Subdomain discovered: {subdomain}",
                "severity": "info",
                "target_host": subdomain,
                "description": f"Subdomain {subdomain} was discovered during enumeration of {target}",
                "source_tool": "subfinder",
                "raw_evidence": {"subdomain": subdomain, "parent_domain": target},
            })

        result.metadata = {
            "total_subdomains": len(subdomains),
            "parent_domain": target,
        }

        return result
