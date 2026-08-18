from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import PageParams

SELLER_STATUSES = ("active", "inactive", "suspended")


class SellerBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    status: str = Field(default="active", pattern="^(active|inactive|suspended)$")
    commission_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    user_id: UUID | None = None


class SellerCreate(SellerBase):
    pass


class SellerUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, pattern="^(active|inactive|suspended)$")
    commission_rate: Decimal | None = Field(default=None, ge=0, le=100)
    user_id: UUID | None = None


class SellerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    status: str
    commission_rate: Decimal
    total_sales: Decimal
    total_orders: int
    created_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class SellerStats(BaseModel):
    total_sales: Decimal
    total_orders: int
    total_commission: Decimal
    avg_order_value: Decimal
    recent_orders: list[dict]
    performance: list[dict]


class SellerListParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, pattern="^(active|inactive|suspended)$")
    sort_by: str | None = None
    sort_order: str | None = Field(default=None, pattern="^(asc|desc)$")
