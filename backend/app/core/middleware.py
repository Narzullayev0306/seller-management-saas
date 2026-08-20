"""Global HTTP middleware: request IDs, security headers, access logging.

- RequestIdMiddleware: attaches a request id (client-provided X-Request-ID or a
  fresh UUID) to every request/response and exposes it via request.state.
- SecurityHeadersMiddleware: hardens responses with standard security headers.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings

logger = logging.getLogger("access")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), payment=()"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
}

CSP_HEADER = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' https: ws: wss:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; form-action 'self'"
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Ensure every request has a traceable X-Request-ID."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            status = 500
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                status,
                duration_ms,
            )
            raise
        status = getattr(response, "status_code", 500)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            status,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if settings.app_env != "development":
            response.headers.setdefault("Content-Security-Policy", CSP_HEADER)
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
        return response
