from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models.scan import Scan, ScanJob

router = APIRouter()


class ScanResponse(BaseModel):
    id: str
    project_id: str
    name: str | None
    profile: str
    status: str
    created_at: str


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanResponse(
        id=str(scan.id), project_id=str(scan.project_id), name=scan.name,
        profile=scan.profile, status=scan.status, created_at=scan.created_at.isoformat(),
    )


@router.get("/{scan_id}/jobs")
async def get_scan_jobs(scan_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(ScanJob).where(ScanJob.scan_id == scan_id))
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "tool_name": j.tool_name,
            "phase": j.phase,
            "status": j.status,
            "target": j.target,
            "duration_seconds": j.duration_seconds,
        }
        for j in jobs
    ]
