from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageParams

ORDER_STATUSES = (
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
)

PAYMENT_STATUSES = (
    "pending",
    "paid",
    "partially_paid",
    "refunded",
    "failed",
)


class OrderItemInput(BaseModel):
    product_id: UUID
    product_variant_id: UUID | None = None
    quantity: int = Field(ge=1, le=10000)


class OrderCreate(BaseModel):
    seller_id: UUID | None = None
    customer_id: UUID
    discount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    tax: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    shipping_fee: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=14, decimal_places=2
    )
    payment_status: str = Field(
        default="pending", pattern="^(pending|paid|partially_paid|refunded|failed)$"
    )
    coupon_code: str | None = Field(default=None, max_length=50)
    items: list[OrderItemInput] = Field(min_length=1, max_length=100)


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|confirmed|processing|shipped|delivered|cancelled)$")


class OrderPaymentUpdate(BaseModel):
    payment_status: str = Field(pattern="^(pending|paid|partially_paid|refunded|failed)$")


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    provider_payment_id: str | None = None
    amount: Decimal
    currency: str
    status: str
    failure_message: str | None = None
    paid_at: datetime | None = None
    created_at: datetime


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_variant_id: UUID | None = None
    product_name: str = ""
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    seller_id: UUID | None
    seller_name: str | None = None
    customer_id: UUID
    customer_name: str = ""
    created_by: UUID | None = None
    created_by_name: str | None = None
    status: str
    payment_status: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping_fee: Decimal
    total: Decimal
    items: list[OrderItemRead] = []
    created_at: datetime


class OrderHistoryEntry(BaseModel):
    id: UUID
    user_id: UUID | None = None
    user_name: str | None = None
    action: str
    meta: dict | None = None
    created_at: datetime


class OrderListParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    status: str | None = Field(
        default=None,
        pattern="^(pending|confirmed|processing|shipped|delivered|cancelled)$",
    )
    payment_status: str | None = Field(
        default=None, pattern="^(pending|paid|partially_paid|refunded)$"
    )
    seller_id: UUID | None = None
    customer_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    sort_by: str | None = None
    sort_order: str | None = Field(default=None, pattern="^(asc|desc)$")
