from typing import Any
import msgpack

# import aioredis
import redis.asyncio as redis


from datetime import datetime

from app.core.load_env import ENVConfig
from app.core.logger_config import get_logger

logger = get_logger(__name__)

class RedisSerializer:
    @staticmethod
    def serialize(data: Any) -> bytes:
        """
        Convert datetime objects to string before serializing with msgpack.
        """

        def default(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()  # Convert datetime to string
            raise TypeError(f"Type {type(obj)} not serializable")

        return msgpack.packb(data, default=default, use_bin_type=True)

    @staticmethod
    def deserialize(serialized_data: bytes) -> Any:
        """
        Deserialize msgpack bytes and convert datetime strings back to datetime objects.
        """

        def object_hook(obj):
            for key, value in obj.items():
                if isinstance(value, str) and value.endswith("Z"):
                    try:
                        obj[key] = datetime.fromisoformat(
                            value
                        )  # Convert string back to datetime
                    except ValueError:
                        pass  # If it fails, keep it as a string
            return obj

        return msgpack.unpackb(serialized_data, object_hook=object_hook, raw=False)


# Global Redis client
redis_client = None


# Initialize Redis client
async def init_redis():
    global redis_client
    redis_client = await redis.from_url(ENVConfig.REDIS_URL)
    logger.info("Connected to Redis DB")


# Close Redis connection
async def close_redis():
    if redis_client:
        await redis_client.close()
        logger.info("Redis DB closed")


# Get Redis client
async def get_redis_cache():
    return redis_client


# Serializer instance
serializer = RedisSerializer()
