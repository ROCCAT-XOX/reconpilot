from pydantic import BaseModel, Field


class FindingResponse(BaseModel):
    model_config = {"from_attributes": True}

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

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, "__table__"):
            data = {
                "id": str(obj.id),
                "scan_id": str(obj.scan_id),
                "project_id": str(obj.project_id),
                "title": obj.title,
                "description": obj.description,
                "severity": obj.severity,
                "cvss_score": float(obj.cvss_score) if obj.cvss_score else None,
                "cve_id": obj.cve_id,
                "cwe_id": obj.cwe_id,
                "target_host": obj.target_host,
                "target_port": obj.target_port,
                "target_protocol": obj.target_protocol,
                "target_url": obj.target_url,
                "target_service": obj.target_service,
                "source_tool": obj.source_tool,
                "raw_evidence": obj.raw_evidence,
                "status": obj.status,
                "assigned_to": str(obj.assigned_to) if obj.assigned_to else None,
                "verified_by": str(obj.verified_by) if obj.verified_by else None,
                "verified_at": obj.verified_at.isoformat() if obj.verified_at else None,
                "fingerprint": obj.fingerprint,
                "is_duplicate": obj.is_duplicate,
                "created_at": obj.created_at.isoformat() if obj.created_at else "",
                "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class FindingCreate(BaseModel):
    scan_id: str
    project_id: str
    title: str
    description: str | None = None
    severity: str = Field(..., pattern="^(critical|high|medium|low|info)$")
    cvss_score: float | None = None
    cve_id: str | None = None
    cwe_id: str | None = None
    target_host: str | None = None
    target_port: int | None = None
    target_protocol: str | None = None
    target_url: str | None = None
    target_service: str | None = None
    source_tool: str
    raw_evidence: dict | None = None


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
