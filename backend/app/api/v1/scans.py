from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser, PaginatedResponse, Pagination, PentesterOrAbove
from app.models.scan import Scan, ScanJob
from app.models.scope import ScopeTarget
from app.orchestrator.profiles import get_profile, list_profiles
from app.schemas.scan import ScanCreate, ScanJobResponse, ScanResponse
from app.tools.registry import tool_registry

router = APIRouter()


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanResponse.model_validate(scan)


@router.get("/{scan_id}/jobs", response_model=list[ScanJobResponse])
async def get_scan_jobs(scan_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(ScanJob).where(ScanJob.scan_id == scan_id).order_by(ScanJob.created_at)
    )
    jobs = result.scalars().all()
    return [
        ScanJobResponse(
            id=str(j.id),
            scan_id=str(j.scan_id),
            tool_name=j.tool_name,
            phase=j.phase,
            status=j.status,
            target=j.target,
            duration_seconds=j.duration_seconds,
            error_message=j.error_message,
            started_at=j.started_at.isoformat() if j.started_at else None,
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
        )
        for j in jobs
    ]


@router.get("/{scan_id}/timeline")
async def get_scan_timeline(scan_id: str, db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(ScanJob).where(ScanJob.scan_id == scan_id).order_by(ScanJob.created_at)
    )
    jobs = result.scalars().all()
    events = []
    for j in jobs:
        if j.started_at:
            events.append({
                "timestamp": j.started_at.isoformat(),
                "event": "tool.started",
                "tool": j.tool_name,
                "phase": j.phase,
                "details": {"target": j.target},
            })
        if j.completed_at:
            events.append({
                "timestamp": j.completed_at.isoformat(),
                "event": "tool.completed",
                "tool": j.tool_name,
                "phase": j.phase,
                "details": {
                    "target": j.target,
                    "status": j.status,
                    "duration": j.duration_seconds,
                },
            })
    return sorted(events, key=lambda e: e["timestamp"])


@router.put("/{scan_id}/pause")
async def pause_scan(scan_id: str, db: DB, current_user: PentesterOrAbove):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != "running":
        raise HTTPException(status_code=400, detail="Scan is not running")
    scan.status = "paused"
    await db.flush()
    return {"detail": "Scan paused", "status": "paused"}


@router.put("/{scan_id}/resume")
async def resume_scan(scan_id: str, db: DB, current_user: PentesterOrAbove):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != "paused":
        raise HTTPException(status_code=400, detail="Scan is not paused")
    scan.status = "running"
    await db.flush()
    return {"detail": "Scan resumed", "status": "running"}


@router.put("/{scan_id}/cancel")
async def cancel_scan(scan_id: str, db: DB, current_user: PentesterOrAbove):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status not in ("running", "paused", "pending"):
        raise HTTPException(status_code=400, detail="Scan cannot be cancelled")
    scan.status = "cancelled"
    scan.completed_at = datetime.now(UTC)
    await db.flush()
    return {"detail": "Scan cancelled", "status": "cancelled"}


# --- Project-scoped scan endpoints ---

project_scans_router = APIRouter()


@project_scans_router.get("/{project_id}/scans", response_model=PaginatedResponse[ScanResponse])
async def list_project_scans(project_id: str, db: DB, current_user: CurrentUser, pagination: Pagination):
    # Count
    count_result = await db.execute(
        select(func.count()).select_from(Scan).where(Scan.project_id == project_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.per_page)
    )
    scans = result.scalars().all()
    return PaginatedResponse(
        items=[ScanResponse.model_validate(s) for s in scans],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


@project_scans_router.post("/{project_id}/scans", response_model=ScanResponse, status_code=201)
async def create_scan(project_id: str, data: ScanCreate, db: DB, current_user: PentesterOrAbove):
    profile = get_profile(data.profile)
    if not profile and data.profile != "custom":
        raise HTTPException(status_code=400, detail=f"Unknown profile: {data.profile}")

    if data.profile == "custom":
        selected_tools = data.config.get("tools", [])
        if not selected_tools:
            raise HTTPException(
                status_code=400,
                detail="Custom profile requires at least one tool to be selected",
            )

    scope_result = await db.execute(
        select(ScopeTarget).where(
            ScopeTarget.project_id == project_id,
            ScopeTarget.is_excluded == False,
        )
    )
    scope_targets_list = [st.target_value for st in scope_result.scalars().all()]

    targets = data.targets or scope_targets_list
    if not targets:
        raise HTTPException(status_code=400, detail="No targets specified and no scope defined")

    scan = Scan(
        project_id=project_id,
        name=data.name or f"{data.profile.title()} Scan",
        profile=data.profile,
        config=data.config,
        started_by=current_user.id,
    )
    db.add(scan)
    await db.flush()

    # Try to dispatch to Celery worker (best-effort, skip if Redis unavailable)
    try:
        import socket
        from urllib.parse import urlparse

        from app.config import settings
        parsed = urlparse(settings.REDIS_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            from workers.tasks.scan_tasks import execute_scan_task
            execute_scan_task.delay(
                str(scan.id), data.profile, targets, scope_targets_list, data.config
            )
    except Exception:
        pass

    return ScanResponse.model_validate(scan)


# Tools and profiles endpoints

@router.get("/tools/available")
async def list_tools(current_user: CurrentUser):
    return tool_registry.list_tools()


@router.get("/profiles/available")
async def get_profiles(current_user: CurrentUser):
    return list_profiles()
