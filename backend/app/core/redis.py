"""Redis connection manager and caching interface."""

from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings

# Global async redis connection
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Returns the shared Redis client or initializes a new connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,
        )
    return _redis_client


async def close_redis_connection():
    """Closes Redis connections on app shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
