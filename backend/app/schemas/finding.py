from pydantic import BaseModel, Field


class FindingResponse(BaseModel):
    id: str
    scan_id: str
    project_id: str
    title: str
    description: str | None
    severity: str
    cvss_score: float | None
    cve_id: str | None
    cwe_id: str | None
    target_host: str | None
    target_port: int | None
    target_protocol: str | None
    target_url: str | None
    target_service: str | None
    source_tool: str
    raw_evidence: dict | None
    status: str
    assigned_to: str | None
    verified_by: str | None
    verified_at: str | None
    fingerprint: str | None
    is_duplicate: bool
    created_at: str
    updated_at: str


class FindingUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(open|confirmed|false_positive|accepted_risk|remediated)$",
    )
    assigned_to: str | None = None
    description: str | None = None


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    id: str
    finding_id: str
    user_id: str | None
    user_name: str | None = None
    content: str
    created_at: str


class FindingStats(BaseModel):
    total: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
    by_tool: dict[str, int]


class ScanComparisonRequest(BaseModel):
    scan_a_id: str
    scan_b_id: str


class ScanComparisonResponse(BaseModel):
    new_findings: int
    resolved_findings: int
    unchanged_findings: int
    new_finding_ids: list[str]
    resolved_finding_ids: list[str]
