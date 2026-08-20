"""Webhook endpoints: CRUD, signing, delivery via worker outbox processing."""

import pytest

from app.services.outbox_service import emit


async def _create_webhook(client, token: str, **overrides) -> dict:
    payload = {
        "name": "ERP Sync",
        "url": "https://example.com/hooks/sms",
        "events": ["order.created", "stock.low"],
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/v1/webhooks",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_webhook_crud_and_secret_masking(client, org_a):
    token = org_a["access_token"]
    webhook = await _create_webhook(client, token)
    # The signing secret is returned in full only on creation.
    assert "*" not in webhook["secret"]
    assert len(webhook["secret"]) >= 32

    resp = await client.get(
        "/api/v1/webhooks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 1
    assert "****" in listed[0]["secret"]

    resp = await client.patch(
        f"/api/v1/webhooks/{webhook['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"events": ["order.cancelled"], "is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["events"] == ["order.cancelled"]
    assert resp.json()["is_active"] is False

    resp = await client.delete(
        f"/api/v1/webhooks/{webhook['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_webhook_rejects_unknown_events(client, org_a):
    resp = await client.post(
        "/api/v1/webhooks",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
        json={
            "name": "Bad",
            "url": "https://example.com/h",
            "events": ["order.nonexistent"],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "WEBHOOK_INVALID_EVENTS"


@pytest.mark.asyncio
async def test_webhook_test_ping(client, org_a, monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "OK"

    calls = {}

    def fake_post(url, **kwargs):
        calls["url"] = url
        calls["headers"] = kwargs.get("headers", {})
        calls["body"] = kwargs.get("content", b"")
        assert kwargs["headers"]["X-Webhook-Signature"].startswith("sha256=")
        assert "X-Webhook-Timestamp" in kwargs["headers"]
        assert kwargs["headers"]["X-Webhook-Event"] == "test.ping"
        return FakeResponse()

    monkeypatch.setattr("app.services.webhook_service.httpx.post", fake_post)
    webhook = await _create_webhook(client, org_a["access_token"])

    resp = await client.post(
        f"/api/v1/webhooks/{webhook['id']}/test",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "response_status": 200, "response_body": "OK", "error": None}
    assert calls["url"] == "https://example.com/hooks/sms"

    deliveries = await client.get(
        f"/api/v1/webhooks/{webhook['id']}/deliveries",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
    )
    assert deliveries.status_code == 200
    assert len(deliveries.json()) == 1
    assert deliveries.json()[0]["response_status"] == 200


@pytest.mark.asyncio
async def test_outbox_dispatch_to_subscribed_webhooks(client, org_a, monkeypatch):
    """Worker processing an outbox event delivers to subscribed endpoints only."""
    token = org_a["access_token"]
    await _create_webhook(client, token, name="Interested")
    await _create_webhook(
        client, token, name="Ignorer", events=["inventory.restocked"]
    )
    deliveries = []

    def fake_post(url, **kwargs):
        deliveries.append({"url": url, "headers": kwargs.get("headers", {})})
        return type("R", (), {"status_code": 200, "text": "ok"})()

    monkeypatch.setattr("app.services.webhook_service.httpx.post", fake_post)

    # Emit directly into the session (bypassing API) and process like the worker.
    from app.db.session import SessionLocal

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    org_id = me.json()["organization_id"]

    with SessionLocal() as db:
        emit(
            db,
            organization_id=org_id,
            event_type="stock.low",
            aggregate_type="product",
            aggregate_id="00000000-0000-0000-0000-000000000001",
            payload={"sku": "X1", "stock": 1},
        )
        db.commit()
        from app.worker import process_pending

        processed = process_pending(db, limit=10)
        assert processed == 1

    assert len(deliveries) == 1
    assert deliveries[0]["url"] == "https://example.com/hooks/sms"
    assert deliveries[0]["headers"]["X-Webhook-Event"] == "stock.low"

    from app.db.session import SessionLocal as SL2

    with SL2() as db:
        from sqlalchemy import select

        from app.models.webhook import WebhookDelivery

        rows = db.execute(select(WebhookDelivery)).scalars().all()
        assert len(rows) == 1
        assert rows[0].response_status == 200
