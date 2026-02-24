"""Tests for tool execution via subprocess, output parsing, and auto-discovery.

All subprocess calls are mocked — no real tools are invoked.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus
from app.tools.scanning.nmap import NmapWrapper
from app.tools.scanning.nuclei import NucleiWrapper
from app.tools.recon.subfinder import SubfinderWrapper
from app.tools.recon.httpx import HttpxWrapper
from app.tools.scanning.ffuf import FfufWrapper
from app.tools.scanning.gobuster import GobusterWrapper
from app.tools.scanning.nikto import NiktoWrapper
from app.tools.web_analysis.whatweb import WhatWebWrapper
from app.tools.web_analysis.testssl import TestsslWrapper
from app.tools.exploitation.sqlmap import SqlmapWrapper
from app.tools.recon.amass import AmassWrapper


# === Helper to mock subprocess ===

def make_mock_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Create a mock asyncio subprocess process."""
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(
        stdout.encode("utf-8"),
        stderr.encode("utf-8"),
    ))
    proc.returncode = returncode
    return proc


# === Nmap Tests ===

class TestNmapExecution:
    def test_build_command_quick(self):
        nmap = NmapWrapper()
        cmd = nmap.build_command("10.0.0.1", {"scan_type": "quick"})
        assert cmd[0] == "nmap"
        assert "-F" in cmd
        assert "-T4" in cmd
        assert "10.0.0.1" in cmd

    def test_build_command_service(self):
        nmap = NmapWrapper()
        cmd = nmap.build_command("10.0.0.1", {"scan_type": "service"})
        assert "-sV" in cmd
        assert "-sC" in cmd

    def test_build_command_full(self):
        nmap = NmapWrapper()
        cmd = nmap.build_command("10.0.0.1", {"scan_type": "full"})
        assert "-p-" in cmd

    def test_build_command_os_detection(self):
        nmap = NmapWrapper()
        cmd = nmap.build_command("10.0.0.1", {"os_detection": True})
        assert "-O" in cmd

    def test_build_command_max_rate(self):
        nmap = NmapWrapper()
        cmd = nmap.build_command("10.0.0.1", {"max_rate": "500"})
        assert "--max-rate" in cmd
        assert "500" in cmd

    def test_parse_output_valid_xml(self):
        nmap = NmapWrapper()
        xml_output = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="10.0.0.1" addrtype="ipv4"/>
    <hostnames><hostname name="server.example.com"/></hostnames>
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
        result = nmap.parse_output(xml_output, "10.0.0.1")
        assert result.status == ToolStatus.COMPLETED
        assert len(result.hosts) == 1
        assert result.hosts[0]["ip"] == "10.0.0.1"
        assert len(result.hosts[0]["ports"]) == 3
        # Only open ports become findings
        assert len(result.findings) == 2
        assert result.findings[0]["target_port"] == 22
        assert result.findings[1]["target_port"] == 80
        assert result.metadata["total_open_ports"] == 2

    def test_parse_output_invalid_xml(self):
        nmap = NmapWrapper()
        result = nmap.parse_output("not xml at all", "10.0.0.1")
        assert result.status == ToolStatus.FAILED
        assert len(result.errors) > 0

    async def test_run_with_subprocess_mock(self):
        nmap = NmapWrapper()
        xml_output = '<?xml version="1.0"?><nmaprun></nmaprun>'
        mock_proc = make_mock_process(stdout=xml_output)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await nmap.run(target="10.0.0.1", config={"scan_type": "quick"})
        assert result.status == ToolStatus.COMPLETED
        assert result.tool_name == "nmap"

    async def test_run_timeout(self):
        nmap = NmapWrapper()
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await nmap.run(target="10.0.0.1", timeout=1)
        assert result.status == ToolStatus.TIMEOUT

    async def test_run_scope_violation(self):
        nmap = NmapWrapper()
        result = await nmap.run(
            target="evil.com",
            scope_targets=["example.com"],
        )
        assert result.status == ToolStatus.FAILED
        assert "outside defined scope" in result.errors[0]


# === Nuclei Tests ===

class TestNucleiExecution:
    def test_build_command(self):
        nuclei = NucleiWrapper()
        cmd = nuclei.build_command("https://example.com", {
            "severities": ["critical", "high"],
            "tags": ["cve"],
            "rate_limit": 100,
        })
        assert "nuclei" == cmd[0]
        assert "-target" in cmd
        assert "critical,high" in cmd
        assert "-tags" in cmd

    def test_parse_output_jsonl(self):
        nuclei = NucleiWrapper()
        output = "\n".join([
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
                "info": {"name": "Nginx Detected", "severity": "info"},
                "host": "https://example.com",
            }),
        ])
        result = nuclei.parse_output(output, "https://example.com")
        assert result.status == ToolStatus.COMPLETED
        assert len(result.findings) == 2
        assert result.findings[0]["severity"] == "critical"
        assert result.findings[0]["cve_id"] == "CVE-2021-44228"
        assert result.findings[0]["cwe_id"] == "CWE-502"
        assert result.findings[1]["severity"] == "info"
        assert result.metadata["severity_counts"]["critical"] == 1

    def test_parse_output_empty(self):
        nuclei = NucleiWrapper()
        result = nuclei.parse_output("", "example.com")
        assert result.status == ToolStatus.COMPLETED
        assert len(result.findings) == 0

    async def test_run_with_mock(self):
        nuclei = NucleiWrapper()
        output = json.dumps({
            "template-id": "test",
            "info": {"name": "Test", "severity": "info"},
            "host": "example.com",
        })
        mock_proc = make_mock_process(stdout=output)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await nuclei.run("example.com")
        assert result.status == ToolStatus.COMPLETED


# === Subfinder Tests ===

class TestSubfinderExecution:
    def test_build_command(self):
        sf = SubfinderWrapper()
        cmd = sf.build_command("example.com", {"threads": 50, "recursive": True})
        assert "subfinder" == cmd[0]
        assert "-d" in cmd
        assert "example.com" in cmd
        assert "-recursive" in cmd

    def test_parse_output_json(self):
        sf = SubfinderWrapper()
        output = "\n".join([
            json.dumps({"host": "api.example.com", "source": "crtsh"}),
            json.dumps({"host": "mail.example.com", "source": "virustotal"}),
            json.dumps({"host": "api.example.com", "source": "hackertarget"}),  # duplicate
        ])
        result = sf.parse_output(output, "example.com")
        assert result.status == ToolStatus.COMPLETED
        assert len(result.hosts) == 3  # raw entries include dup
        assert result.metadata["total_subdomains"] == 2  # deduped
        assert len(result.findings) == 2

    def test_parse_output_plain_text(self):
        sf = SubfinderWrapper()
        output = "api.example.com\nmail.example.com\n"
        result = sf.parse_output(output, "example.com")
        assert result.metadata["total_subdomains"] == 2


# === httpx Tests ===

class TestHttpxExecution:
    def test_build_command(self):
        httpx = HttpxWrapper()
        cmd = httpx.build_command("example.com", {"tech_detect": True, "threads": 25})
        assert "httpx" == cmd[0]
        assert "-tech-detect" in cmd

    def test_parse_output(self):
        httpx = HttpxWrapper()
        output = json.dumps({
            "url": "https://example.com",
            "status_code": 200,
            "title": "Example Domain",
            "webserver": "nginx",
            "tech": ["Nginx", "WordPress"],
            "content_length": 1234,
            "host": "example.com",
        })
        result = httpx.parse_output(output, "example.com")
        assert result.status == ToolStatus.COMPLETED
        assert len(result.hosts) == 1
        assert result.hosts[0]["url"] == "https://example.com"
        # 1 HTTP service finding + 1 WordPress CMS finding
        assert len(result.findings) == 2
        assert any("WordPress" in f["title"] for f in result.findings)


# === ffuf Tests ===

class TestFfufExecution:
    def test_build_command(self):
        ffuf = FfufWrapper()
        cmd = ffuf.build_command("https://example.com", {"wordlist": "/tmp/list.txt"})
        assert "ffuf" == cmd[0]
        assert "FUZZ" in cmd[1] or any("FUZZ" in c for c in cmd)

    def test_parse_output(self):
        ffuf = FfufWrapper()
        output = json.dumps({
            "results": [
                {"url": "https://example.com/admin", "status": 200, "length": 500,
                 "words": 50, "lines": 10, "input": {"FUZZ": "admin"}, "redirectlocation": ""},
                {"url": "https://example.com/robots.txt", "status": 200, "length": 100,
                 "words": 10, "lines": 3, "input": {"FUZZ": "robots.txt"}, "redirectlocation": ""},
            ],
        })
        result = ffuf.parse_output(output, "https://example.com")
        assert len(result.findings) == 2
        # admin should have medium severity
        admin_finding = [f for f in result.findings if "admin" in f["title"]][0]
        assert admin_finding["severity"] == "medium"


# === Gobuster Tests ===

class TestGobusterExecution:
    def test_parse_output(self):
        gb = GobusterWrapper()
        output = """/admin (Status: 200) [Size: 1234]
/images (Status: 301) [Size: 500]
/login (Status: 200) [Size: 2000]
"""
        result = gb.parse_output(output, "https://example.com")
        assert len(result.findings) == 3
        login_f = [f for f in result.findings if "login" in f["title"]][0]
        assert login_f["severity"] == "medium"


# === Nikto Tests ===

class TestNiktoExecution:
    def test_parse_output_json(self):
        nikto = NiktoWrapper()
        output = json.dumps({
            "vulnerabilities": [
                {"OSVDB": "3092", "method": "GET", "url": "/admin/",
                 "msg": "Directory listing found: /admin/"},
                {"OSVDB": "0", "method": "GET", "url": "/",
                 "msg": "Server header reveals version information"},
            ]
        })
        result = nikto.parse_output(output, "https://example.com")
        assert len(result.findings) == 2
        assert result.findings[0]["severity"] == "medium"  # directory listing
        assert result.findings[1]["severity"] == "low"  # version/header


# === WhatWeb Tests ===

class TestWhatWebExecution:
    def test_parse_output(self):
        ww = WhatWebWrapper()
        output = json.dumps({
            "target": "https://example.com",
            "plugins": {
                "Nginx": {"version": ["1.24.0"]},
                "PHP": {"version": ["8.2"]},
                "WordPress": {"version": ["6.4"], "string": ["WordPress 6.4"]},
                "HTTPServer": {},  # should be skipped
            },
        })
        result = ww.parse_output(output, "https://example.com")
        assert result.status == ToolStatus.COMPLETED
        # HTTPServer skipped
        assert len(result.findings) == 3
        assert "Nginx" in result.metadata["technologies"]


# === testssl Tests ===

class TestTestsslExecution:
    def test_parse_output(self):
        ts = TestsslWrapper()
        output = json.dumps([
            {"id": "heartbleed", "severity": "CRITICAL", "finding": "VULNERABLE", "cve": "CVE-2014-0160"},
            {"id": "secure_renego", "severity": "OK", "finding": "supported", "cve": ""},
            {"id": "BEAST", "severity": "MEDIUM", "finding": "TLS1: some ciphers", "cve": "CVE-2011-3389"},
        ])
        result = ts.parse_output(output, "example.com:443")
        # OK severity without CVE is skipped
        assert len(result.findings) == 2
        assert result.findings[0]["severity"] == "critical"
        assert result.findings[0]["cve_id"] == "CVE-2014-0160"


# === SQLMap Tests ===

class TestSqlmapExecution:
    def test_build_command(self):
        sm = SqlmapWrapper()
        cmd = sm.build_command("https://example.com/?id=1", {"level": 3, "risk": 2})
        assert "--level" in cmd
        assert "3" in cmd

    def test_parse_output_vulnerable(self):
        sm = SqlmapWrapper()
        output = """
[INFO] testing 'GET parameter id'
Parameter: GET parameter 'id' (GET)
    Type: boolean-based blind
    Payload: id=1 AND 1=1

[INFO] GET parameter 'id' is vulnerable
sqlmap identified the following injection point(s)
back-end DBMS: MySQL >= 5.0
"""
        result = sm.parse_output(output, "https://example.com/?id=1")
        assert len(result.findings) >= 1
        assert result.metadata["dbms"] == "MySQL >= 5.0"

    def test_parse_output_no_vulns(self):
        sm = SqlmapWrapper()
        output = "all tested parameters do not appear to be injectable"
        result = sm.parse_output(output, "https://example.com/?id=1")
        assert len(result.findings) == 0
        assert result.metadata.get("no_vulns_found") is True


# === Amass Tests ===

class TestAmassExecution:
    def test_parse_output(self):
        amass = AmassWrapper()
        output = "\n".join([
            json.dumps({"name": "sub1.example.com", "addresses": [{"ip": "1.2.3.4"}], "tag": "cert"}),
            json.dumps({"name": "sub2.example.com", "addresses": [], "tag": "api"}),
        ])
        result = amass.parse_output(output, "example.com")
        assert result.metadata["total_subdomains"] == 2
        assert len(result.findings) == 2


# === Base class run() tests ===

class TestBaseToolRun:
    async def test_run_success(self):
        nmap = NmapWrapper()
        xml = '<?xml version="1.0"?><nmaprun></nmaprun>'
        mock_proc = make_mock_process(stdout=xml)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await nmap.run("10.0.0.1")
        assert result.status == ToolStatus.COMPLETED
        assert result.duration_seconds > 0

    async def test_run_with_stderr(self):
        nmap = NmapWrapper()
        xml = '<?xml version="1.0"?><nmaprun></nmaprun>'
        mock_proc = make_mock_process(stdout=xml, stderr="Warning: something", returncode=1)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await nmap.run("10.0.0.1")
        assert "Warning: something" in result.errors[0]

    async def test_run_exception(self):
        nmap = NmapWrapper()
        with patch("asyncio.create_subprocess_exec", side_effect=OSError("not found")):
            result = await nmap.run("10.0.0.1")
        assert result.status == ToolStatus.FAILED
        assert "not found" in result.errors[0]

    async def test_scope_validation(self):
        nmap = NmapWrapper()
        result = await nmap.run("evil.com", scope_targets=["example.com"])
        assert result.status == ToolStatus.FAILED

    async def test_scope_allows_subdomain(self):
        nmap = NmapWrapper()
        xml = '<?xml version="1.0"?><nmaprun></nmaprun>'
        mock_proc = make_mock_process(stdout=xml)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await nmap.run("sub.example.com", scope_targets=["example.com"])
        assert result.status == ToolStatus.COMPLETED

    async def test_scope_allows_ip_in_cidr(self):
        nmap = NmapWrapper()
        xml = '<?xml version="1.0"?><nmaprun></nmaprun>'
        mock_proc = make_mock_process(stdout=xml)
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await nmap.run("10.0.0.5", scope_targets=["10.0.0.0/24"])
        assert result.status == ToolStatus.COMPLETED
