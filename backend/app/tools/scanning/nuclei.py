import json
from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus

NUCLEI_SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "unknown": "info",
}


class NucleiWrapper(BaseToolWrapper):
    """Wrapper for ProjectDiscovery Nuclei vulnerability scanner."""

    @property
    def name(self) -> str:
        return "nuclei"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SCANNING

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["nuclei", "-target", target, "-jsonl", "-silent"]

        severities = config.get("severities", ["critical", "high", "medium"])
        cmd.extend(["-severity", ",".join(severities)])

        if "tags" in config:
            cmd.extend(["-tags", ",".join(config["tags"])])

        if "exclude_tags" in config:
            cmd.extend(["-exclude-tags", ",".join(config["exclude_tags"])])

        rate_limit = config.get("rate_limit", 150)
        cmd.extend(["-rate-limit", str(rate_limit)])

        concurrency = config.get("concurrency", 25)
        cmd.extend(["-concurrency", str(concurrency)])

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

        severity_counts = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0,
        }

        for line in raw_output.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            severity = NUCLEI_SEVERITY_MAP.get(
                data.get("info", {}).get("severity", "info"), "info"
            )
            severity_counts[severity] += 1

            finding = {
                "title": data.get("info", {}).get("name", "Unknown Finding"),
                "severity": severity,
                "target_host": data.get("host", target),
                "target_url": data.get("matched-at", ""),
                "description": data.get("info", {}).get("description", ""),
                "cve_id": self._extract_cve(data),
                "cwe_id": self._extract_cwe(data),
                "source_tool": "nuclei",
                "raw_evidence": {
                    "template_id": data.get("template-id", ""),
                    "template_url": data.get("template-url", ""),
                    "matcher_name": data.get("matcher-name", ""),
                    "extracted_results": data.get("extracted-results", []),
                    "curl_command": data.get("curl-command", ""),
                },
            }
            result.findings.append(finding)

        result.metadata = {
            "total_findings": len(result.findings),
            "severity_counts": severity_counts,
        }

        return result

    def _extract_cve(self, data: dict) -> str | None:
        classification = data.get("info", {}).get("classification", {})
        cve_ids = classification.get("cve-id", [])
        if cve_ids and isinstance(cve_ids, list):
            return cve_ids[0]
        return None

    def _extract_cwe(self, data: dict) -> str | None:
        classification = data.get("info", {}).get("classification", {})
        cwe_ids = classification.get("cwe-id", [])
        if cwe_ids and isinstance(cwe_ids, list):
            return cwe_ids[0]
        return None
