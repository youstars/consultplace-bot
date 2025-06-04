import redis.asyncio as redis
from aiogram.fsm.storage.redis import RedisStorage
from consultplace_bot.config import settings

_redis = redis.from_url(settings.redis_url, decode_responses=True)
storage = RedisStorage(_redis)