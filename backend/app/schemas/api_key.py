from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.services.permissions import PERMISSIONS

ALL_SCOPES = sorted(PERMISSIONS.keys())


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(min_length=1, max_length=40)
    expires_at: datetime | None = None


class ApiKeyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    scopes: list[str] | None = Field(default=None, min_length=1, max_length=40)
    is_active: bool | None = None
    expires_at: datetime | None = None


class ApiKeyRead(BaseModel):
    id: UUID
    name: str
    prefix: str
    scopes: list[str]
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class ApiKeyWithSecret(ApiKeyRead):
    """Full key material — returned exactly once, on creation."""

    key: str
