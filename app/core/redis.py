from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

# The client connects lazily, so importing this module never needs Redis to be up.
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client
