import json
from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class HttpxWrapper(BaseToolWrapper):
    """Wrapper for ProjectDiscovery httpx HTTP probing tool."""

    @property
    def name(self) -> str:
        return "httpx"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.RECON

    def is_available(self) -> bool:
        import subprocess
        try:
            subprocess.run(["httpx", "-version"], capture_output=True, timeout=10)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["httpx", "-u", target, "-silent", "-json"]

        if config.get("tech_detect", True):
            cmd.append("-tech-detect")

        if config.get("status_code", True):
            cmd.append("-status-code")

        if config.get("title", True):
            cmd.append("-title")

        if config.get("web_server", True):
            cmd.append("-web-server")

        if config.get("follow_redirects", True):
            cmd.extend(["-follow-redirects"])

        threads = config.get("threads", 50)
        cmd.extend(["-threads", str(threads)])

        timeout = config.get("timeout", 10)
        cmd.extend(["-timeout", str(timeout)])

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        for line in raw_output.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            url = data.get("url", "")
            status_code = data.get("status_code", 0)
            title = data.get("title", "")
            web_server = data.get("webserver", "")
            tech = data.get("tech", [])
            content_length = data.get("content_length", 0)
            host = data.get("host", target)

            host_data = {
                "url": url,
                "status_code": status_code,
                "title": title,
                "web_server": web_server,
                "technologies": tech,
                "content_length": content_length,
            }
            result.hosts.append(host_data)

            result.findings.append({
                "title": f"HTTP service: {url} [{status_code}] {title}",
                "severity": "info",
                "target_host": host,
                "target_url": url,
                "description": (
                    f"HTTP service found at {url} "
                    f"(Status: {status_code}, Server: {web_server}, "
                    f"Title: {title})"
                ),
                "source_tool": "httpx",
                "raw_evidence": host_data,
            })

            # Flag interesting technologies
            for t in tech:
                t_lower = t.lower()
                if any(k in t_lower for k in ["wordpress", "joomla", "drupal"]):
                    result.findings.append({
                        "title": f"CMS detected: {t} on {url}",
                        "severity": "info",
                        "target_host": host,
                        "target_url": url,
                        "description": f"Content Management System {t} detected at {url}",
                        "source_tool": "httpx",
                        "raw_evidence": {"technology": t, "url": url},
                    })

        result.metadata = {
            "total_urls": len(result.hosts),
            "technologies_found": list(set(
                t for h in result.hosts for t in h.get("technologies", [])
            )),
        }

        return result
