import redis.asyncio as redis
from typing import Optional
from app.config.settings import settings
from app.core.logger import logger

class RedisClient:
    def __init__(self):
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=10,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    async def ping(self) -> bool:
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def is_duplicate_delivery(self, delivery_id: str) -> bool:
        """
        Uses SETNX to mark a webhook delivery ID. Returns True if it was already processed.
        Sets a TTL of 5 minutes.
        """
        from app.cache.cache_keys import webhook_delivery_key
        key = webhook_delivery_key(delivery_id)
        # setnx returns 1 if set, 0 if it already existed
        is_new = await self.client.setnx(key, "1")
        if is_new:
            await self.client.expire(key, 300) # 5 minutes TTL
            return False
        return True

    async def acquire_pr_lock(self, repo_name: str, pr_number: int) -> bool:
        """
        Tries to acquire a lock for a specific PR. Returns True if successfully locked.
        """
        from app.cache.cache_keys import pr_lock_key
        key = pr_lock_key(repo_name, pr_number)
        # Lock expires in 1 hour in case process crashes
        return bool(await self.client.set(key, "locked", nx=True, ex=3600))

    async def release_pr_lock(self, repo_name: str, pr_number: int) -> None:
        from app.cache.cache_keys import pr_lock_key
        key = pr_lock_key(repo_name, pr_number)
        await self.client.delete(key)

    async def set_pr_status(self, repo_name: str, pr_number: int, status: str) -> None:
        """
        Status can be QUEUED, RUNNING, COMPLETED, FAILED.
        """
        from app.cache.cache_keys import pr_status_key
        key = pr_status_key(repo_name, pr_number)
        await self.client.set(key, status, ex=86400) # Keep status for 24 hours

    async def get_pr_status(self, repo_name: str, pr_number: int) -> Optional[str]:
        from app.cache.cache_keys import pr_status_key
        key = pr_status_key(repo_name, pr_number)
        return await self.client.get(key)

    async def close(self):
        await self.client.aclose()

redis_client = RedisClient()
