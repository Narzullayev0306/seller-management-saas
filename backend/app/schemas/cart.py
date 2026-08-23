from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CartItemInput(BaseModel):
    product_id: UUID
    product_variant_id: UUID | None = None
    quantity: int = Field(ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartItemRead(BaseModel):
    id: UUID
    product_id: UUID
    product_variant_id: UUID | None = None
    name: str
    sku: str
    price: Decimal
    image_url: str | None = None
    variant_name: str | None = None
    variant_attributes: dict[str, str] | None = None
    quantity: int
    stock_quantity: int
    subtotal: Decimal
    created_at: datetime


class CartRead(BaseModel):
    cart_id: UUID
    items: list[CartItemRead] = []
    item_count: int = 0
    subtotal: Decimal = Decimal("0")
