from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models.report import Report

router = APIRouter()


class ReportResponse(BaseModel):
    id: str
    name: str
    template: str
    format: str
    file_path: str | None
    created_at: str


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse(
        id=str(report.id), name=report.name, template=report.template,
        format=report.format, file_path=report.file_path,
        created_at=report.created_at.isoformat(),
    )
