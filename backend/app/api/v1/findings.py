from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models.finding import Finding

router = APIRouter()


class FindingResponse(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    source_tool: str
    target_host: str | None
    target_port: int | None
    cve_id: str | None


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse(
        id=str(finding.id), title=finding.title, severity=finding.severity,
        status=finding.status, source_tool=finding.source_tool,
        target_host=finding.target_host, target_port=finding.target_port,
        cve_id=finding.cve_id,
    )


@router.put("/{finding_id}/verify")
async def verify_finding(finding_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    from datetime import datetime, timezone
    finding.status = "confirmed"
    finding.verified_by = current_user.id
    finding.verified_at = datetime.now(timezone.utc)
    return {"status": "confirmed", "verified_by": str(current_user.id)}
