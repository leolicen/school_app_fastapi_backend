import redis.asyncio as redis
from settings import settings

rdb = redis.from_url(settings.redis_url)
