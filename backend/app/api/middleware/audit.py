import logging
import time
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.database import async_session
from app.models.audit_log import AuditLog
from app.core.security import verify_token

logger = logging.getLogger("reconforge.audit")

# Map HTTP methods + paths to action names
ACTION_MAP = {
    ("POST", "/auth/login"): "user.login",
    ("POST", "/auth/logout"): "user.logout",
    ("POST", "/auth/refresh"): "user.token_refresh",
    ("POST", "/users"): "user.created",
    ("DELETE", "/users"): "user.deactivated",
    ("POST", "/projects"): "project.created",
    ("PUT", "/projects"): "project.updated",
    ("DELETE", "/projects"): "project.archived",
    ("POST", "/members"): "project.member_added",
    ("DELETE", "/members"): "project.member_removed",
    ("POST", "/scope"): "scope.target_added",
    ("DELETE", "/scope"): "scope.target_removed",
    ("POST", "/scans"): "scan.started",
    ("PUT", "/scans"): "scan.updated",
    ("PUT", "/findings"): "finding.updated",
    ("POST", "/comments"): "finding.commented",
    ("POST", "/reports"): "report.generated",
}


def _resolve_action(method: str, path: str) -> str | None:
    """Resolve an audit action name from the request method and path."""
    for (m, p), action in ACTION_MAP.items():
        if method == m and p in path:
            return action
    return None


def _extract_user_id(request: Request) -> str | None:
    """Try to extract user_id from the Authorization header."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = verify_token(token)
        if payload:
            return payload.get("sub")
    return None


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        if not request.url.path.startswith("/api/"):
            return response

        # Log to console
        logger.info(
            "method=%s path=%s status=%s duration=%.3fs ip=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            request.client.host if request.client else "unknown",
        )

        # Write to DB for mutating operations
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            action = _resolve_action(request.method, request.url.path)
            if action and response.status_code < 400:
                user_id = _extract_user_id(request)
                try:
                    async with async_session() as session:
                        log_entry = AuditLog(
                            user_id=user_id if user_id else None,
                            action=action,
                            resource_type=request.url.path.split("/")[3] if len(request.url.path.split("/")) > 3 else None,
                            details={
                                "method": request.method,
                                "path": request.url.path,
                                "status": response.status_code,
                                "duration_ms": round(duration * 1000),
                            },
                            ip_address=request.client.host if request.client else None,
                        )
                        session.add(log_entry)
                        await session.commit()
                except Exception as e:
                    logger.error("Failed to write audit log: %s", e)

        return response
