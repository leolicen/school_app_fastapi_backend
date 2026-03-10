from fastapi import Depends
import redis.asyncio as redis
from typing import Annotated, AsyncGenerator

from .settings import settings


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Yield an async Redis client and ensure it is closed after use.

    Uses UTF-8 encoding with decoded responses (strings instead of bytes).
    The connection is always closed in the finally block, even on error.
    """
    client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

    try:
        yield client
    finally:
        await client.aclose()


# Redis session dependency
RedisDep = Annotated[redis.Redis, Depends(get_redis)]
