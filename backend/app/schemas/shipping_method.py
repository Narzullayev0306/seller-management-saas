from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShippingMethodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    min_order_amount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    max_order_amount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    estimated_delivery_days: int | None = Field(default=None, ge=0, le=365)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)


class ShippingMethodUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    min_order_amount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    max_order_amount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    estimated_delivery_days: int | None = Field(default=None, ge=0, le=365)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class ShippingMethodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    price: Decimal
    min_order_amount: Decimal | None = None
    max_order_amount: Decimal | None = None
    estimated_delivery_days: int | None = None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class StorefrontShippingMethod(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    price: Decimal
    min_order_amount: Decimal | None = None
    max_order_amount: Decimal | None = None
    estimated_delivery_days: int | None = None
