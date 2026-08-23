from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReturnRequestCreate(BaseModel):
    order_item_id: UUID
    quantity: int = Field(ge=1, le=10000)
    reason: str | None = Field(default=None, max_length=2000)
    condition: str = Field(
        default="unused", pattern="^(unused|defective|damaged|wrong_item)$"
    )


class ReturnRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    order_item_id: UUID
    product_id: UUID
    product_variant_id: UUID | None = None
    product_name: str = ""
    quantity: int
    reason: str | None = None
    condition: str
    status: str
    created_at: datetime
    decided_at: datetime | None = None


class ReturnDecision(BaseModel):
    action: str = Field(pattern="^(approve|reject|receive|complete)$")


class RefundCreate(BaseModel):
    order_id: UUID
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    reason: str | None = Field(default=None, max_length=2000)
    payment_id: UUID | None = None


class RefundAction(BaseModel):
    action: str = Field(pattern="^(process|fail)$")


class RefundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    order_number: str = ""
    return_request_id: UUID | None = None
    payment_id: UUID | None = None
    amount: Decimal
    reason: str | None = None
    status: str
    created_at: datetime
    processed_at: datetime | None = None
