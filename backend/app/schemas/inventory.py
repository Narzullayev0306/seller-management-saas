from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageParams


class StockItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    sku: str
    category: str
    stock_quantity: int
    low_stock_threshold: int
    status: str
    stock_status: str


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_name: str = ""
    type: str
    quantity: int
    reason: str | None
    reference_id: UUID | None = None
    previous_stock: int | None = None
    new_stock: int | None = None
    created_at: datetime


class AdjustmentCreate(BaseModel):
    product_id: UUID
    type: str = Field(pattern="^(purchase|adjustment|return)$")
    quantity: int = Field(ge=1, le=1000000)
    reason: str = Field(min_length=1, max_length=255)


class InventoryListParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    stock_status: str | None = Field(
        default=None, pattern="^(in_stock|low_stock|out_of_stock)$"
    )
    category: str | None = Field(default=None, max_length=100)
    sort_by: str | None = None
    sort_order: str | None = Field(default=None, pattern="^(asc|desc)$")


class MovementListParams(PageParams):
    product_id: UUID | None = None
    type: str | None = Field(
        default=None, pattern="^(purchase|sale|adjustment|return)$"
    )
    sort_by: str | None = None
    sort_order: str | None = Field(default=None, pattern="^(asc|desc)$")
