from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    name: str = Field(..., max_length=255)
    scan_id: str | None = None
    template: str = Field(default="technical_report", pattern="^(executive_summary|technical_report)$")
    format: str = Field(default="pdf", pattern="^(pdf|html|json|csv)$")
    config: dict = Field(default_factory=dict)


class ReportResponse(BaseModel):
    id: str
    project_id: str
    scan_id: str | None
    name: str
    template: str
    format: str
    file_path: str | None
    config: dict
    generated_by: str | None
    created_at: str
