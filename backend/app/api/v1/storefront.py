from __future__ import annotations

import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.ratelimit import check_rate_limit
from app.core.redis import cache_get, cache_invalidate, cache_set
from app.db.session import get_db
from app.schemas.common import build_page
from app.schemas.storefront import (
    BackInStockCreate,
    BrandWithCount,
    CatalogParams,
    CatalogResponse,
    CategoryWithCount,
    CheckoutCreate,
    CheckoutResult,
    ProductDetail,
    ReviewCreate,
    ReviewRead,
)
from app.services.storefront_service import StorefrontService

router = APIRouter(prefix="/storefront", tags=["storefront"])

CATALOG_CACHE_TTL = 60


def invalidate_catalog_cache() -> None:
    cache_invalidate("sf:catalog:*")


@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="Public product catalog",
    description="Paginated catalog with category/brand/search/featured filters "
    "and sorting. Includes rating aggregates and brand names. Cached in Redis for 60s.",
)
def catalog(
    params: CatalogParams = Depends(),
    db: Session = Depends(get_db),
) -> CatalogResponse:
    key_parts = (
        params.page,
        params.page_size,
        params.search or "",
        params.category or "",
        params.brand or "",
        "1" if params.featured is None else ("1" if params.featured else "0"),
        params.sort_by or "",
    )
    cache_key = "sf:catalog:" + hashlib.sha256("|".join(map(str, key_parts)).encode()).hexdigest()

    cached = cache_get(cache_key)
    if cached is not None:
        return CatalogResponse.model_validate(cached)

    service = StorefrontService(db)
    items, total, categories, brands = service.catalog(
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        category=params.category,
        brand=params.brand,
        featured=params.featured,
        sort_by=params.sort_by,
    )
    page = build_page(items, params.page, params.page_size, total)
    response = CatalogResponse(
        items=page.items,
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
        categories=categories,
        brands=brands,
    )
    cache_set(cache_key, response.model_dump(mode="json"), CATALOG_CACHE_TTL)
    return response


@router.get(
    "/products/{product_id}",
    response_model=ProductDetail,
    summary="Public product detail",
    description="Product with brand, gallery images, reviews and 90-day price history.",
)
def product_detail(product_id: UUID, db: Session = Depends(get_db)) -> ProductDetail:
    return StorefrontService(db).product_detail(product_id)


@router.get(
    "/brands",
    response_model=list[BrandWithCount],
    summary="Public brands with product counts",
)
def brands(db: Session = Depends(get_db)) -> list[BrandWithCount]:
    return StorefrontService(db).brands()


@router.get(
    "/categories",
    response_model=list[CategoryWithCount],
    summary="Public categories with product counts",
)
def categories(db: Session = Depends(get_db)) -> list[CategoryWithCount]:
    return StorefrontService(db).categories()


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewRead,
    status_code=201,
    summary="Submit a product review",
)
def create_review(
    product_id: UUID,
    payload: ReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ReviewRead:
    check_rate_limit(request, "review", limit=10, window=60)
    result = StorefrontService(db).add_review(product_id, payload)
    invalidate_catalog_cache()
    return result


@router.post(
    "/products/{product_id}/back-in-stock",
    status_code=204,
    summary="Request back-in-stock notification",
)
def back_in_stock(
    product_id: UUID,
    payload: BackInStockCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    check_rate_limit(request, "back_in_stock", limit=5, window=60)
    StorefrontService(db).request_back_in_stock(product_id, payload)


@router.post(
    "/checkout",
    response_model=CheckoutResult,
    status_code=201,
    summary="Guest checkout",
    description="Creates (or finds) the customer and places an order: stock is "
    "reserved and movements recorded exactly like the admin flow.",
    responses={
        404: {"description": "Product not found"},
        409: {"description": "Insufficient stock"},
    },
)
def checkout(
    payload: CheckoutCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> CheckoutResult:
    check_rate_limit(request, "checkout", limit=5, window=60)
    result = StorefrontService(db).checkout(payload)
    invalidate_catalog_cache()
    return result
