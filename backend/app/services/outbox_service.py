"""Transactional outbox: domain events written in the same transaction as the
business change, then delivered asynchronously by the background worker."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outbox import OutboxEvent

MAX_ATTEMPTS = 5


def emit(
    db: Session,
    *,
    organization_id: UUID,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> OutboxEvent:
    """Append an event to the outbox. Shares the caller's transaction:
    the event is only visible once the surrounding commit succeeds."""
    event = OutboxEvent(
        organization_id=organization_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload or {},
    )
    db.add(event)
    db.flush()
    return event


def claim_ready_events(db: Session, limit: int = 50) -> list[OutboxEvent]:
    """Claim unprocessed events with row locks (safe for concurrent workers)."""
    stmt = (
        select(OutboxEvent)
        .where(
            OutboxEvent.processed_at.is_(None),
            OutboxEvent.attempts < MAX_ATTEMPTS,
        )
        .order_by(OutboxEvent.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list(db.execute(stmt).scalars().all())


def mark_processed(db: Session, event: OutboxEvent) -> None:
    event.processed_at = datetime.now(UTC)
    event.last_error = None


def mark_failed(db: Session, event: OutboxEvent, error: str) -> None:
    event.attempts += 1
    event.last_error = error[:2000]
    if event.attempts >= MAX_ATTEMPTS:
        event.processed_at = datetime.now(UTC)
