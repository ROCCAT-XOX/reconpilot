from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser
from app.models.finding import Finding
from app.models.project import Project
from app.models.scan import Scan

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: DB, current_user: CurrentUser):
    """Return aggregated dashboard statistics."""
    # Project count
    projects_count = (
        await db.execute(select(func.count()).select_from(Project))
    ).scalar() or 0

    # Active scans (running or pending)
    active_scans = (
        await db.execute(
            select(func.count())
            .select_from(Scan)
            .where(Scan.status.in_(["running", "pending"]))
        )
    ).scalar() or 0

    # Total findings
    total_findings = (
        await db.execute(select(func.count()).select_from(Finding))
    ).scalar() or 0

    # Critical findings
    critical_findings = (
        await db.execute(
            select(func.count())
            .select_from(Finding)
            .where(Finding.severity == "critical")
        )
    ).scalar() or 0

    # High findings
    high_findings = (
        await db.execute(
            select(func.count())
            .select_from(Finding)
            .where(Finding.severity == "high")
        )
    ).scalar() or 0

    # Recent scans (last 10)
    recent_scans_result = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(10)
    )
    recent_scans = [
        {
            "id": str(s.id),
            "name": s.name,
            "profile": s.profile,
            "status": s.status,
            "project_id": str(s.project_id),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in recent_scans_result.scalars().all()
    ]

    return {
        "projects_count": projects_count,
        "active_scans": active_scans,
        "total_findings": total_findings,
        "critical_findings": critical_findings,
        "high_findings": high_findings,
        "recent_scans": recent_scans,
    }
