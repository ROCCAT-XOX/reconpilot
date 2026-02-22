from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter()


def _report_to_response(r: Report) -> ReportResponse:
    return ReportResponse(
        id=str(r.id),
        project_id=str(r.project_id),
        scan_id=str(r.scan_id) if r.scan_id else None,
        name=r.name,
        template=r.template,
        format=r.format,
        file_path=r.file_path,
        config=r.config or {},
        generated_by=str(r.generated_by) if r.generated_by else None,
        created_at=r.created_at.isoformat() if r.created_at else "",
    )


@router.get("/", response_model=list[ReportResponse])
async def list_reports(db: DB, current_user: CurrentUser):
    result = await db.execute(select(Report).order_by(Report.created_at.desc()).limit(100))
    reports = result.scalars().all()
    return [_report_to_response(r) for r in reports]


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(data: ReportCreate, db: DB, current_user: CurrentUser):
    report = Report(
        project_id=data.scan_id if data.scan_id else None,  # Will be set below
        name=data.name,
        template=data.template,
        format=data.format,
        config=data.config,
        generated_by=current_user.id,
    )
    # For now, reports are created as placeholders (no actual PDF generation)
    db.add(report)
    await db.flush()
    return _report_to_response(report)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)
