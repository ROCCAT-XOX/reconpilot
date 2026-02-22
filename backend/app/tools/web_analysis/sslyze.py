import logging
import time
from datetime import UTC

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class SSLyzeWrapper(BaseToolWrapper):
    """
    Wrapper for SSLyze SSL/TLS scanner.
    Uses Python API directly — no subprocess needed.
    """

    @property
    def name(self) -> str:
        return "sslyze"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_ANALYSIS

    def build_command(self, target: str, config: dict) -> list[str]:
        return []  # Not used — SSLyze uses Python API

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        return ToolResult(tool_name=self.name, target=target, status=ToolStatus.COMPLETED)

    def is_available(self) -> bool:
        try:
            import sslyze  # noqa: F401
            return True
        except ImportError:
            return False

    async def run(
        self,
        target: str,
        config: dict | None = None,
        timeout: int = 300,
        scope_targets: list[str] | None = None,
    ) -> ToolResult:
        config = config or {}
        start_time = time.time()
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
        )

        try:
            from sslyze import (
                ScanCommand,
                Scanner,
                ServerNetworkLocation,
                ServerScanRequest,
            )

            if ":" in target:
                host, port_str = target.rsplit(":", 1)
                port = int(port_str)
            else:
                host = target
                port = 443

            location = ServerNetworkLocation(hostname=host, port=port)
            scan_request = ServerScanRequest(
                server_location=location,
                scan_commands={
                    ScanCommand.CERTIFICATE_INFO,
                    ScanCommand.SSL_2_0_CIPHER_SUITES,
                    ScanCommand.SSL_3_0_CIPHER_SUITES,
                    ScanCommand.TLS_1_0_CIPHER_SUITES,
                    ScanCommand.TLS_1_1_CIPHER_SUITES,
                    ScanCommand.TLS_1_2_CIPHER_SUITES,
                    ScanCommand.TLS_1_3_CIPHER_SUITES,
                    ScanCommand.HEARTBLEED,
                    ScanCommand.TLS_COMPRESSION,
                    ScanCommand.TLS_FALLBACK_SCSV,
                },
            )

            scanner = Scanner()
            scanner.queue_scans([scan_request])

            for scan_result in scanner.get_results():
                # Check deprecated protocols
                deprecated_checks = [
                    ("SSLv2", "ssl_2_0_cipher_suites", "high"),
                    ("SSLv3", "ssl_3_0_cipher_suites", "high"),
                    ("TLSv1.0", "tls_1_0_cipher_suites", "medium"),
                    ("TLSv1.1", "tls_1_1_cipher_suites", "medium"),
                ]

                for proto_name, attr_name, severity in deprecated_checks:
                    proto_result = getattr(scan_result.scan_result, attr_name, None)
                    if proto_result and proto_result.result:
                        accepted = proto_result.result.accepted_cipher_suites
                        if accepted:
                            result.findings.append({
                                "title": f"Deprecated protocol {proto_name} enabled",
                                "severity": severity,
                                "target_host": host,
                                "target_port": port,
                                "description": (
                                    f"{proto_name} is enabled with {len(accepted)} cipher suites. "
                                    f"This protocol is deprecated and insecure."
                                ),
                                "source_tool": "sslyze",
                                "raw_evidence": {
                                    "protocol": proto_name,
                                    "accepted_ciphers": [c.cipher_suite.name for c in accepted],
                                },
                            })

                # Heartbleed check
                heartbleed = getattr(scan_result.scan_result, "heartbleed", None)
                if heartbleed and heartbleed.result:
                    if heartbleed.result.is_vulnerable_to_heartbleed:
                        result.findings.append({
                            "title": "Vulnerable to Heartbleed (CVE-2014-0160)",
                            "severity": "critical",
                            "cve_id": "CVE-2014-0160",
                            "target_host": host,
                            "target_port": port,
                            "description": (
                                "The server is vulnerable to the Heartbleed bug, "
                                "which allows remote attackers to read memory contents."
                            ),
                            "source_tool": "sslyze",
                        })

                # Certificate info
                cert_info = getattr(scan_result.scan_result, "certificate_info", None)
                if cert_info and cert_info.result:
                    for deployment in cert_info.result.certificate_deployments:
                        leaf_cert = deployment.received_certificate_chain[0]
                        not_after = leaf_cert.not_valid_after_utc

                        from datetime import datetime
                        days_until_expiry = (not_after - datetime.now(UTC)).days

                        if days_until_expiry < 0:
                            result.findings.append({
                                "title": "SSL/TLS certificate has expired",
                                "severity": "high",
                                "target_host": host,
                                "target_port": port,
                                "description": (
                                    f"Certificate expired {abs(days_until_expiry)} "
                                    f"days ago on {not_after.isoformat()}"
                                ),
                                "source_tool": "sslyze",
                            })
                        elif days_until_expiry < 30:
                            result.findings.append({
                                "title": "SSL/TLS certificate expiring soon",
                                "severity": "medium",
                                "target_host": host,
                                "target_port": port,
                                "description": (
                                    f"Certificate expires in {days_until_expiry} days "
                                    f"on {not_after.isoformat()}"
                                ),
                                "source_tool": "sslyze",
                            })

                # TLS 1.2 cipher suite analysis
                tls12 = getattr(scan_result.scan_result, "tls_1_2_cipher_suites", None)
                if tls12 and tls12.result:
                    weak_ciphers = []
                    for cipher in tls12.result.accepted_cipher_suites:
                        name = cipher.cipher_suite.name
                        if any(w in name for w in ["RC4", "DES", "NULL", "EXPORT", "anon"]):
                            weak_ciphers.append(name)
                    if weak_ciphers:
                        result.findings.append({
                            "title": "Weak TLS cipher suites accepted",
                            "severity": "medium",
                            "target_host": host,
                            "target_port": port,
                            "description": (
                                f"The server accepts {len(weak_ciphers)} weak cipher suites: "
                                f"{', '.join(weak_ciphers[:5])}"
                            ),
                            "source_tool": "sslyze",
                            "raw_evidence": {"weak_ciphers": weak_ciphers},
                        })

        except Exception as e:
            result.status = ToolStatus.FAILED
            result.errors.append(str(e))

        result.duration_seconds = time.time() - start_time
        result.metadata = {"total_findings": len(result.findings)}
        return result
