import json

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class WhatWebWrapper(BaseToolWrapper):
    """Wrapper for WhatWeb technology fingerprinting."""

    @property
    def name(self) -> str:
        return "whatweb"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_ANALYSIS

    def is_available(self) -> bool:
        import subprocess

        try:
            subprocess.run(["whatweb", "--version"], capture_output=True, timeout=10)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["whatweb", "--color=never", "--log-json=-", target]

        aggression = config.get("aggression", 1)
        cmd.extend(["-a", str(aggression)])

        if config.get("verbose", False):
            cmd.append("-v")

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        technologies: list[dict] = []

        for line in raw_output.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            url = data.get("target", target)
            plugins = data.get("plugins", {})

            for plugin_name, plugin_data in plugins.items():
                if plugin_name in ("HTTPServer", "IP", "Country", "UncommonHeaders"):
                    continue

                version_list = plugin_data.get("version", [])
                version = version_list[0] if version_list else None
                string_list = plugin_data.get("string", [])

                tech_info = {
                    "name": plugin_name,
                    "version": version,
                    "details": string_list,
                }
                technologies.append(tech_info)

                severity = "info"
                desc = f"Technology detected: {plugin_name}"
                if version:
                    desc += f" version {version}"

                result.findings.append({
                    "title": f"Technology: {plugin_name}" + (f" {version}" if version else ""),
                    "severity": severity,
                    "target_host": url.split("//")[-1].split("/")[0] if "//" in url else target,
                    "target_url": url,
                    "description": desc,
                    "source_tool": "whatweb",
                    "raw_evidence": tech_info,
                })

        result.metadata = {
            "total_technologies": len(technologies),
            "technologies": [t["name"] for t in technologies],
        }

        return result
