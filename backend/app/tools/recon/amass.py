import json

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class AmassWrapper(BaseToolWrapper):
    """Wrapper for OWASP Amass subdomain enumeration."""

    @property
    def name(self) -> str:
        return "amass"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.RECON

    def is_available(self) -> bool:
        import subprocess

        try:
            subprocess.run(["amass", "-version"], capture_output=True, timeout=10)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(self, target: str, config: dict) -> list[str]:
        import tempfile
        default_output = f"{tempfile.gettempdir()}/amass_{target}.json"
        output_file = config.get("output_file", default_output)
        cmd = ["amass", "enum", "-passive", "-d", target, "-json", output_file]

        if config.get("active", False):
            cmd[2] = "-active"

        if "timeout" in config:
            cmd.extend(["-timeout", str(config["timeout"])])

        if config.get("brute", False):
            cmd.append("-brute")

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        subdomains: set[str] = set()

        for line in raw_output.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                name = data.get("name", "").strip()
                if name:
                    subdomains.add(name)
                    result.hosts.append({
                        "hostname": name,
                        "source": "amass",
                        "addresses": data.get("addresses", []),
                        "tag": data.get("tag", ""),
                    })
            except json.JSONDecodeError:
                subdomain = line.strip()
                if subdomain and "." in subdomain:
                    subdomains.add(subdomain)
                    result.hosts.append({"hostname": subdomain, "source": "amass"})

        for subdomain in sorted(subdomains):
            result.findings.append({
                "title": f"Subdomain discovered: {subdomain}",
                "severity": "info",
                "target_host": subdomain,
                "description": (
                    f"Subdomain {subdomain} was discovered during "
                    f"Amass enumeration of {target}"
                ),
                "source_tool": "amass",
                "raw_evidence": {"subdomain": subdomain, "parent_domain": target},
            })

        result.metadata = {
            "total_subdomains": len(subdomains),
            "parent_domain": target,
        }

        return result
