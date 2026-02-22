from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DB, PentesterOrAbove
from app.models.finding import Finding, FindingComment
from app.models.report import ScanComparison
from app.schemas.finding import (
    FindingResponse, FindingUpdate, CommentCreate, CommentResponse,
    FindingStats, ScanComparisonRequest, ScanComparisonResponse,
)
from app.services.finding_service import compute_finding_fingerprint

router = APIRouter()


def _finding_to_response(f: Finding) -> FindingResponse:
    return FindingResponse(
        id=str(f.id),
        scan_id=str(f.scan_id),
        project_id=str(f.project_id),
        title=f.title,
        description=f.description,
        severity=f.severity,
        cvss_score=float(f.cvss_score) if f.cvss_score else None,
        cve_id=f.cve_id,
        cwe_id=f.cwe_id,
        target_host=f.target_host,
        target_port=f.target_port,
        target_protocol=f.target_protocol,
        target_url=f.target_url,
        target_service=f.target_service,
        source_tool=f.source_tool,
        raw_evidence=f.raw_evidence,
        status=f.status,
        assigned_to=str(f.assigned_to) if f.assigned_to else None,
        verified_by=str(f.verified_by) if f.verified_by else None,
        verified_at=f.verified_at.isoformat() if f.verified_at else None,
        fingerprint=f.fingerprint,
        is_duplicate=f.is_duplicate,
        created_at=f.created_at.isoformat(),
        updated_at=f.updated_at.isoformat(),
    )


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return _finding_to_response(finding)


@router.put("/{finding_id}", response_model=FindingResponse)
async def update_finding(finding_id: str, data: FindingUpdate, db: DB, current_user: PentesterOrAbove):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    if data.status is not None:
        finding.status = data.status
    if data.assigned_to is not None:
        finding.assigned_to = data.assigned_to
    if data.description is not None:
        finding.description = data.description

    await db.flush()
    return _finding_to_response(finding)


@router.put("/{finding_id}/verify")
async def verify_finding(finding_id: str, db: DB, current_user: PentesterOrAbove):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = "confirmed"
    finding.verified_by = current_user.id
    finding.verified_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "confirmed", "verified_by": str(current_user.id)}


# --- Comments ---

@router.get("/{finding_id}/comments", response_model=list[CommentResponse])
async def list_comments(finding_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(FindingComment)
        .where(FindingComment.finding_id == finding_id)
        .order_by(FindingComment.created_at)
    )
    comments = result.scalars().all()
    return [
        CommentResponse(
            id=str(c.id),
            finding_id=str(c.finding_id),
            user_id=str(c.user_id) if c.user_id else None,
            content=c.content,
            created_at=c.created_at.isoformat(),
        )
        for c in comments
    ]


@router.post("/{finding_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(finding_id: str, data: CommentCreate, db: DB, current_user: PentesterOrAbove):
    # Verify finding exists
    finding_result = await db.execute(select(Finding).where(Finding.id == finding_id))
    if not finding_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Finding not found")

    comment = FindingComment(
        finding_id=finding_id,
        user_id=current_user.id,
        content=data.content,
    )
    db.add(comment)
    await db.flush()
    return CommentResponse(
        id=str(comment.id),
        finding_id=str(comment.finding_id),
        user_id=str(comment.user_id),
        content=comment.content,
        created_at=comment.created_at.isoformat(),
    )


# --- Project-scoped finding endpoints ---

from fastapi import APIRouter as _APIRouter

project_findings_router = _APIRouter()


@project_findings_router.get("/{project_id}/findings", response_model=list[FindingResponse])
async def list_project_findings(
    project_id: str,
    db: DB,
    current_user: CurrentUser,
    severity: str | None = Query(None),
    status: str | None = Query(None),
    source_tool: str | None = Query(None),
    include_duplicates: bool = Query(False),
):
    query = select(Finding).where(Finding.project_id == project_id)

    if severity:
        query = query.where(Finding.severity == severity)
    if status:
        query = query.where(Finding.status == status)
    if source_tool:
        query = query.where(Finding.source_tool == source_tool)
    if not include_duplicates:
        query = query.where(Finding.is_duplicate == False)

    query = query.order_by(
        # Order by severity: critical, high, medium, low, info
        func.array_position(
            func.cast(["critical", "high", "medium", "low", "info"], type_=None),
            Finding.severity,
        ) if False else Finding.created_at.desc()  # Fallback
    )

    result = await db.execute(query)
    findings = result.scalars().all()

    # Sort by severity manually
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings_sorted = sorted(findings, key=lambda f: severity_order.get(f.severity, 5))

    return [_finding_to_response(f) for f in findings_sorted]


@project_findings_router.get("/{project_id}/findings/stats", response_model=FindingStats)
async def get_finding_stats(project_id: str, db: DB, current_user: CurrentUser):
    findings_result = await db.execute(
        select(Finding).where(
            Finding.project_id == project_id,
            Finding.is_duplicate == False,
        )
    )
    findings = findings_result.scalars().all()

    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    by_status = {}
    by_tool = {}

    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_status[f.status] = by_status.get(f.status, 0) + 1
        by_tool[f.source_tool] = by_tool.get(f.source_tool, 0) + 1

    return FindingStats(
        total=len(findings),
        by_severity=by_severity,
        by_status=by_status,
        by_tool=by_tool,
    )


@project_findings_router.post("/{project_id}/compare", response_model=ScanComparisonResponse)
async def compare_scans(
    project_id: str,
    data: ScanComparisonRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Compare findings between two scans."""
    # Get findings for scan A
    result_a = await db.execute(
        select(Finding).where(Finding.scan_id == data.scan_a_id, Finding.is_duplicate == False)
    )
    findings_a = {f.fingerprint: f for f in result_a.scalars().all() if f.fingerprint}

    # Get findings for scan B
    result_b = await db.execute(
        select(Finding).where(Finding.scan_id == data.scan_b_id, Finding.is_duplicate == False)
    )
    findings_b = {f.fingerprint: f for f in result_b.scalars().all() if f.fingerprint}

    fps_a = set(findings_a.keys())
    fps_b = set(findings_b.keys())

    new_fps = fps_b - fps_a
    resolved_fps = fps_a - fps_b
    unchanged_fps = fps_a & fps_b

    # Save comparison
    comparison = ScanComparison(
        project_id=project_id,
        scan_a_id=data.scan_a_id,
        scan_b_id=data.scan_b_id,
        new_findings=len(new_fps),
        resolved_findings=len(resolved_fps),
        unchanged_findings=len(unchanged_fps),
        comparison_data={
            "new": [str(findings_b[fp].id) for fp in new_fps],
            "resolved": [str(findings_a[fp].id) for fp in resolved_fps],
        },
    )
    db.add(comparison)
    await db.flush()

    return ScanComparisonResponse(
        new_findings=len(new_fps),
        resolved_findings=len(resolved_fps),
        unchanged_findings=len(unchanged_fps),
        new_finding_ids=[str(findings_b[fp].id) for fp in new_fps],
        resolved_finding_ids=[str(findings_a[fp].id) for fp in resolved_fps],
    )
