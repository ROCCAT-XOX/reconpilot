"""Tests for tool output parsing and finding fingerprinting."""
import json

from app.services.finding_service import compute_finding_fingerprint
from app.tools.scanning.nmap import NmapWrapper
from app.tools.scanning.nuclei import NucleiWrapper

SAMPLE_NMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <hostnames><hostname name="router.local"/></hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="8.9"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="nginx" version="1.24"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="closed"/>
        <service name="https"/>
      </port>
    </ports>
  </host>
</nmaprun>"""

SAMPLE_NUCLEI_JSONL = '\n'.join([
    json.dumps({
        "template-id": "cve-2021-44228",
        "info": {
            "name": "Log4j RCE",
            "severity": "critical",
            "description": "Remote code execution via Log4j",
            "classification": {"cve-id": ["CVE-2021-44228"], "cwe-id": ["CWE-502"]},
        },
        "host": "https://example.com",
        "matched-at": "https://example.com/api",
    }),
    json.dumps({
        "template-id": "tech-detect",
        "info": {"name": "Nginx Detected", "severity": "info", "description": ""},
        "host": "https://example.com",
        "matched-at": "https://example.com",
    }),
])


class TestNmapParsing:
    def setup_method(self):
        self.nmap = NmapWrapper()

    def test_parse_hosts(self):
        result = self.nmap.parse_output(SAMPLE_NMAP_XML, "192.168.1.1")
        assert len(result.hosts) == 1
        assert result.hosts[0]["ip"] == "192.168.1.1"

    def test_parse_open_ports(self):
        result = self.nmap.parse_output(SAMPLE_NMAP_XML, "192.168.1.1")
        open_ports = [p for p in result.hosts[0]["ports"] if p["state"] == "open"]
        assert len(open_ports) == 2
        assert open_ports[0]["port"] == 22
        assert open_ports[1]["port"] == 80

    def test_findings_generated_for_open_ports(self):
        result = self.nmap.parse_output(SAMPLE_NMAP_XML, "192.168.1.1")
        assert len(result.findings) == 2
        assert "22" in result.findings[0]["title"]

    def test_hostnames_parsed(self):
        result = self.nmap.parse_output(SAMPLE_NMAP_XML, "192.168.1.1")
        assert "router.local" in result.hosts[0]["hostnames"]

    def test_metadata_counts(self):
        result = self.nmap.parse_output(SAMPLE_NMAP_XML, "192.168.1.1")
        assert result.metadata["total_hosts"] == 1
        assert result.metadata["total_open_ports"] == 2

    def test_invalid_xml_returns_failed(self):
        result = self.nmap.parse_output("not xml at all", "target")
        assert result.status.value == "failed"
        assert len(result.errors) > 0


class TestNucleiParsing:
    def setup_method(self):
        self.nuclei = NucleiWrapper()

    def test_parse_findings(self):
        result = self.nuclei.parse_output(SAMPLE_NUCLEI_JSONL, "example.com")
        assert len(result.findings) == 2

    def test_severity_mapping(self):
        result = self.nuclei.parse_output(SAMPLE_NUCLEI_JSONL, "example.com")
        assert result.findings[0]["severity"] == "critical"
        assert result.findings[1]["severity"] == "info"

    def test_cve_extraction(self):
        result = self.nuclei.parse_output(SAMPLE_NUCLEI_JSONL, "example.com")
        assert result.findings[0]["cve_id"] == "CVE-2021-44228"

    def test_empty_input(self):
        result = self.nuclei.parse_output("", "example.com")
        assert len(result.findings) == 0

    def test_invalid_json_lines_skipped(self):
        mixed = "not json\n" + json.dumps({
            "template-id": "test",
            "info": {"name": "Test", "severity": "low"},
            "host": "test.com",
        })
        result = self.nuclei.parse_output(mixed, "test.com")
        assert len(result.findings) == 1


class TestFindingFingerprint:
    def test_same_inputs_same_fingerprint(self):
        fp1 = compute_finding_fingerprint("host.com", 80, None, "CVE-2021-1234", None, "Test Finding")
        fp2 = compute_finding_fingerprint("host.com", 80, None, "CVE-2021-1234", None, "Test Finding")
        assert fp1 == fp2

    def test_different_inputs_different_fingerprint(self):
        fp1 = compute_finding_fingerprint("host.com", 80, None, None, None, "Finding A")
        fp2 = compute_finding_fingerprint("host.com", 443, None, None, None, "Finding B")
        assert fp1 != fp2

    def test_fingerprint_is_sha256_hex(self):
        fp = compute_finding_fingerprint("host.com", 80, None, None, None, "Test")
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_case_insensitive_title(self):
        fp1 = compute_finding_fingerprint("host.com", 80, None, None, None, "SQL Injection")
        fp2 = compute_finding_fingerprint("host.com", 80, None, None, None, "sql injection")
        assert fp1 == fp2
