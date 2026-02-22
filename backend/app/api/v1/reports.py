from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DB, LeadOrAbove
from app.models.report import Report
from app.models.finding import Finding

router = APIRouter()


class ReportResponse(BaseModel):
    id: str
    project_id: str
    scan_id: str | None
    name: str
    template: str
    format: str
    file_path: str | None
    config: dict | None
    generated_by: str | None
    created_at: str


class ReportCreate(BaseModel):
    name: str
    template: str = "executive_summary"
    format: str = "pdf"
    scan_id: str | None = None
    config: dict | None = None


def _report_to_response(r: Report) -> ReportResponse:
    return ReportResponse(
        id=str(r.id),
        project_id=str(r.project_id),
        scan_id=str(r.scan_id) if r.scan_id else None,
        name=r.name,
        template=r.template,
        format=r.format,
        file_path=r.file_path,
        config=r.config,
        generated_by=str(r.generated_by) if r.generated_by else None,
        created_at=r.created_at.isoformat(),
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.get("/{report_id}/download")
async def download_report(report_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not ready")

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    media_type = {
        "pdf": "application/pdf",
        "html": "text/html",
        "json": "application/json",
        "csv": "text/csv",
    }.get(report.format, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=f"{report.name}.{report.format}",
    )


# Project-scoped reports
from fastapi import APIRouter as _APIRouter

project_reports_router = _APIRouter()


@project_reports_router.get("/{project_id}/reports", response_model=list[ReportResponse])
async def list_project_reports(project_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(Report).where(Report.project_id == project_id).order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return [_report_to_response(r) for r in reports]


@project_reports_router.post("/{project_id}/reports", response_model=ReportResponse, status_code=201)
async def create_report(project_id: str, data: ReportCreate, db: DB, current_user: LeadOrAbove):
    report = Report(
        project_id=project_id,
        scan_id=data.scan_id,
        name=data.name,
        template=data.template,
        format=data.format,
        config=data.config or {},
        generated_by=current_user.id,
    )
    db.add(report)
    await db.flush()

    # Try to generate synchronously for simple reports, or queue via Celery
    try:
        from workers.tasks.report_tasks import generate_report_task
        generate_report_task.delay(
            str(report.id), project_id, data.template, data.format, data.config
        )
    except Exception:
        # Generate synchronously if Celery is not available
        try:
            from app.reporting.generator import ReportGenerator
            generator = ReportGenerator()

            # Fetch findings
            query = select(Finding).where(Finding.project_id == project_id, Finding.is_duplicate == False)
            if data.scan_id:
                query = query.where(Finding.scan_id == data.scan_id)
            findings_result = await db.execute(query)
            findings = findings_result.scalars().all()

            from app.models.project import Project
            proj_result = await db.execute(select(Project).where(Project.id == project_id))
            project_obj = proj_result.scalar_one_or_none()

            project_data = {
                "id": str(project_obj.id),
                "name": project_obj.name,
                "client_name": project_obj.client_name,
                "description": project_obj.description,
            }
            findings_data = [
                {
                    "title": f.title, "severity": f.severity, "description": f.description,
                    "target_host": f.target_host, "target_port": f.target_port,
                    "target_url": f.target_url, "source_tool": f.source_tool,
                    "cve_id": f.cve_id, "cwe_id": f.cwe_id, "status": f.status,
                    "cvss_score": float(f.cvss_score) if f.cvss_score else None,
                }
                for f in findings
            ]

            config = data.config or {}
            config["template"] = f"{data.template}.html"

            if data.format == "pdf":
                output_path = await generator.generate_pdf(project_data, findings_data, config)
            elif data.format == "html":
                output_path = await generator.generate_html(project_data, findings_data, config)
            elif data.format == "json":
                output_path = await generator.generate_json(project_data, findings_data, config)
            elif data.format == "csv":
                output_path = await generator.generate_csv(project_data, findings_data, config)
            else:
                output_path = await generator.generate_pdf(project_data, findings_data, config)

            report.file_path = str(output_path)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Report generation failed: {e}")

    await db.flush()
    return _report_to_response(report)
