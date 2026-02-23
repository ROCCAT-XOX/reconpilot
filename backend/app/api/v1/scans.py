import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser, PaginatedResponse, Pagination, PentesterOrAbove
from app.models.scan import Scan, ScanJob
from app.models.scope import ScopeTarget
from app.orchestrator.profiles import get_profile, list_profiles
from app.schemas.scan import ScanCreate, ScanJobResponse, ScanResponse
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ScanResponse])
async def list_scans(db: DB, current_user: CurrentUser, pagination: Pagination):
    """List all scans across all projects."""
    total_q = select(func.count()).select_from(Scan)
    total = (await db.execute(total_q)).scalar() or 0
    result = await db.execute(
        select(Scan)
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


async def _run_scan_fallback(scan_id: str, profile_name: str, targets: list[str], scope_targets: list[str], config: dict):
    """Run scan as asyncio background task (fallback when Celery/Redis unavailable)."""
    from app.core.database import async_session
    from app.core.events import event_manager
    from app.orchestrator.chain_logic import ChainLogicEngine
    from app.orchestrator.engine import PipelineEngine
    from app.orchestrator.profiles import get_profile
    from app.tools.registry import tool_registry

    logger.info(f"[Fallback] Starting scan {scan_id} in-process")

    async with async_session() as db:
        try:
            profile = get_profile(profile_name)
            if not profile:
                logger.error(f"[Fallback] Unknown profile: {profile_name}")
                return

            engine = PipelineEngine(
                tool_registry=tool_registry,
                chain_engine=ChainLogicEngine(),
                event_manager=event_manager,
                db_session=db,
            )
            from uuid import UUID
            await engine.execute_scan(
                scan_id=UUID(scan_id),
                profile=profile,
                targets=targets,
                scope_targets=scope_targets,
                custom_config=config,
            )
            await db.commit()
        except Exception as e:
            logger.error(f"[Fallback] Scan {scan_id} failed: {e}")
            try:
                from sqlalchemy import select as sel
                result = await db.execute(sel(Scan).where(Scan.id == scan_id))
                scan = result.scalar_one_or_none()
                if scan and scan.status not in ("completed", "failed", "cancelled"):
                    scan.status = "failed"
                    scan.completed_at = datetime.now(UTC)
                    await db.commit()
            except Exception:
                logger.exception(f"[Fallback] Failed to update scan {scan_id} status")


def _try_celery_dispatch(scan_id: str, profile: str, targets: list[str], scope_targets: list[str], config: dict) -> bool:
    """Try to dispatch scan to Celery. Returns True if successful."""
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
    if result != 0:
        raise ConnectionError(f"Redis not reachable at {host}:{port}")

    from workers.tasks.scan_tasks import execute_scan_task
    execute_scan_task.delay(scan_id, profile, targets, scope_targets, config)
    return True


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

    scan_id_str = str(scan.id)
    dispatched = False

    # Try Celery first
    try:
        dispatched = _try_celery_dispatch(scan_id_str, data.profile, targets, scope_targets_list, data.config)
        logger.info(f"Scan {scan_id_str} dispatched to Celery")
    except Exception as e:
        logger.warning(f"Celery dispatch failed for scan {scan_id_str}: {e}. Falling back to in-process execution.")

    # Fallback: run as asyncio background task
    if not dispatched:
        try:
            asyncio.get_event_loop().create_task(
                _run_scan_fallback(scan_id_str, data.profile, targets, scope_targets_list, data.config)
            )
            logger.info(f"Scan {scan_id_str} started as in-process fallback")
            dispatched = True
        except Exception as e:
            logger.error(f"Fallback execution also failed for scan {scan_id_str}: {e}")
            scan.status = "failed"
            scan.completed_at = datetime.now(UTC)
            await db.flush()

    return ScanResponse.model_validate(scan)


@project_scans_router.post("/{project_id}/scans/{scan_id}/retry", response_model=ScanResponse)
async def retry_scan(project_id: str, scan_id: str, db: DB, current_user: PentesterOrAbove):
    """Retry a failed or cancelled scan."""
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id, Scan.project_id == project_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status not in ("failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Scan cannot be retried (status: {scan.status})")

    # Reset scan state
    scan.status = "pending"
    scan.started_at = None
    scan.completed_at = None
    await db.flush()

    # Re-fetch scope
    scope_result = await db.execute(
        select(ScopeTarget).where(
            ScopeTarget.project_id == project_id,
            ScopeTarget.is_excluded == False,
        )
    )
    scope_targets_list = [st.target_value for st in scope_result.scalars().all()]
    targets = scan.config.get("targets", scope_targets_list) or scope_targets_list

    scan_id_str = str(scan.id)
    dispatched = False

    try:
        dispatched = _try_celery_dispatch(scan_id_str, scan.profile, targets, scope_targets_list, scan.config)
    except Exception as e:
        logger.warning(f"Celery dispatch failed for retry {scan_id_str}: {e}")

    if not dispatched:
        try:
            asyncio.get_event_loop().create_task(
                _run_scan_fallback(scan_id_str, scan.profile, targets, scope_targets_list, scan.config)
            )
        except Exception as e:
            logger.error(f"Fallback retry also failed for scan {scan_id_str}: {e}")
            scan.status = "failed"
            scan.completed_at = datetime.now(UTC)
            await db.flush()

    return ScanResponse.model_validate(scan)


# Tools and profiles endpoints

@router.get("/tools/available")
async def list_tools(current_user: CurrentUser):
    return tool_registry.list_tools()


@router.get("/profiles/available")
async def get_profiles(current_user: CurrentUser):
    return list_profiles()
