import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("reconforge.audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        if request.url.path.startswith("/api/"):
            logger.info(
                "method=%s path=%s status=%s duration=%.3fs ip=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration,
                request.client.host if request.client else "unknown",
            )

        return response
