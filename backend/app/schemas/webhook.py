from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

WEBHOOK_EVENTS = (
    "order.created",
    "order.cancelled",
    "order.status_changed",
    "product.created",
    "product.updated",
    "stock.low",
    "inventory.restocked",
)


class WebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    events: list[str] = Field(min_length=1, max_length=20)
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = Field(default=None, min_length=1, max_length=500)
    events: list[str] | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None


class WebhookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    secret: str
    events: list[str]
    is_active: bool
    last_delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    response_status: int | None = None
    response_body: str | None = None
    error: str | None = None
    delivered_at: datetime | None = None
    created_at: datetime


class WebhookTestResult(BaseModel):
    ok: bool
    response_status: int | None = None
    response_body: str | None = None
    error: str | None = None
