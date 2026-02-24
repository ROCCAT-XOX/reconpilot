import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.middleware.audit import AuditLogMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.router import api_router
from app.api.v1.websocket import router as ws_router
from app.config import settings
from app.core.logging import generate_request_id, request_id_var, setup_logging

# Initialize structured logging
setup_logging(environment=settings.ENVIRONMENT)

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or generate_request_id()
        request_id_var.set(req_id)
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        response.headers["X-Request-ID"] = req_id
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "status": response.status_code,
                "duration_ms": round(duration_ms, 1),
                "request_id": req_id,
            },
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup health checks
    # Database check
    try:
        from sqlalchemy import text

        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection OK")
    except Exception as e:
        logger.warning(f"⚠️  Database health check failed: {e}")

    # Redis check
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.ping()
        logger.info("✅ Redis connection OK")
    except Exception as e:
        logger.warning(f"⚠️  Redis health check failed: {e}")

    global _app_started_at
    _app_started_at = datetime.now(UTC)

    yield

    # Shutdown cleanup
    try:
        from app.core.redis import close_redis
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Redis cleanup error: {e}")

    try:
        from app.core.database import engine
        await engine.dispose()
        logger.info("Database engine disposed")
    except Exception as e:
        logger.warning(f"Database cleanup error: {e}")


app = FastAPI(
    redirect_slashes=True,
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS — allow all origins only in non-production environments
cors_origins = settings.BACKEND_CORS_ORIGINS
if settings.ENVIRONMENT != "production" and "*" not in cors_origins:
    cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Request ID tracking (outermost = runs first)
app.add_middleware(RequestIDMiddleware)

# Rate limiting (Redis-based, must be before audit)
app.add_middleware(RateLimitMiddleware)

# Audit logging
app.add_middleware(AuditLogMiddleware)

# App startup time for uptime tracking
_app_started_at: datetime | None = None

# API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Enhanced health check: DB, Redis, Celery connectivity."""
    checks: dict[str, str] = {}
    overall = "healthy"

    # Database check
    try:
        from sqlalchemy import text
        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        overall = "degraded"

    # Redis check
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        overall = "degraded"

    # Celery worker check (via Redis inspect)
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        # Check if any celery worker keys exist
        worker_keys = await r.keys("celery-task-meta-*")
        checks["celery"] = "ok"
        checks["celery_task_count"] = str(len(worker_keys))
    except Exception:
        checks["celery"] = "unknown"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }


@app.get(f"{settings.API_V1_PREFIX}/status")
async def app_status():
    """Application status endpoint: version, uptime, stats."""
    now = datetime.now(UTC)
    uptime_seconds = (now - _app_started_at).total_seconds() if _app_started_at else 0

    # Last scan time
    last_scan_time = None
    try:
        from sqlalchemy import select, desc
        from app.core.database import async_session
        from app.models.scan import Scan
        async with async_session() as session:
            result = await session.execute(
                select(Scan.completed_at)
                .where(Scan.completed_at.isnot(None))
                .order_by(desc(Scan.completed_at))
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                last_scan_time = row.isoformat()
    except Exception:
        pass

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(uptime_seconds),
        "started_at": _app_started_at.isoformat() if _app_started_at else None,
        "last_scan_completed": last_scan_time,
        "timestamp": now.isoformat(),
    }


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }
