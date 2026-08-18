from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageParams


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=50)
    description: str | None = None
    category: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    cost_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    stock_quantity: int = Field(ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)
    status: str = Field(default="active", pattern="^(active|inactive)$")
    image_url: str | None = Field(default=None, max_length=500)
    brand_id: UUID | None = None
    featured: bool = False


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    cost_price: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    stock_quantity: int | None = Field(default=None, ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")
    image_url: str | None = Field(default=None, max_length=500)
    brand_id: UUID | None = None
    featured: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    sku: str
    description: str | None
    category: str
    price: Decimal
    cost_price: Decimal
    stock_quantity: int
    low_stock_threshold: int
    status: str
    stock_status: str
    image_url: str | None = None
    brand_id: UUID | None = None
    featured: bool = False
    created_at: datetime


class ProductListParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")
    stock_status: str | None = Field(
        default=None, pattern="^(in_stock|low_stock|out_of_stock)$"
    )
    sort_by: str | None = None
    sort_order: str | None = Field(default=None, pattern="^(asc|desc)$")
