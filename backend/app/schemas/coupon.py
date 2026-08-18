from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageParams


class CouponBase(BaseModel):
    code: str = Field(min_length=3, max_length=50, pattern="^[A-Za-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=300)
    discount_type: str = Field(pattern="^(percent|fixed)$")
    discount_value: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    min_subtotal: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=14, decimal_places=2
    )
    max_redemptions: int | None = Field(default=None, gt=0)
    max_per_customer: int | None = Field(default=None, gt=0)
    active: bool = True
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=50, pattern="^[A-Za-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=300)
    discount_type: str | None = Field(default=None, pattern="^(percent|fixed)$")
    discount_value: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    min_subtotal: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    max_redemptions: int | None = Field(default=None, gt=0)
    max_per_customer: int | None = Field(default=None, gt=0)
    active: bool | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class CouponRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    description: str | None = None
    discount_type: str
    discount_value: Decimal
    min_subtotal: Decimal
    max_redemptions: int | None = None
    max_per_customer: int | None = None
    active: bool
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    usage_count: int = 0
    created_at: datetime


class CouponValidateResult(BaseModel):
    valid: bool
    code: str
    discount_type: str
    discount_value: Decimal
    min_subtotal: Decimal = Decimal("0")
    message: str = ""


class CouponListParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    active: bool | None = None
