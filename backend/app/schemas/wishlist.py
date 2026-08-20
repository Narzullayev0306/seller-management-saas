from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WishlistItemInput(BaseModel):
    product_id: UUID
    product_variant_id: UUID | None = None


class WishlistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_variant_id: UUID | None = None
    name: str
    sku: str
    price: Decimal
    image_url: str | None = None
    variant_name: str | None = None
    variant_attributes: dict | None = None
    in_stock: bool
    created_at: datetime


class WishlistRead(BaseModel):
    wishlist_id: UUID
    items: list[WishlistItemRead]
    item_count: int


class WishlistItemCreate(BaseModel):
    product_id: UUID = Field(description="Product to add to the wishlist")
    product_variant_id: UUID | None = None
