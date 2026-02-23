import re

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class GobusterWrapper(BaseToolWrapper):
    """Wrapper for Gobuster directory brute-forcing."""

    @property
    def name(self) -> str:
        return "gobuster"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SCANNING

    def is_available(self) -> bool:
        import subprocess

        try:
            subprocess.run(["gobuster", "version"], capture_output=True, timeout=10)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(self, target: str, config: dict) -> list[str]:
        wordlist = config.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        cmd = [
            "gobuster", "dir",
            "-u", target,
            "-w", wordlist,
            "--no-color",
            "-q",
        ]

        if "extensions" in config:
            cmd.extend(["-x", ",".join(config["extensions"])])

        if "status_codes" in config:
            cmd.extend(["-s", config["status_codes"]])

        threads = config.get("threads", 10)
        cmd.extend(["-t", str(threads)])

        if config.get("follow_redirect", False):
            cmd.append("-r")

        if "timeout" in config:
            cmd.extend(["--timeout", f"{config['timeout']}s"])

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        # Gobuster output format: /path (Status: 200) [Size: 1234]
        pattern = re.compile(
            r"^(/\S*)\s+\(Status:\s*(\d+)\)\s+\[Size:\s*(\d+)\]"
        )

        for line in raw_output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if not match:
                continue

            path = match.group(1)
            status_code = int(match.group(2))
            size = int(match.group(3))
            full_url = f"{target.rstrip('/')}{path}"

            severity = "info"
            if status_code == 200:
                severity = "low"
            path_lower = path.lower()
            if any(kw in path_lower for kw in [
                "admin", "login", "dashboard", "config", "backup",
                ".env", "wp-admin", "phpmyadmin", ".git",
            ]):
                severity = "medium"

            result.findings.append({
                "title": f"Directory/file found: {path} [{status_code}]",
                "severity": severity,
                "target_host": target.split("//")[-1].split("/")[0] if "//" in target else target,
                "target_url": full_url,
                "description": (
                    f"Found {full_url} (Status: {status_code}, Size: {size} bytes)"
                ),
                "source_tool": "gobuster",
                "raw_evidence": {
                    "path": path,
                    "status": status_code,
                    "size": size,
                    "url": full_url,
                },
            })

        result.metadata = {
            "total_results": len(result.findings),
            "target_url": target,
        }

        return result
