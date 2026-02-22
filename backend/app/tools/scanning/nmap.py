import xml.etree.ElementTree as ET
from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class NmapWrapper(BaseToolWrapper):
    """Wrapper for nmap network scanner."""

    @property
    def name(self) -> str:
        return "nmap"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DISCOVERY

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["nmap"]

        scan_type = config.get("scan_type", "service")
        if scan_type == "quick":
            cmd.extend(["-F", "-T4"])
        elif scan_type == "service":
            cmd.extend(["-sV", "-sC", "-T3"])
        elif scan_type == "full":
            cmd.extend(["-sV", "-sC", "-p-", "-T3"])
        elif scan_type == "udp":
            cmd.extend(["-sU", "--top-ports", "100"])

        if config.get("os_detection", False):
            cmd.append("-O")

        cmd.extend(["-oX", "-"])

        if "max_rate" in config:
            cmd.extend(["--max-rate", str(config["max_rate"])])

        cmd.append(target)
        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        try:
            root = ET.fromstring(raw_output)
        except ET.ParseError as e:
            result.status = ToolStatus.FAILED
            result.errors.append(f"Failed to parse nmap XML: {e}")
            return result

        for host_elem in root.findall(".//host"):
            addr_elem = host_elem.find("address")
            if addr_elem is None:
                continue

            host_ip = addr_elem.get("addr", "")
            host_state = "unknown"
            status_elem = host_elem.find("status")
            if status_elem is not None:
                host_state = status_elem.get("state", "unknown")

            os_matches = []
            for osmatch in host_elem.findall(".//osmatch"):
                os_matches.append({
                    "name": osmatch.get("name", ""),
                    "accuracy": osmatch.get("accuracy", ""),
                })

            hostnames = []
            for hostname in host_elem.findall(".//hostname"):
                hostnames.append(hostname.get("name", ""))

            host_data = {
                "ip": host_ip,
                "state": host_state,
                "hostnames": hostnames,
                "os_matches": os_matches,
                "ports": [],
            }

            for port_elem in host_elem.findall(".//port"):
                port_id = port_elem.get("portid", "")
                protocol = port_elem.get("protocol", "tcp")

                state_elem = port_elem.find("state")
                port_state = state_elem.get("state", "") if state_elem is not None else ""

                service_elem = port_elem.find("service")
                service_name = ""
                service_version = ""
                service_product = ""

                if service_elem is not None:
                    service_name = service_elem.get("name", "")
                    service_product = service_elem.get("product", "")
                    service_version = service_elem.get("version", "")

                port_data = {
                    "port": int(port_id),
                    "protocol": protocol,
                    "state": port_state,
                    "service": service_name,
                    "product": service_product,
                    "version": service_version,
                }
                host_data["ports"].append(port_data)

                if port_state == "open":
                    version_str = f" {service_product} {service_version}".strip()
                    result.findings.append({
                        "title": f"Open port {port_id}/{protocol}: {service_name}{version_str}",
                        "severity": "info",
                        "target_host": host_ip,
                        "target_port": int(port_id),
                        "target_protocol": protocol,
                        "target_service": service_name,
                        "description": (
                            f"Port {port_id}/{protocol} is open running "
                            f"{service_name}{version_str} on {host_ip}"
                        ),
                        "raw_evidence": port_data,
                    })

            result.hosts.append(host_data)

        result.metadata = {
            "total_hosts": len(result.hosts),
            "total_open_ports": sum(
                len([p for p in h["ports"] if p["state"] == "open"])
                for h in result.hosts
            ),
        }

        return result
