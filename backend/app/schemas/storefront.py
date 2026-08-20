from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import PageParams


class CatalogProduct(BaseModel):
    id: UUID
    name: str
    category: str
    price: Decimal
    stock_quantity: int
    stock_status: str
    image_url: str | None = None
    brand_name: str | None = None
    rating: Decimal | None = None
    review_count: int = 0
    featured: bool = False


class CatalogResponse(BaseModel):
    items: list[CatalogProduct]
    page: int
    page_size: int
    total: int
    total_pages: int
    categories: list[str]
    brands: list[str]


class ProductImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    position: int


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    logo_url: str | None = None
    description: str | None = None


class PricePoint(BaseModel):
    old_price: Decimal
    new_price: Decimal
    changed_at: datetime


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_name: str
    rating: int
    comment: str | None = None
    created_at: datetime


class ProductVariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    sku: str
    attributes: dict[str, str] | None = None
    price: Decimal
    stock_quantity: int
    active: bool


class ProductDetail(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    category: str
    price: Decimal
    stock_quantity: int
    stock_status: str
    image_url: str | None = None
    featured: bool = False
    brand: BrandRead | None = None
    images: list[ProductImageRead] = []
    reviews: list[ReviewRead] = []
    price_history: list[PricePoint] = []
    variants: list[ProductVariantRead] = []
    rating: Decimal | None = None
    review_count: int = 0


class BrandWithCount(BaseModel):
    id: UUID
    name: str
    logo_url: str | None = None
    description: str | None = None
    product_count: int = 0


class CategoryWithCount(BaseModel):
    category: str
    product_count: int = 0


class ReviewCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class BackInStockCreate(BaseModel):
    email: EmailStr


class CheckoutItem(BaseModel):
    product_id: UUID
    product_variant_id: UUID | None = None
    quantity: int = Field(ge=1, le=100)


class CheckoutCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=150)
    last_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=300)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    tax: Decimal = Field(default=Decimal("0"), ge=0)
    shipping_method_id: UUID | None = None
    coupon_code: str | None = Field(default=None, max_length=50)
    items: list[CheckoutItem] = Field(min_length=1)


class CheckoutResult(BaseModel):
    order_id: UUID
    order_number: str
    status: str
    payment_status: str
    payment_id: UUID
    total: Decimal
    discount: Decimal = Decimal("0")
    coupon_code: str | None = None
    items_count: int


class StorefrontInfo(BaseModel):
    slug: str
    name: str
    currency: str = "USD"
    timezone: str = "UTC"
    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    description: str | None = None
    social_links: dict | None = None


class CatalogParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=120)
    featured: bool | None = None
    sort_by: str | None = Field(
        default=None, pattern="^(price_asc|price_desc|newest|popular)$"
    )
