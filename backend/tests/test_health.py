"""System health endpoints and request-tracing middleware."""

import re

import pytest

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


@pytest.mark.asyncio
async def test_health_returns_service_status(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "service" in body


@pytest.mark.asyncio
async def test_health_live_is_trivially_ok(client):
    resp = await client.get("/api/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready_reports_database_check(client):
    resp = await client.get("/api/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["request_id"]


@pytest.mark.asyncio
async def test_request_id_from_client_is_echoed(client):
    resp = await client.get("/api/health", headers={"X-Request-ID": "trace-me-123"})
    assert resp.headers["X-Request-ID"] == "trace-me-123"


@pytest.mark.asyncio
async def test_request_id_is_generated_when_missing(client):
    resp = await client.get("/api/health")
    assert UUID_RE.match(resp.headers["X-Request-ID"])


@pytest.mark.asyncio
async def test_security_headers_are_present(client):
    resp = await client.get("/api/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
