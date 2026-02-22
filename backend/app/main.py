import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.audit import AuditLogMiddleware
from app.api.v1.router import api_router
from app.api.v1.websocket import router as ws_router
from app.config import settings

logger = logging.getLogger(__name__)


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
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Audit logging
app.add_middleware(AuditLogMiddleware)

# API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }
