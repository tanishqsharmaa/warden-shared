"""Redis Client Connection Pool Manager with Sentinel and RESP3 Support."""
import asyncio
import logging

import redis.asyncio as aioredis
from redis.asyncio.retry import Retry
from redis.asyncio.sentinel import Sentinel
from redis.backoff import ExponentialBackoff

from warden_shared.errors.exceptions import CacheUnavailableError

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """Manages resilient Redis connection pools supporting standalone and Sentinel topologies."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        sentinel_hosts: list[tuple[str, int]] | None = None,
        service_name: str = "mymaster",
        socket_timeout: float = 0.2,
        socket_connect_timeout: float = 0.5,
        max_connections: int = 50,
        retry_attempts: int = 3,
    ) -> None:
        self.redis_url = redis_url
        self.sentinel_hosts = sentinel_hosts
        self.service_name = service_name
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.max_connections = max_connections
        self.retry_attempts = retry_attempts
        self._client: aioredis.Redis | None = None
        self._sentinel: Sentinel | None = None
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get_client(self) -> aioredis.Redis:
        """Acquire or initialize async Redis client with configured timeouts and retry backoff."""
        async with self._get_lock():
            if self._client is not None:
                return self._client

            try:
                retry = Retry(ExponentialBackoff(cap=0.4, base=0.1), retries=self.retry_attempts)
                if self.sentinel_hosts:
                    self._sentinel = Sentinel(  # type: ignore[no-untyped-call]
                        sentinels=self.sentinel_hosts,
                        socket_timeout=self.socket_timeout,
                        socket_connect_timeout=self.socket_connect_timeout,
                        retry=retry,
                    )
                    self._client = self._sentinel.master_for(
                        self.service_name,
                        max_connections=self.max_connections,
                        socket_timeout=self.socket_timeout,
                        socket_connect_timeout=self.socket_connect_timeout,
                        decode_responses=True,
                        retry=retry,
                    )
                else:
                    self._client = aioredis.from_url(
                        self.redis_url,
                        max_connections=self.max_connections,
                        socket_timeout=self.socket_timeout,
                        socket_connect_timeout=self.socket_connect_timeout,
                        decode_responses=True,
                        retry=retry,
                    )

                # Test connection
                await self._client.ping()
                return self._client

            except Exception as exc:
                logger.warning("Redis connection failed or timed out: %s", exc)
                self._client = None
                raise CacheUnavailableError(
                    detail=f"Redis connection failed or timed out: {exc}"
                ) from exc

    async def ping(self) -> bool:
        """Verify Redis connectivity."""
        client = await self.get_client()
        res = await client.ping()
        return bool(res)

    async def close(self) -> None:
        """Cleanly close connection pools."""
        async with self._get_lock():
            if self._client is not None:
                await self._client.aclose()
                self._client = None
