from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    name: str | None = None
    profile: str = Field(default="standard", pattern="^(quick|standard|deep|custom)$")
    config: dict = Field(default_factory=dict)
    targets: list[str] = Field(default_factory=list)


class ScanResponse(BaseModel):
    model_config = {"from_attributes": True}

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

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, "__table__"):
            data = {
                "id": str(obj.id),
                "project_id": str(obj.project_id),
                "name": obj.name,
                "profile": obj.profile,
                "status": obj.status,
                "config": obj.config or {},
                "started_at": obj.started_at.isoformat() if obj.started_at else None,
                "completed_at": obj.completed_at.isoformat() if obj.completed_at else None,
                "started_by": str(obj.started_by) if obj.started_by else None,
                "created_at": obj.created_at.isoformat() if obj.created_at else "",
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


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
