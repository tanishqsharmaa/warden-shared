"""Unit tests for Redis connection manager and resilient timeout handling."""
from unittest.mock import ANY, AsyncMock, patch

import pytest

from warden_shared.cache.redis_client import RedisConnectionManager
from warden_shared.errors.exceptions import CacheUnavailableError


@pytest.mark.asyncio
async def test_redis_client_initialization_and_ping():
    mgr = RedisConnectionManager("redis://localhost:6379")

    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("redis.asyncio.from_url", return_value=mock_client):
        client = await mgr.get_client()
        assert client is mock_client
        mock_client.ping.assert_called_once()

        ping_result = await mgr.ping()
        assert ping_result is True

        await mgr.close()
        mock_client.aclose.assert_called_once()

@pytest.mark.asyncio
async def test_redis_client_connection_timeout_handling():
    mgr = RedisConnectionManager("redis://unreachable-redis:6379")

    with patch("redis.asyncio.from_url", side_effect=TimeoutError("Connection timed out after 0.5s")):
        with pytest.raises(CacheUnavailableError) as exc_info:
            await mgr.get_client()
        assert exc_info.value.status_code == 503
        assert exc_info.value.error_code == "ERR_CACHE_UNAVAILABLE"
        assert "timed out" in exc_info.value.detail

@pytest.mark.asyncio
async def test_redis_client_sentinel_initialization():
    sentinel_hosts = [("sentinel-1", 26379), ("sentinel-2", 26379)]
    mgr = RedisConnectionManager(
        sentinel_hosts=sentinel_hosts,
        service_name="warden-master",
    )

    mock_master = AsyncMock()
    mock_master.ping.return_value = True

    with patch("warden_shared.cache.redis_client.Sentinel") as mock_sentinel_cls:
        mock_sentinel_instance = mock_sentinel_cls.return_value
        mock_sentinel_instance.master_for.return_value = mock_master

        client = await mgr.get_client()
        assert client is mock_master
        mock_master.ping.assert_called_once()
        mock_sentinel_instance.master_for.assert_called_once_with(
            "warden-master",
            max_connections=50,
            socket_timeout=0.2,
            socket_connect_timeout=0.5,
            decode_responses=True,
            retry=ANY,
        )

@pytest.mark.asyncio
async def test_redis_client_concurrent_initialization_lock():
    import asyncio
    mgr = RedisConnectionManager("redis://localhost:6379")

    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("redis.asyncio.from_url", return_value=mock_client) as mock_from_url:
        # Run 10 concurrent get_client() calls
        clients = await asyncio.gather(*(mgr.get_client() for _ in range(10)))
        assert len(clients) == 10
        # All callers get the exact same client instance
        for c in clients:
            assert c is mock_client
        # from_url must only be invoked once due to the asyncio lock
        mock_from_url.assert_called_once()

