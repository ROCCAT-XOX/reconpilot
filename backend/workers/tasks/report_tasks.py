import asyncio
import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="report.generate")
def generate_report_task(self, report_id: str, project_id: str, template: str, format: str, config: dict | None = None):
    """Celery task to generate a report."""
    logger.info(f"Generating report {report_id} for project {project_id}")

    async def _run():
        from app.core.database import async_session
        from app.reporting.generator import ReportGenerator
        from app.models.report import Report
        from app.models.finding import Finding
        from app.models.project import Project
        from sqlalchemy import select

        async with async_session() as session:
            # Fetch project
            proj_result = await session.execute(select(Project).where(Project.id == project_id))
            project = proj_result.scalar_one_or_none()
            if not project:
                logger.error(f"Project {project_id} not found")
                return

            # Fetch findings
            findings_result = await session.execute(
                select(Finding)
                .where(Finding.project_id == project_id, Finding.is_duplicate == False)
                .order_by(Finding.severity)
            )
            findings = findings_result.scalars().all()

            # Generate report
            generator = ReportGenerator()
            project_data = {
                "id": str(project.id),
                "name": project.name,
                "client_name": project.client_name,
                "description": project.description,
            }
            findings_data = [
                {
                    "title": f.title,
                    "severity": f.severity,
                    "description": f.description,
                    "target_host": f.target_host,
                    "target_port": f.target_port,
                    "target_url": f.target_url,
                    "source_tool": f.source_tool,
                    "cve_id": f.cve_id,
                    "cwe_id": f.cwe_id,
                    "status": f.status,
                    "cvss_score": float(f.cvss_score) if f.cvss_score else None,
                }
                for f in findings
            ]

            config = config or {}
            if format == "pdf":
                output_path = await generator.generate_pdf(project_data, findings_data, {**config, "template": f"{template}.html"})
            elif format == "html":
                output_path = await generator.generate_html(project_data, findings_data, {**config, "template": f"{template}.html"})
            elif format == "json":
                output_path = await generator.generate_json(project_data, findings_data, config)
            elif format == "csv":
                output_path = await generator.generate_csv(project_data, findings_data, config)
            else:
                output_path = await generator.generate_pdf(project_data, findings_data, {**config, "template": f"{template}.html"})

            # Update report record
            report_result = await session.execute(select(Report).where(Report.id == report_id))
            report = report_result.scalar_one_or_none()
            if report:
                report.file_path = str(output_path)
            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise
    finally:
        loop.close()

    return {"report_id": report_id, "status": "completed"}
