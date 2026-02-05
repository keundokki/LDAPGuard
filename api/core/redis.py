import logging
from typing import Optional

import redis.asyncio as redis

from api.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client instance."""
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = await redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    return _redis_client


async def close_redis_client():
    """Close Redis client connection."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")
