import asyncio
import logging
from uuid import UUID

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="scan.execute")
def execute_scan_task(self, scan_id: str, profile_name: str, targets: list[str], scope_targets: list[str], config: dict | None = None):
    """Celery task to execute a scan pipeline."""
    logger.info(f"Starting scan task: {scan_id} with profile {profile_name}")

    async def _run():
        from app.core.database import async_session
        from app.core.events import event_manager
        from app.orchestrator.chain_logic import ChainLogicEngine
        from app.orchestrator.engine import PipelineEngine
        from app.orchestrator.profiles import get_profile
        from app.tools.registry import tool_registry

        profile = get_profile(profile_name)
        if not profile:
            logger.error(f"Unknown profile: {profile_name}")
            return

        async with async_session() as session:
            engine = PipelineEngine(
                tool_registry=tool_registry,
                chain_engine=ChainLogicEngine(),
                event_manager=event_manager,
                db_session=session,
            )
            await engine.execute_scan(
                scan_id=UUID(scan_id),
                profile=profile,
                targets=targets,
                scope_targets=scope_targets,
                custom_config=config,
            )
            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    except Exception as e:
        logger.error(f"Scan task {scan_id} failed: {e}")
        raise
    finally:
        loop.close()

    return {"scan_id": scan_id, "status": "completed"}


@celery_app.task(name="scan.cancel")
def cancel_scan_task(scan_id: str):
    """Cancel a running scan."""
    logger.info(f"Cancelling scan: {scan_id}")
    # In production, this would communicate with the running task
    return {"scan_id": scan_id, "status": "cancelled"}
