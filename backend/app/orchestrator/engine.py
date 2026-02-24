import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import WebSocketEventManager
from app.models.finding import Finding
from app.models.scan import Scan, ScanJob
from app.orchestrator.chain_logic import ChainLogicEngine
from app.orchestrator.profiles import ScanProfile
from app.services.finding_service import compute_finding_fingerprint
from app.services.scope_validator import ScopeValidator
from app.orchestrator.auto_discover import AutoDiscoverService
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ScopeViolationError(Exception):
    """Raised when a scan target is outside the authorized scope."""
    pass


class PipelineEngine:
    """
    Orchestrates scan phase execution and tool invocation.

    Responsibilities:
    - Phase management (sequential)
    - Tool execution (parallel within a phase)
    - Chain Logic delegation
    - Live status updates via WebSocket
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        chain_engine: ChainLogicEngine,
        event_manager: WebSocketEventManager,
        db_session: AsyncSession,
    ):
        self.tools = tool_registry
        self.chain_engine = chain_engine
        self.events = event_manager
        self.db = db_session
        self.auto_discover = AutoDiscoverService(tool_registry)
        self._cancelled: set[str] = set()
        self._paused: set[str] = set()

    def cancel_scan(self, scan_id: str):
        self._cancelled.add(scan_id)

    def pause_scan(self, scan_id: str):
        self._paused.add(scan_id)

    def resume_scan(self, scan_id: str):
        self._paused.discard(scan_id)

    async def execute_scan(
        self,
        scan_id: UUID,
        profile: ScanProfile,
        targets: list[str],
        scope_targets: list[str],
        custom_config: dict | None = None,
    ) -> None:
        """Execute a complete scan according to the profile."""
        scan_id_str = str(scan_id)

        # --- Mandatory scope enforcement (pre-scan hook) ---
        self._enforce_scope(targets, scope_targets)

        await self.events.emit(scan_id, "scan.started", {
            "profile": profile.name,
            "targets": targets,
        })

        # Update scan status
        from sqlalchemy import select
        result = await self.db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan:
            scan.status = "running"
            scan.started_at = datetime.now(UTC)
            await self.db.flush()

        discovered_targets: dict[str, set] = {
            "domains": set(targets),
            "urls": set(),
            "hosts": set(),
        }

        try:
            # --- Auto-Discovery Phase ---
            ad_config = self.auto_discover.parse_config(custom_config or {})
            if any([ad_config.subdomains, ad_config.technologies, ad_config.ports]):
                await self.events.emit(scan_id, "autodiscover.started", {})
                ad_result = await self.auto_discover.run(
                    targets=targets,
                    config=ad_config,
                    scope_targets=scope_targets,
                )
                discovered_targets["domains"].update(ad_result.subdomains)
                discovered_targets["urls"].update(ad_result.urls)
                discovered_targets["hosts"].update(ad_result.hosts)

                # Override nmap config for full port scan if requested
                if ad_result.full_port_scan and custom_config is not None:
                    custom_config.setdefault("scan_type", "full")

                await self.events.emit(scan_id, "autodiscover.completed", {
                    "subdomains": len(ad_result.subdomains),
                    "urls": len(ad_result.urls),
                    "technologies": len(ad_result.technologies),
                    "full_port_scan": ad_result.full_port_scan,
                })

            for phase in sorted(profile.phases, key=lambda p: p.order):
                # Check cancellation
                if scan_id_str in self._cancelled:
                    await self._update_scan_status(scan_id, "cancelled")
                    await self.events.emit(scan_id, "scan.cancelled", {})
                    return

                # Check pause
                while scan_id_str in self._paused:
                    await asyncio.sleep(1)

                await self.events.emit(scan_id, "phase.started", {
                    "phase": phase.name,
                    "order": phase.order,
                })

                tasks = []
                for tool_config in phase.tools:
                    if not tool_config.enabled:
                        continue

                    wrapper = self.tools.get(tool_config.tool_name)
                    if wrapper is None:
                        logger.warning(f"Tool '{tool_config.tool_name}' not found, skipping")
                        continue

                    tool_targets = self._resolve_targets(
                        tool_config.tool_name, discovered_targets, targets
                    )

                    for target in tool_targets:
                        config = {**tool_config.config, **(custom_config or {})}
                        tasks.append(
                            self._execute_tool(
                                scan_id=scan_id,
                                wrapper=wrapper,
                                target=target,
                                config=config,
                                scope_targets=scope_targets,
                                phase_name=phase.name,
                            )
                        )

                if phase.parallel:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    results = []
                    for task in tasks:
                        r = await task
                        results.append(r)

                # Chain Logic evaluation
                for r in results:
                    if isinstance(r, Exception):
                        logger.error(f"Tool execution failed: {r}")
                        continue
                    new_targets = await self.chain_engine.evaluate(r, discovered_targets)
                    for target_type, values in new_targets.items():
                        discovered_targets.setdefault(target_type, set()).update(values)

                await self.events.emit(scan_id, "phase.completed", {
                    "phase": phase.name,
                })

            # Scan completed
            await self._update_scan_status(scan_id, "completed")
            finding_count = await self._count_findings(scan_id)
            await self.events.emit(scan_id, "scan.completed", {
                "total_findings": finding_count,
            })

        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}")
            await self._update_scan_status(scan_id, "failed")
            await self.events.emit(scan_id, "scan.failed", {"error": str(e)})

    async def _execute_tool(
        self, scan_id, wrapper, target, config, scope_targets, phase_name,
    ):
        """Execute a single tool and save results."""
        await self.events.emit(scan_id, "tool.started", {
            "tool": wrapper.name,
            "target": target,
            "phase": phase_name,
        })

        result = await wrapper.run(
            target=target,
            config=config,
            scope_targets=scope_targets,
        )

        await self._save_scan_job(scan_id, wrapper.name, target, result, phase_name)
        await self._save_findings(scan_id, result)

        await self.events.emit(scan_id, "tool.completed", {
            "tool": wrapper.name,
            "target": target,
            "findings_count": len(result.findings),
            "status": result.status.value,
            "duration": result.duration_seconds,
        })

        return result

    def _resolve_targets(self, tool_name, discovered, primary_targets):
        """Determine which targets a tool should scan."""
        url_tools = {"nikto", "nuclei", "ffuf", "sqlmap"}
        if tool_name in url_tools and discovered.get("urls"):
            return list(discovered["urls"])

        host_tools = {"nmap"}
        if tool_name in host_tools and discovered.get("hosts"):
            return list(discovered["hosts"])

        return list(discovered.get("domains", set()) or primary_targets)

    async def _save_scan_job(self, scan_id, tool_name, target, result, phase):
        """Save a ScanJob to the database."""
        job = ScanJob(
            scan_id=scan_id,
            tool_name=tool_name,
            phase=phase,
            status=result.status.value,
            target=target,
            duration_seconds=int(result.duration_seconds),
            error_message="\n".join(result.errors) if result.errors else None,
        )
        self.db.add(job)
        await self.db.flush()

    async def _save_findings(self, scan_id, result):
        """Save findings with deduplication."""
        from sqlalchemy import select

        # Get project_id from scan
        scan_result = await self.db.execute(select(Scan).where(Scan.id == scan_id))
        scan = scan_result.scalar_one_or_none()
        if not scan:
            return

        for f in result.findings:
            fingerprint = compute_finding_fingerprint(
                target_host=f.get("target_host", ""),
                target_port=f.get("target_port"),
                target_url=f.get("target_url"),
                cve_id=f.get("cve_id"),
                cwe_id=f.get("cwe_id"),
                title=f.get("title", ""),
            )

            # Check for duplicate
            existing = await self.db.execute(
                select(Finding).where(
                    Finding.project_id == scan.project_id,
                    Finding.fingerprint == fingerprint,
                )
            )
            if existing.scalar_one_or_none():
                continue  # Skip duplicate

            finding = Finding(
                scan_id=scan_id,
                project_id=scan.project_id,
                title=f.get("title", "Unknown"),
                description=f.get("description"),
                severity=f.get("severity", "info"),
                cve_id=f.get("cve_id"),
                cwe_id=f.get("cwe_id"),
                target_host=f.get("target_host"),
                target_port=f.get("target_port"),
                target_protocol=f.get("target_protocol"),
                target_url=f.get("target_url"),
                target_service=f.get("target_service"),
                source_tool=result.tool_name,
                raw_evidence=f.get("raw_evidence"),
                fingerprint=fingerprint,
            )
            self.db.add(finding)

        await self.db.flush()

    async def _update_scan_status(self, scan_id, status):
        from sqlalchemy import select
        result = await self.db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan:
            scan.status = status
            if status in ("completed", "failed", "cancelled"):
                scan.completed_at = datetime.now(UTC)
            await self.db.flush()

    @staticmethod
    def _enforce_scope(targets: list[str], scope_targets: list[str]) -> None:
        """Validate all targets against scope before scan execution.

        Raises ScopeViolationError if any target is outside scope.
        """
        if not scope_targets:
            raise ScopeViolationError(
                "No scope defined. Cannot execute scan without an authorized scope."
            )

        # Build scope entries from flat list (assume domain type for strings)
        allowed = []
        for st in scope_targets:
            # Detect type heuristically
            import ipaddress
            try:
                ipaddress.ip_address(st)
                allowed.append({"type": "ip", "value": st})
            except ValueError:
                if "/" in st and any(c.isdigit() for c in st.split("/")[0]):
                    allowed.append({"type": "ip_range", "value": st})
                else:
                    allowed.append({"type": "domain", "value": st})

        validator = ScopeValidator(allowed_targets=allowed)
        out_of_scope = []
        for target in targets:
            result = validator.validate(target)
            if not result.is_valid:
                out_of_scope.append(target)

        if out_of_scope:
            raise ScopeViolationError(
                f"Scan blocked: the following targets are outside the authorized scope: "
                f"{', '.join(out_of_scope)}. Define them in the project scope first."
            )

    async def _count_findings(self, scan_id) -> int:
        from sqlalchemy import func, select
        result = await self.db.execute(
            select(func.count()).select_from(Finding).where(Finding.scan_id == scan_id)
        )
        return result.scalar() or 0
