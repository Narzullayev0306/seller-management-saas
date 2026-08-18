"""Redis-backed rate limiting with graceful fallback (allow) when Redis is off."""

from __future__ import annotations

import ipaddress
import logging
import time

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import ApiError
from app.core.redis import _get_client

logger = logging.getLogger(__name__)

_in_memory_store: dict[str, list[float]] = {}


def _peer_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _is_trusted_proxy(peer: str) -> bool:
    if not settings.trusted_proxies:
        return False
    try:
        addr = ipaddress.ip_address(peer)
    except ValueError:
        return False
    for entry in settings.trusted_proxies:
        try:
            if ipaddress.ip_address(entry) == addr:
                return True
        except ValueError:
            try:
                if addr in ipaddress.ip_network(entry, strict=False):
                    return True
            except ValueError:
                continue
    return False


def _client_ip(request: Request) -> str:
    """Client IP, honoring X-Forwarded-For only when the direct peer is a trusted proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    peer = _peer_ip(request)
    if forwarded and _is_trusted_proxy(peer):
        return forwarded.split(",")[0].strip()
    return peer


def check_rate_limit(request: Request, scope: str, limit: int, window: int) -> None:
    """Fixed-window limit per client IP with Redis + in-memory fallback; raises 429 when exceeded."""
    client = _get_client()
    key = f"rl:{scope}:{_client_ip(request)}"

    if client is not None:
        try:
            current = client.incr(key)
            if current == 1:
                client.expire(key, window)
            if current > limit:
                raise ApiError(429, "RATE_LIMITED", "Too many requests, please slow down")
            return
        except ApiError:
            raise
        except Exception:
            logger.warning("Redis rate limit check failed for %s, using fallback", key)

    # In-memory sliding fallback when Redis is disabled or unreachable
    now = time.time()
    timestamps = _in_memory_store.setdefault(key, [])
    # Filter out timestamps older than the window
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= limit:
        _in_memory_store[key] = timestamps
        raise ApiError(429, "RATE_LIMITED", "Too many requests, please slow down")
    timestamps.append(now)
    _in_memory_store[key] = timestamps
