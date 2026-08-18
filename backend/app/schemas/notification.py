from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationRead(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    data: dict[str, Any] | None = None
    read: bool
    created_at: datetime


class NotificationListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    unread_only: bool = False


class UnreadCount(BaseModel):
    count: int
