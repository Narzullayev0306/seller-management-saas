from __future__ import annotations

import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.core.ratelimit import check_rate_limit
from app.core.redis import cache_get, cache_invalidate, cache_set
from app.db.session import get_db
from app.models.organization import Organization
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
    StorefrontInfo,
)
from app.services.idempotency_service import (
    claim_idempotency_key,
    store_response,
    wait_for_response,
)
from app.services.storefront_service import StorefrontService, resolve_storefront

CATALOG_CACHE_TTL = 60


def invalidate_catalog_cache(org_id: UUID | None = None) -> None:
    if org_id is not None:
        cache_invalidate(f"sf:catalog:{org_id}:*")
    cache_invalidate("sf:catalog:*")


def _catalog_key(org_id: UUID, params: CatalogParams) -> str:
    key_parts = (
        params.page,
        params.page_size,
        params.search or "",
        params.category or "",
        params.brand or "",
        "1" if params.featured is None else ("1" if params.featured else "0"),
        params.sort_by or "",
    )
    digest = hashlib.sha256("|".join(map(str, key_parts)).encode()).hexdigest()
    return f"sf:catalog:{org_id}:{digest}"


def _build_catalog(org_id: UUID, db: Session, params: CatalogParams) -> CatalogResponse:
    service = StorefrontService(db, org_id)
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
    return CatalogResponse(
        items=page.items,
        page=page.page,
        page_size=page.page_size,
        total=page.total,
        total_pages=page.total_pages,
        categories=categories,
        brands=brands,
    )


def _idempotent_checkout(
    org_id: UUID, idem_key: str | None, run_checkout, status_code: int = 201
):
    """Run checkout guarded by an Idempotency-Key when provided."""
    if idem_key:
        if not claim_idempotency_key(org_id, idem_key):
            stored = wait_for_response(org_id, idem_key)
            if stored is not None:
                status, body = stored
                return JSONResponse(content=body, status_code=status)
            raise bad_request(
                "IDEMPOTENCY_IN_PROGRESS",
                "This request is still being processed, please retry shortly",
            )
        result = run_checkout()
        body = result.model_dump(mode="json")
        store_response(org_id, idem_key, status_code, body)
        return JSONResponse(content=body, status_code=status_code)
    return run_checkout()


def _make_slug_routes() -> APIRouter:
    router = APIRouter(prefix="/stores/{slug}", tags=["storefront"])

    @router.get(
        "/info",
        response_model=StorefrontInfo,
        summary="Public storefront metadata for a store",
        description="Resolves the store by slug and returns its public metadata "
        "(slug, name, currency, timezone, logo).",
    )
    def info(slug: str, db: Session = Depends(get_db)) -> StorefrontInfo:
        return _storefront_info(db, resolve_storefront(db, slug))

    @router.get(
        "/catalog",
        response_model=CatalogResponse,
        summary="Public product catalog for a store",
        description="Paginated catalog with category/brand/search/featured filters "
        "and sorting. Tenant-aware: the organization is resolved by store slug. "
        "Cached in Redis for 60s with a tenant-scoped key.",
    )
    def catalog(
        slug: str,
        params: CatalogParams = Depends(),
        db: Session = Depends(get_db),
    ) -> CatalogResponse:
        org_id = resolve_storefront(db, slug)
        cache_key = _catalog_key(org_id, params)
        cached = cache_get(cache_key)
        if cached is not None:
            return CatalogResponse.model_validate(cached)
        response = _build_catalog(org_id, db, params)
        cache_set(cache_key, response.model_dump(mode="json"), CATALOG_CACHE_TTL)
        return response

    @router.get(
        "/products/{product_id}",
        response_model=ProductDetail,
        summary="Public product detail for a store",
        description="Product with brand, gallery images, reviews and 90-day price history.",
    )
    def product_detail(
        slug: str, product_id: UUID, db: Session = Depends(get_db)
    ) -> ProductDetail:
        return StorefrontService(db, resolve_storefront(db, slug)).product_detail(product_id)

    @router.get(
        "/brands",
        response_model=list[BrandWithCount],
        summary="Public brands with product counts",
    )
    def brands(slug: str, db: Session = Depends(get_db)) -> list[BrandWithCount]:
        return StorefrontService(db, resolve_storefront(db, slug)).brands()

    @router.get(
        "/categories",
        response_model=list[CategoryWithCount],
        summary="Public categories with product counts",
    )
    def categories(slug: str, db: Session = Depends(get_db)) -> list[CategoryWithCount]:
        return StorefrontService(db, resolve_storefront(db, slug)).categories()

    @router.post(
        "/products/{product_id}/reviews",
        response_model=ReviewRead,
        status_code=201,
        summary="Submit a product review",
    )
    def create_review(
        slug: str,
        product_id: UUID,
        payload: ReviewCreate,
        request: Request,
        db: Session = Depends(get_db),
    ) -> ReviewRead:
        check_rate_limit(request, "review", limit=10, window=60)
        org_id = resolve_storefront(db, slug)
        result = StorefrontService(db, org_id).add_review(product_id, payload)
        invalidate_catalog_cache(org_id)
        return result

    @router.post(
        "/products/{product_id}/back-in-stock",
        status_code=204,
        summary="Request back-in-stock notification",
    )
    def back_in_stock(
        slug: str,
        product_id: UUID,
        payload: BackInStockCreate,
        request: Request,
        db: Session = Depends(get_db),
    ) -> None:
        check_rate_limit(request, "back_in_stock", limit=5, window=60)
        org_id = resolve_storefront(db, slug)
        StorefrontService(db, org_id).request_back_in_stock(product_id, payload)

    @router.post(
        "/checkout",
        response_model=CheckoutResult,
        status_code=201,
        summary="Guest checkout",
        description="Creates (or finds) the customer and places an order: stock is "
        "reserved and movements recorded exactly like the admin flow. Supports an "
        "optional Idempotency-Key header to prevent duplicate orders.",
        responses={
            404: {"description": "Product or storefront not found"},
            409: {"description": "Insufficient stock"},
        },
    )
    def checkout(
        slug: str,
        payload: CheckoutCreate,
        request: Request,
        db: Session = Depends(get_db),
) -> JSONResponse | CheckoutResult:
        check_rate_limit(request, "checkout", limit=5, window=60)
        org_id = resolve_storefront(db, slug)

        def _run() -> CheckoutResult:
            result = StorefrontService(db, org_id).checkout(payload)
            invalidate_catalog_cache(org_id)
            return result

        return _idempotent_checkout(
            org_id, request.headers.get("Idempotency-Key"), _run
        )

    return router


router = _make_slug_routes()


legacy_router = APIRouter(prefix="/storefront", tags=["storefront"], deprecated=True)


def _storefront_info(db: Session, org_id: UUID) -> StorefrontInfo:
    org = db.get(Organization, org_id)
    return StorefrontInfo(
        slug=org.slug,
        name=org.name,
        currency=org.currency or "USD",
        timezone=org.timezone or "UTC",
        logo_url=org.logo_url,
    )


@legacy_router.get(
    "/info",
    response_model=StorefrontInfo,
    summary="Public storefront metadata (default store)",
    description="Legacy route serving the first enabled storefront. "
    "Prefer /stores/{slug}/info.",
)
def legacy_info(db: Session = Depends(get_db)) -> StorefrontInfo:
    return _storefront_info(db, resolve_storefront(db, None))


@legacy_router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="Public product catalog (default store)",
    description="Legacy route serving the first enabled storefront. "
    "Prefer /stores/{slug}/catalog.",
)
def legacy_catalog(
    params: CatalogParams = Depends(),
    db: Session = Depends(get_db),
) -> CatalogResponse:
    org_id = resolve_storefront(db, None)
    cache_key = _catalog_key(org_id, params)
    cached = cache_get(cache_key)
    if cached is not None:
        return CatalogResponse.model_validate(cached)
    response = _build_catalog(org_id, db, params)
    cache_set(cache_key, response.model_dump(mode="json"), CATALOG_CACHE_TTL)
    return response


@legacy_router.get(
    "/products/{product_id}",
    response_model=ProductDetail,
    summary="Public product detail (default store)",
)
def legacy_product_detail(
    product_id: UUID, db: Session = Depends(get_db)
) -> ProductDetail:
    return StorefrontService(db, resolve_storefront(db, None)).product_detail(product_id)


@legacy_router.get(
    "/brands", response_model=list[BrandWithCount], summary="Public brands (default store)"
)
def legacy_brands(db: Session = Depends(get_db)) -> list[BrandWithCount]:
    return StorefrontService(db, resolve_storefront(db, None)).brands()


@legacy_router.get(
    "/categories",
    response_model=list[CategoryWithCount],
    summary="Public categories (default store)",
)
def legacy_categories(db: Session = Depends(get_db)) -> list[CategoryWithCount]:
    return StorefrontService(db, resolve_storefront(db, None)).categories()


@legacy_router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewRead,
    status_code=201,
    summary="Submit a product review (default store)",
)
def legacy_create_review(
    product_id: UUID,
    payload: ReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ReviewRead:
    check_rate_limit(request, "review", limit=10, window=60)
    org_id = resolve_storefront(db, None)
    result = StorefrontService(db, org_id).add_review(product_id, payload)
    invalidate_catalog_cache(org_id)
    return result


@legacy_router.post(
    "/products/{product_id}/back-in-stock",
    status_code=204,
    summary="Request back-in-stock notification (default store)",
)
def legacy_back_in_stock(
    product_id: UUID,
    payload: BackInStockCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    check_rate_limit(request, "back_in_stock", limit=5, window=60)
    org_id = resolve_storefront(db, None)
    StorefrontService(db, org_id).request_back_in_stock(product_id, payload)


@legacy_router.post(
    "/checkout",
    response_model=CheckoutResult,
    status_code=201,
    summary="Guest checkout (default store)",
)
def legacy_checkout(
    payload: CheckoutCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse | CheckoutResult:
    check_rate_limit(request, "checkout", limit=5, window=60)
    org_id = resolve_storefront(db, None)

    def _run() -> CheckoutResult:
        result = StorefrontService(db, org_id).checkout(payload)
        invalidate_catalog_cache(org_id)
        return result

    return _idempotent_checkout(org_id, request.headers.get("Idempotency-Key"), _run)


router = _make_slug_routes()
