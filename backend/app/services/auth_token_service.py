"""Single-use auth token lifecycle (email verification, password reset, invites)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import bad_request
from app.core.security import generate_refresh_token, hash_refresh_token
from app.models.auth_token import AuthToken
from app.models.user import User

TOKEN_TTL = {
    "verify_email": timedelta(hours=24),
    "reset_password": timedelta(hours=1),
    "invite": timedelta(hours=72),
}


def create_auth_token(db: Session, user_id: UUID, purpose: str) -> str:
    """Store a hashed token and return the raw one to send to the user."""
    ttl = TOKEN_TTL.get(purpose, timedelta(hours=24))
    raw = generate_refresh_token()
    db.add(
        AuthToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) + ttl,
        )
    )
    db.flush()
    return raw


def consume_auth_token(db: Session, raw: str, purpose: str) -> User:
    """Validate and mark a token used; returns the owning user."""
    token = db.execute(
        select(AuthToken)
        .options(selectinload(AuthToken.user))
        .where(
            AuthToken.token_hash == hash_refresh_token(raw),
            AuthToken.purpose == purpose,
        )
    ).scalar_one_or_none()
    if token is None:
        raise bad_request("INVALID_TOKEN", "This link is invalid")
    if token.used_at is not None:
        raise bad_request("TOKEN_USED", "This link has already been used")
    if token.expires_at < datetime.now(UTC):
        raise bad_request("TOKEN_EXPIRED", "This link has expired")
    if not token.user.is_active:
        raise bad_request("ACCOUNT_DISABLED", "This account has been disabled")
    token.used_at = datetime.now(UTC)
    db.flush()
    return token.user


def get_invite_payload(db: Session, raw: str) -> dict:
    """Read the invite's target user + org without consuming it."""
    token = db.execute(
        select(AuthToken)
        .options(selectinload(AuthToken.user))
        .where(
            AuthToken.token_hash == hash_refresh_token(raw),
            AuthToken.purpose == "invite",
        )
    ).scalar_one_or_none()
    if token is None:
        raise bad_request("INVALID_TOKEN", "This invitation link is invalid")
    if token.used_at is not None:
        raise bad_request("TOKEN_USED", "This invitation has already been accepted")
    if token.expires_at < datetime.now(UTC):
        raise bad_request("TOKEN_EXPIRED", "This invitation has expired")
    return {
        "user": token.user,
        "organization_name": token.user.organization.name,
    }


def invalidate_user_tokens(db: Session, user_id: UUID, purpose: str) -> None:
    """Revoke all outstanding tokens of a purpose for a user (e.g. on reset)."""
    tokens = db.execute(
        select(AuthToken).where(
            AuthToken.user_id == user_id,
            AuthToken.purpose == purpose,
            AuthToken.used_at.is_(None),
        )
    ).scalars()
    now = datetime.now(UTC)
    for token in tokens:
        token.used_at = now
