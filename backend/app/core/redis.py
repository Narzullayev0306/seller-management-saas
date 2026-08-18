"""Redis helpers with graceful degradation.

Every operation silently falls back to "no cache / allow" when Redis is
disabled or unreachable, so the app keeps working without it (tests, etc.).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazily build a sync Redis client; None when disabled or unavailable."""
    global _client
    if not settings.redis_enabled or not settings.redis_url:
        return None
    if _client is None:
        try:
            import redis

            _client = redis.Redis.from_url(
                settings.redis_url,
                socket_connect_timeout=1,
                socket_timeout=2,
                decode_responses=True,
            )
            _client.ping()
        except Exception:
            logger.warning("Redis unavailable (%s); running without cache", settings.redis_url)
            _client = False
    return _client if _client is not False else None


def cache_get(key: str) -> Any | None:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("Redis GET failed for %s", key)
        return None


def cache_set(key: str, value: Any, ttl: int) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        logger.warning("Redis SET failed for %s", key)


def cache_invalidate(pattern: str) -> None:
    """Delete all keys matching a glob pattern (best effort)."""
    client = _get_client()
    if client is None:
        return
    try:
        for key in client.scan_iter(match=pattern, count=200):
            client.delete(key)
    except Exception:
        logger.warning("Redis invalidation failed for %s", pattern)
