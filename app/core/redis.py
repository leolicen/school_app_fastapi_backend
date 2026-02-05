from fastapi import Depends
import redis.asyncio as redis
from typing import Annotated, AsyncGenerator

from .settings import settings


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    
    client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        yield client
    finally:
        await client.aclose()
        

RedisDep = Annotated[redis.Redis, Depends(get_redis)]
