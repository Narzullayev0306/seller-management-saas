"""Idempotency-key handling for critical POST endpoints.

A client sends an `Idempotency-Key` header; the first request claims the key
(in its own short-lived transaction) and later duplicate requests receive the
stored response instead of re-running the business operation.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.idempotency import IdempotencyKey

CLAIM_TIMEOUT_SECONDS = 5.0


def claim_idempotency_key(
    organization_id: UUID,
    key: str,
    *,
    user_id: UUID | None = None,
    request_hash: str | None = None,
) -> bool:
    """Claim a key for this request. Returns True when this request may proceed,
    False when the key was already claimed by another (duplicate) request."""
    with SessionLocal() as db:
        existing = db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.organization_id == organization_id,
                IdempotencyKey.key == key,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return False
        db.add(
            IdempotencyKey(
                organization_id=organization_id,
                key=key,
                user_id=user_id,
                request_hash=request_hash,
                expires_at=IdempotencyKey.default_expiry(),
            )
        )
        try:
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False


def get_stored_response(
    organization_id: UUID, key: str
) -> tuple[int, dict[str, Any]] | None:
    """Return (status, body) when the claimed key was completed, else None."""
    with SessionLocal() as db:
        row = db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.organization_id == organization_id,
                IdempotencyKey.key == key,
            )
        ).scalar_one_or_none()
        if row is None or row.status != "completed" or row.response_body is None:
            return None
        return row.response_status, row.response_body


def store_response(
    organization_id: UUID, key: str, status: int, body: dict[str, Any]
) -> None:
    with SessionLocal() as db:
        row = db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.organization_id == organization_id,
                IdempotencyKey.key == key,
            )
        ).scalar_one_or_none()
        if row is None:
            return
        row.status = "completed"
        row.response_status = status
        row.response_body = body
        db.commit()


def wait_for_response(organization_id: UUID, key: str) -> tuple[int, dict[str, Any]] | None:
    """Poll for a completed duplicate request (the winner of the claim)."""
    deadline = time.monotonic() + CLAIM_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        stored = get_stored_response(organization_id, key)
        if stored is not None:
            return stored
        time.sleep(0.1)
    return None
