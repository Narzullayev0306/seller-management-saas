"""Background worker: delivers transactional outbox events asynchronously.

Run as a separate process/container:
    python -m app.worker

Event handlers turn domain events into side effects (in-app notifications,
emails) that must NOT run inside the original business transaction.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (register every mapper before any session use)
from app.db.session import SessionLocal
from app.models.product import Product
from app.models.storefront import BackInStockRequest
from app.services import webhook_service
from app.services.email_service import render, send_email
from app.services.notification_service import (
    notify_low_stock,
    notify_new_order,
    notify_order_cancelled,
)
from app.services.outbox_service import claim_ready_events, mark_failed, mark_processed

logger = logging.getLogger("worker")

POLL_INTERVAL_SECONDS = 2.0


def _handle_back_in_stock_restock(
    db: Session, organization_id: UUID, product_id: UUID
) -> None:
    product = db.get(Product, product_id)
    if product is None or product.stock_quantity <= 0:
        return
    requests = db.execute(
        select(BackInStockRequest).where(
            BackInStockRequest.organization_id == organization_id,
            BackInStockRequest.product_id == product_id,
            BackInStockRequest.notified_at.is_(None),
        )
    ).scalars().all()
    for request in requests:
        send_email(
            request.email,
            f'"{product.name}" is back in stock',
            render(
                f"<h2 style='margin:0 0 12px;color:#0f172a;font-size:18px;'>Back in stock</h2>"
                f"<p style='color:#475569;font-size:14px;line-height:1.6;'>"
                f"Good news — <b>{product.name}</b> is available again. "
                f"Visit the store to place your order before it sells out.</p>"
            ),
        )
        request.notified_at = datetime.now(UTC)


def handle_event(db: Session, event) -> None:
    """Dispatch a single outbox event to its handler(s). Raises on failure."""
    payload = event.payload or {}
    event_type = event.event_type
    if event_type == "order.created":
        notify_new_order(
            db,
            organization_id=event.organization_id,
            order_number=payload.get("order_number", ""),
            order_id=event.aggregate_id,
            actor_user_id=payload.get("actor_user_id"),
        )
    elif event_type == "order.cancelled":
        notify_order_cancelled(
            db,
            organization_id=event.organization_id,
            order_number=payload.get("order_number", ""),
            order_id=event.aggregate_id,
            actor_user_id=payload.get("actor_user_id"),
        )
    elif event_type == "stock.low":
        notify_low_stock(db, event.organization_id, event.aggregate_id)
    elif event_type == "inventory.restocked":
        _handle_back_in_stock_restock(
            db, event.organization_id, event.aggregate_id
        )
    else:
        raise ValueError(f"Unknown event type: {event_type}")
    webhook_service.deliver_event(db, event)


def process_pending(db: Session, limit: int = 50) -> int:
    """Process up to `limit` ready events in the given session. Returns the
    number of events attempted. Safe to call from tests."""
    events = claim_ready_events(db, limit)
    for event in events:
        try:
            handle_event(db, event)
            mark_processed(db, event)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception(
                "Outbox event %s (%s) failed", event.id, event.event_type
            )
            mark_failed(db, event, str(exc))
            db.commit()
    return len(events)


async def run() -> None:
    logger.info("Worker started (poll interval %ss)", POLL_INTERVAL_SECONDS)
    while True:
        try:
            with SessionLocal() as db:
                processed = process_pending(db)
                if processed:
                    logger.info("Processed %s outbox events", processed)
        except Exception:
            logger.exception("Worker loop iteration failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
