from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    name: str | None = None
    profile: str = Field(default="standard", pattern="^(quick|standard|deep|custom)$")
    config: dict = Field(default_factory=dict)
    targets: list[str] = Field(default_factory=list)


class ScanResponse(BaseModel):
    id: str
    project_id: str
    name: str | None
    profile: str
    status: str
    config: dict
    started_at: str | None
    completed_at: str | None
    started_by: str | None
    created_at: str


class ScanJobResponse(BaseModel):
    id: str
    scan_id: str
    tool_name: str
    phase: str
    status: str
    target: str | None
    duration_seconds: int | None
    error_message: str | None
    started_at: str | None
    completed_at: str | None


class ScanTimelineEvent(BaseModel):
    timestamp: str
    event: str
    tool: str | None = None
    phase: str | None = None
    details: dict = Field(default_factory=dict)
