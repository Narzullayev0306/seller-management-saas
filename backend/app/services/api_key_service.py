from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError, bad_request, not_found
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.schemas.api_key import ALL_SCOPES, ApiKeyCreate, ApiKeyUpdate

KEY_PREFIX = "smk_"


def hash_key(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _validate_scopes(scopes: list[str]) -> None:
    unknown = [s for s in scopes if s not in ALL_SCOPES]
    if unknown:
        raise bad_request(
            "API_KEY_INVALID_SCOPES",
            f"Unknown scope(s): {', '.join(sorted(unknown))}",
        )


def generate_secret() -> tuple[str, str]:
    secret = KEY_PREFIX + secrets.token_urlsafe(32)
    return secret, secret[: len(KEY_PREFIX) + 8]


def create_api_key(
    db: Session, organization_id: UUID, payload: ApiKeyCreate, created_by: UUID | None
) -> tuple[ApiKey, str]:
    _validate_scopes(payload.scopes)
    secret, prefix = generate_secret()
    key = ApiKey(
        organization_id=organization_id,
        name=payload.name,
        key_hash=hash_key(secret),
        prefix=prefix,
        scopes=payload.scopes,
        is_active=True,
        expires_at=payload.expires_at,
        created_by=created_by,
    )
    db.add(key)
    db.flush()
    return key, secret


def list_api_keys(db: Session, organization_id: UUID) -> list[ApiKey]:
    return list(
        db.execute(
            select(ApiKey)
            .where(ApiKey.organization_id == organization_id)
            .order_by(ApiKey.created_at.desc())
        ).scalars()
    )


def _get_key(
    db: Session, organization_id: UUID, key_id: UUID, actor_id: UUID | None = None
) -> ApiKey:
    key = db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.organization_id == organization_id,
        )
    ).scalar_one_or_none()
    if key is None:
        raise not_found("API_KEY_NOT_FOUND", "API key not found")
    if key.created_by is not None and actor_id is not None and key.created_by != actor_id:
        raise ApiError(
            status_code=403,
            code="API_KEY_NOT_FOUND",
            message="API key not found",
        )
    return key


def update_api_key(
    db: Session,
    organization_id: UUID,
    key_id: UUID,
    payload: ApiKeyUpdate,
    actor_id: UUID,
) -> ApiKey:
    key = _get_key(db, organization_id, key_id, actor_id)
    if payload.scopes is not None:
        _validate_scopes(payload.scopes)
        key.scopes = payload.scopes
    if payload.name is not None:
        key.name = payload.name
    if payload.is_active is not None:
        key.is_active = payload.is_active
    if "expires_at" in payload.model_fields_set:
        key.expires_at = payload.expires_at
    db.flush()
    return key


def delete_api_key(
    db: Session, organization_id: UUID, key_id: UUID, actor_id: UUID
) -> None:
    key = _get_key(db, organization_id, key_id, actor_id)
    db.delete(key)
    db.flush()


def verify_api_key(db: Session, secret: str) -> ApiKey | None:
    """Resolve a raw key to its row, checking activation state and expiry."""
    if not secret.startswith(KEY_PREFIX):
        return None
    key = db.execute(
        select(ApiKey).where(ApiKey.key_hash == hash_key(secret))
    ).scalar_one_or_none()
    if key is None or not key.is_active:
        return None
    org = db.get(Organization, key.organization_id)
    if org is None or not org.is_active:
        return None
    if key.expires_at is not None and key.expires_at < datetime.now(UTC):
        return None
    key.last_used_at = datetime.now(UTC)
    db.commit()
    return key
