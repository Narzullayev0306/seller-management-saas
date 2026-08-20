from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderItemInput(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1, le=100000)
    unit_cost: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID | None = None
    expected_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    items: list[PurchaseOrderItemInput] = Field(min_length=1, max_length=100)


class PurchaseOrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ordered|received|cancelled)$")


class PurchaseOrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_name: str = ""
    sku: str = ""
    quantity: int
    unit_cost: Decimal
    subtotal: Decimal


class PurchaseOrderRead(BaseModel):
    id: UUID
    supplier_id: UUID | None = None
    supplier_name: str | None = None
    po_number: str
    status: str
    expected_date: date | None = None
    notes: str | None = None
    total: Decimal
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    received_at: datetime | None = None
    items: list[PurchaseOrderItemRead]
