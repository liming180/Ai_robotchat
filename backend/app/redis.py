"""
Redis connection and utilities.
"""

import redis.asyncio as redis
from typing import Optional
from app.config import settings

# Global Redis client
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get or create Redis client instance.
    """
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return redis_client


async def close_redis():
    """
    Close Redis connection.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def set_cache(key: str, value: str, expire_seconds: int = 21600):
    """
    Set a value in Redis cache with expiration.
    Default expiration: 6 hours.
    """
    r = await get_redis()
    await r.setex(key, expire_seconds, value)


async def get_cache(key: str) -> Optional[str]:
    """
    Get a value from Redis cache.
    """
    r = await get_redis()
    return await r.get(key)


async def delete_cache(key: str):
    """
    Delete a value from Redis cache.
    """
    r = await get_redis()
    await r.delete(key)
