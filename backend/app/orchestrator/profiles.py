from dataclasses import dataclass, field


@dataclass
class ToolConfig:
    """Configuration for a tool within a phase."""
    tool_name: str
    enabled: bool = True
    config: dict = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class ScanPhase:
    """A phase in the scan pipeline."""
    name: str
    order: int
    tools: list[ToolConfig] = field(default_factory=list)
    parallel: bool = True
    wait_for_completion: bool = True


@dataclass
class ScanProfile:
    """Definition of a scan profile with phases and tools."""
    name: str
    description: str
    phases: list[ScanPhase] = field(default_factory=list)
    estimated_duration_minutes: int = 30


PROFILES: dict[str, ScanProfile] = {
    "quick": ScanProfile(
        name="Quick Recon",
        description="Fast overview: Subdomains + Top-100 ports + Tech stack",
        estimated_duration_minutes=15,
        phases=[
            ScanPhase(
                name="OSINT & Discovery",
                order=1,
                tools=[
                    ToolConfig("subfinder"),
                ],
            ),
            ScanPhase(
                name="Probing",
                order=2,
                tools=[
                    ToolConfig("httpx", config={"tech_detect": True}),
                    ToolConfig("nmap", config={"scan_type": "quick"}),
                ],
            ),
        ],
    ),
    "standard": ScanProfile(
        name="Standard",
        description="Full scan: OSINT + Port scan + Web vulnerability analysis",
        estimated_duration_minutes=60,
        phases=[
            ScanPhase(
                name="OSINT & Discovery",
                order=1,
                tools=[
                    ToolConfig("subfinder"),
                ],
            ),
            ScanPhase(
                name="Probing & Fingerprinting",
                order=2,
                tools=[
                    ToolConfig("httpx", config={"tech_detect": True}),
                    ToolConfig("nmap", config={"scan_type": "service"}),
                ],
            ),
            ScanPhase(
                name="Vulnerability Scanning",
                order=3,
                tools=[
                    ToolConfig("nuclei", config={"severities": ["critical", "high", "medium"]}),
                    ToolConfig("nikto"),
                    ToolConfig("sslyze"),
                ],
            ),
            ScanPhase(
                name="Web Fuzzing",
                order=4,
                tools=[
                    ToolConfig("ffuf", config={"wordlist": "common.txt"}),
                ],
            ),
        ],
    ),
    "deep": ScanProfile(
        name="Deep Dive",
        description="Deep analysis: Everything + SQLi + Auth testing",
        estimated_duration_minutes=180,
        phases=[
            ScanPhase(
                name="OSINT & Discovery",
                order=1,
                tools=[
                    ToolConfig("subfinder"),
                ],
            ),
            ScanPhase(
                name="Probing & Fingerprinting",
                order=2,
                tools=[
                    ToolConfig("httpx", config={"tech_detect": True}),
                    ToolConfig("nmap", config={"scan_type": "full", "os_detection": True}),
                ],
            ),
            ScanPhase(
                name="Vulnerability Scanning",
                order=3,
                tools=[
                    ToolConfig("nuclei", config={"severities": ["critical", "high", "medium", "low"]}),
                    ToolConfig("nikto"),
                    ToolConfig("sslyze"),
                ],
            ),
            ScanPhase(
                name="Web Deep Analysis",
                order=4,
                tools=[
                    ToolConfig("ffuf", config={"wordlist": "directory-list-2.3-medium.txt"}),
                ],
            ),
            ScanPhase(
                name="Exploitation Validation",
                order=5,
                tools=[
                    ToolConfig("sqlmap", config={"level": 3, "risk": 2}),
                ],
            ),
        ],
    ),
}


def get_profile(name: str) -> ScanProfile | None:
    """Get a scan profile by name."""
    return PROFILES.get(name)


def list_profiles() -> list[dict]:
    """Return profile summaries for the API."""
    return [
        {
            "name": p.name,
            "key": key,
            "description": p.description,
            "estimated_duration_minutes": p.estimated_duration_minutes,
            "phases": len(p.phases),
            "tools": [t.tool_name for phase in p.phases for t in phase.tools],
        }
        for key, p in PROFILES.items()
    ]
