import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def blacklist_token(token: str, ttl_seconds: int) -> None:
    """Add a token to the blacklist with TTL matching its expiry."""
    r = await get_redis()
    await r.setex(f"token_blacklist:{token}", ttl_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    r = await get_redis()
    return await r.exists(f"token_blacklist:{token}") > 0
