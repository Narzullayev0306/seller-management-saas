"""Webhook endpoints: subscribe, dispatch signed deliveries, delivery log."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.models.outbox import OutboxEvent
from app.models.webhook import WebhookDelivery, WebhookEndpoint
from app.schemas.webhook import WEBHOOK_EVENTS, WebhookCreate, WebhookUpdate

logger = logging.getLogger("webhooks")

DELIVERY_TIMEOUT_SECONDS = 10.0


def _validate_events(events: list[str]) -> None:
    unknown = [e for e in events if e not in WEBHOOK_EVENTS]
    if unknown:
        raise bad_request(
            "WEBHOOK_INVALID_EVENTS",
            f"Unknown event types: {', '.join(unknown)}. "
            f"Supported: {', '.join(WEBHOOK_EVENTS)}",
        )


def create_webhook(
    db: Session, org_id: UUID, payload: WebhookCreate
) -> WebhookEndpoint:
    _validate_events(payload.events)
    endpoint = WebhookEndpoint(
        organization_id=org_id,
        name=payload.name,
        url=payload.url,
        secret=secrets.token_urlsafe(32),
        events=payload.events,
        is_active=payload.is_active,
    )
    db.add(endpoint)
    db.commit()
    return endpoint


def _get_webhook(db: Session, org_id: UUID, webhook_id: UUID) -> WebhookEndpoint:
    endpoint = db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.organization_id == org_id,
            WebhookEndpoint.id == webhook_id,
        )
    ).scalar_one_or_none()
    if endpoint is None:
        raise not_found("WebhookEndpoint")
    return endpoint


def update_webhook(
    db: Session, org_id: UUID, webhook_id: UUID, payload: WebhookUpdate
) -> WebhookEndpoint:
    endpoint = _get_webhook(db, org_id, webhook_id)
    data = payload.model_dump(exclude_none=True)
    if "events" in data:
        _validate_events(data["events"])
    for field, value in data.items():
        setattr(endpoint, field, value)
    db.commit()
    return endpoint


def delete_webhook(db: Session, org_id: UUID, webhook_id: UUID) -> None:
    endpoint = _get_webhook(db, org_id, webhook_id)
    db.delete(endpoint)
    db.commit()


def list_webhooks(db: Session, org_id: UUID) -> list[WebhookEndpoint]:
    return list(
        db.execute(
            select(WebhookEndpoint)
            .where(WebhookEndpoint.organization_id == org_id)
            .order_by(WebhookEndpoint.created_at)
        ).scalars()
    )


def list_deliveries(
    db: Session, org_id: UUID, webhook_id: UUID, limit: int = 50
) -> list[WebhookDelivery]:
    _get_webhook(db, org_id, webhook_id)
    return list(
        db.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.webhook_endpoint_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def _sign(secret: str, body: bytes, timestamp: int) -> str:
    message = f"{timestamp}.{body.decode('utf-8')}".encode()
    return "sha256=" + hmac.new(
        secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()


def _deliver(db: Session, endpoint: WebhookEndpoint, event_type: str, payload: dict) -> None:
    delivery = WebhookDelivery(
        webhook_endpoint_id=endpoint.id, event_type=event_type, payload=payload
    )
    db.add(delivery)
    db.flush()
    try:
        body = json.dumps({"event": event_type, "data": payload}).encode("utf-8")
        timestamp = int(datetime.now(UTC).timestamp())
        response = httpx.post(
            endpoint.url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": _sign(endpoint.secret, body, timestamp),
                "X-Webhook-Timestamp": str(timestamp),
                "X-Webhook-Event": event_type,
                "User-Agent": "seller-management-webhook/1.0",
            },
            timeout=DELIVERY_TIMEOUT_SECONDS,
        )
        delivery.response_status = response.status_code
        delivery.response_body = response.text[:4000]
        delivery.delivered_at = datetime.now(UTC)
        endpoint.last_delivered_at = delivery.delivered_at
    except httpx.HTTPError as exc:
        delivery.error = str(exc)[:2000]
        logger.warning(
            "Webhook %s delivery for %s failed: %s", endpoint.id, event_type, exc
        )
    db.commit()


def deliver_event(db: Session, event: OutboxEvent) -> None:
    """Dispatch an outbox event to every subscribed, active endpoint."""
    endpoints = db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.organization_id == event.organization_id,
            WebhookEndpoint.is_active.is_(True),
        )
    ).scalars().all()
    for endpoint in endpoints:
        if event.event_type in endpoint.events:
            _deliver(db, endpoint, event.event_type, event.payload or {})


def test_webhook(
    db: Session, org_id: UUID, webhook_id: UUID
) -> WebhookDelivery:
    endpoint = _get_webhook(db, org_id, webhook_id)
    _deliver(
        db,
        endpoint,
        "test.ping",
        {"message": f"Test ping from {endpoint.name}", "timestamp": datetime.now(UTC).isoformat()},
    )
    delivery = db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_endpoint_id == endpoint.id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(1)
    ).scalar_one()
    return delivery
