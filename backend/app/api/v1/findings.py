from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser, PaginatedResponse, Pagination, PentesterOrAbove
from app.models.finding import Finding, FindingComment
from app.models.report import ScanComparison
from app.schemas.finding import (
    CommentCreate,
    CommentResponse,
    FindingResponse,
    FindingStats,
    FindingUpdate,
    ScanComparisonRequest,
    ScanComparisonResponse,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[FindingResponse])
async def list_all_findings(
    db: DB,
    current_user: CurrentUser,
    pagination: Pagination,
    severity: str | None = Query(None),
    status: str | None = Query(None),
    source_tool: str | None = Query(None),
    include_duplicates: bool = Query(False),
):
    """List all findings (across all projects the user can see)."""
    base_query = select(Finding)

    if severity:
        base_query = base_query.where(Finding.severity == severity)
    if status:
        base_query = base_query.where(Finding.status == status)
    if source_tool:
        base_query = base_query.where(Finding.source_tool == source_tool)
    if not include_duplicates:
        base_query = base_query.where(Finding.is_duplicate == False)  # noqa: E712

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar()

    result = await db.execute(
        base_query.order_by(Finding.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.per_page)
    )
    findings = result.scalars().all()

    return PaginatedResponse(
        items=[FindingResponse.model_validate(f) for f in findings],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)


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
    return FindingResponse.model_validate(finding)


@router.put("/{finding_id}/verify")
async def verify_finding(finding_id: str, db: DB, current_user: PentesterOrAbove):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = "confirmed"
    finding.verified_by = current_user.id
    finding.verified_at = datetime.now(UTC)
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

project_findings_router = APIRouter()


@project_findings_router.get("/{project_id}/findings", response_model=PaginatedResponse[FindingResponse])
async def list_project_findings(
    project_id: str,
    db: DB,
    current_user: CurrentUser,
    pagination: Pagination,
    severity: str | None = Query(None),
    status: str | None = Query(None),
    source_tool: str | None = Query(None),
    include_duplicates: bool = Query(False),
):
    base_query = select(Finding).where(Finding.project_id == project_id)

    if severity:
        base_query = base_query.where(Finding.severity == severity)
    if status:
        base_query = base_query.where(Finding.status == status)
    if source_tool:
        base_query = base_query.where(Finding.source_tool == source_tool)
    if not include_duplicates:
        base_query = base_query.where(Finding.is_duplicate == False)

    # Count
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar()

    result = await db.execute(
        base_query.order_by(Finding.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.per_page)
    )
    findings = result.scalars().all()

    # Sort by severity manually
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings_sorted = sorted(findings, key=lambda f: severity_order.get(f.severity, 5))

    return PaginatedResponse(
        items=[FindingResponse.model_validate(f) for f in findings_sorted],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


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
    result_a = await db.execute(
        select(Finding).where(Finding.scan_id == data.scan_a_id, Finding.is_duplicate == False)
    )
    findings_a = {f.fingerprint: f for f in result_a.scalars().all() if f.fingerprint}

    result_b = await db.execute(
        select(Finding).where(Finding.scan_id == data.scan_b_id, Finding.is_duplicate == False)
    )
    findings_b = {f.fingerprint: f for f in result_b.scalars().all() if f.fingerprint}

    fps_a = set(findings_a.keys())
    fps_b = set(findings_b.keys())

    new_fps = fps_b - fps_a
    resolved_fps = fps_a - fps_b
    unchanged_fps = fps_a & fps_b

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
