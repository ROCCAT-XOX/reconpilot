import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Per-path rate limit config: (max_requests, window_seconds)
RATE_LIMIT_RULES: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login": (5, 60),
    "/api/v1/auth/login/json": (5, 60),
    "/api/v1/auth/refresh": (10, 60),
}

# Default rate limit for all other endpoints
DEFAULT_RATE_LIMIT = (100, 60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware with per-path rules."""

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        path = request.url.path

        max_requests, window = RATE_LIMIT_RULES.get(path, DEFAULT_RATE_LIMIT)
        key = f"rate_limit:{client_ip}:{path}"

        try:
            from app.core.redis import get_redis
            r = await get_redis()

            current = await r.incr(key)
            if current == 1:
                await r.expire(key, window)

            ttl = await r.ttl(key)

            if current > max_requests:
                logger.warning(
                    f"Rate limit exceeded: {client_ip} on {path} "
                    f"({current}/{max_requests} in {window}s)"
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={
                        "Retry-After": str(max(ttl, 1)),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, max_requests - current)
            )
            return response

        except Exception as e:
            # If Redis is down, allow the request (fail-open)
            logger.warning(f"Rate limiter Redis error (fail-open): {e}")
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For behind reverse proxy."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
