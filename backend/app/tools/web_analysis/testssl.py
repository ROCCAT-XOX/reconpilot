import json

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class TestsslWrapper(BaseToolWrapper):
    """Wrapper for testssl.sh TLS/SSL testing."""

    @property
    def name(self) -> str:
        return "testssl"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_ANALYSIS

    def is_available(self) -> bool:
        import subprocess

        try:
            subprocess.run(
                ["testssl", "--help"], capture_output=True, timeout=10
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["testssl", "--jsonfile=-", "--quiet"]

        if config.get("full", False):
            cmd.append("--full")

        if config.get("starttls"):
            cmd.extend(["--starttls", config["starttls"]])

        if config.get("sneaky", False):
            cmd.append("--sneaky")

        cmd.append(target)
        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        if ":" in target and not target.startswith("http"):
            host = target.split(":")[0]
        elif "//" in target:
            host = target.split("//")[-1].split("/")[0].split(":")[0]
        else:
            host = target

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # testssl may output array or single object
            try:
                # Try to find JSON array in output
                start = raw_output.find("[")
                end = raw_output.rfind("]") + 1
                if start >= 0 and end > start:
                    data = json.loads(raw_output[start:end])
                else:
                    result.errors.append("Failed to parse testssl output")
                    return result
            except json.JSONDecodeError:
                result.errors.append("Failed to parse testssl JSON output")
                return result

        entries = data if isinstance(data, list) else [data]

        severity_map = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
            "OK": "info",
            "INFO": "info",
        }

        for entry in entries:
            entry_id = entry.get("id", "")
            finding_text = entry.get("finding", "")
            entry_severity = entry.get("severity", "INFO").upper()
            cve = entry.get("cve", "")

            if entry_severity in ("OK", "INFO") and not cve:
                continue

            severity = severity_map.get(entry_severity, "info")

            title = f"SSL/TLS: {entry_id}"
            if cve:
                title += f" ({cve})"

            result.findings.append({
                "title": title,
                "severity": severity,
                "target_host": host,
                "description": finding_text,
                "source_tool": "testssl",
                "cve_id": cve if cve else None,
                "raw_evidence": {
                    "id": entry_id,
                    "finding": finding_text,
                    "severity": entry_severity,
                    "cve": cve,
                    "ip": entry.get("ip", ""),
                    "port": entry.get("port", ""),
                },
            })

        result.metadata = {
            "total_findings": len(result.findings),
            "target": target,
        }

        return result
