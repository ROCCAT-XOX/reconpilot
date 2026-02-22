import json
from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class NiktoWrapper(BaseToolWrapper):
    """Wrapper for Nikto web server scanner."""

    @property
    def name(self) -> str:
        return "nikto"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SCANNING

    def is_available(self) -> bool:
        import subprocess
        try:
            subprocess.run(["nikto", "-Version"], capture_output=True, timeout=10)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["nikto", "-h", target, "-Format", "json", "-output", "-"]

        if config.get("ssl", False) or target.startswith("https"):
            cmd.append("-ssl")

        if "port" in config:
            cmd.extend(["-p", str(config["port"])])

        if config.get("tuning"):
            cmd.extend(["-Tuning", config["tuning"]])

        if config.get("no_404", True):
            cmd.append("-no404")

        timeout = config.get("timeout", 10)
        cmd.extend(["-timeout", str(timeout)])

        if config.get("maxtime"):
            cmd.extend(["-maxtime", str(config["maxtime"])])

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # Try to parse line-by-line for older nikto versions
            self._parse_text_output(raw_output, target, result)
            return result

        # Nikto JSON can be a list or dict
        hosts = data if isinstance(data, list) else [data]

        for host_data in hosts:
            vulnerabilities = host_data.get("vulnerabilities", [])
            for vuln in vulnerabilities:
                osvdb_id = vuln.get("OSVDB", "0")
                method = vuln.get("method", "GET")
                url = vuln.get("url", "/")
                msg = vuln.get("msg", "")

                severity = "info"
                msg_lower = msg.lower()
                if any(k in msg_lower for k in ["sql injection", "xss", "remote code"]):
                    severity = "high"
                elif any(k in msg_lower for k in ["directory listing", "default file", "backup"]):
                    severity = "medium"
                elif any(k in msg_lower for k in ["header", "cookie", "version"]):
                    severity = "low"

                full_url = f"{target.rstrip('/')}{url}"

                result.findings.append({
                    "title": f"Nikto: {msg[:100]}",
                    "severity": severity,
                    "target_host": target.split("//")[-1].split("/")[0] if "//" in target else target,
                    "target_url": full_url,
                    "description": msg,
                    "source_tool": "nikto",
                    "raw_evidence": {
                        "osvdb": osvdb_id,
                        "method": method,
                        "url": url,
                        "message": msg,
                    },
                })

        result.metadata = {
            "total_findings": len(result.findings),
        }

        return result

    def _parse_text_output(self, raw_output: str, target: str, result: ToolResult):
        """Fallback parser for text-based nikto output."""
        for line in raw_output.split("\n"):
            line = line.strip()
            if line.startswith("+ ") and ":" in line:
                msg = line[2:]
                result.findings.append({
                    "title": f"Nikto: {msg[:100]}",
                    "severity": "info",
                    "target_host": target,
                    "target_url": target,
                    "description": msg,
                    "source_tool": "nikto",
                    "raw_evidence": {"raw_line": line},
                })
