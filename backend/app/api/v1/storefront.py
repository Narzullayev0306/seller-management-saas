from __future__ import annotations

import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_customer, optional_current_customer
from app.core.exceptions import bad_request
from app.core.ratelimit import check_rate_limit
from app.core.redis import cache_get, cache_invalidate, cache_set
from app.db.session import get_db
from app.models.customer_account import CustomerAccount
from app.models.order import Order
from app.models.organization import Organization
from app.schemas.cart import CartItemInput, CartItemUpdate, CartRead
from app.schemas.common import build_page
from app.schemas.customer_auth import (
    CustomerLoginRequest,
    CustomerLogoutRequest,
    CustomerMe,
    CustomerProfileUpdate,
    CustomerRefreshRequest,
    CustomerRegisterRequest,
    CustomerTokenPair,
)
from app.schemas.order import OrderRead
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
from app.services import cart_service, customer_auth_service
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


def _clear_cart_after_checkout(
    db: Session,
    org_id: UUID,
    account: CustomerAccount | None,
    request: Request,
) -> None:
    """Remove the shopper's cart once their order has been placed."""
    if account is not None:
        cart = cart_service.find_customer_cart(db, org_id, account.customer_id)
    else:
        cart = cart_service.find_session_cart(
            db, org_id, request.headers.get("X-Cart-Token")
        )
    if cart is not None:
        cart_service.clear(db, cart)


def _customer_order_read(order: Order) -> OrderRead:
    return OrderRead(
        id=order.id,
        order_number=order.order_number,
        seller_id=order.seller_id,
        seller_name=order.seller.full_name if order.seller else None,
        customer_id=order.customer_id,
        customer_name=order.customer.full_name if order.customer else "",
        created_by=order.created_by,
        created_by_name=order.creator.full_name if order.creator else None,
        status=order.status,
        payment_status=order.payment_status,
        subtotal=order.subtotal,
        discount=order.discount,
        tax=order.tax,
        shipping_fee=order.shipping_fee,
        total=order.total,
        items=[
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_variant_id": item.product_variant_id,
                "product_name": item.product.name if item.product else "",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in order.items
        ],
        created_at=order.created_at,
    )


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
        "optional Idempotency-Key header to prevent duplicate orders. When a "
        "customer Bearer token is provided, the order is linked to that account "
        "and the customer's cart is cleared.",
        responses={
            404: {"description": "Product or storefront not found"},
            409: {"description": "Insufficient stock"},
        },
    )
    def checkout(
        slug: str,
        payload: CheckoutCreate,
        request: Request,
        account: CustomerAccount | None = Depends(optional_current_customer),
        db: Session = Depends(get_db),
) -> JSONResponse | CheckoutResult:
        check_rate_limit(request, "checkout", limit=5, window=60)
        org_id = resolve_storefront(db, slug)

        def _run() -> CheckoutResult:
            result = StorefrontService(db, org_id).checkout(
                payload, customer_account=account
            )
            invalidate_catalog_cache(org_id)
            _clear_cart_after_checkout(db, org_id, account, request)
            return result

        return _idempotent_checkout(
            org_id, request.headers.get("Idempotency-Key"), _run
        )

    # ---- customer accounts ----------------------------------------------

    @router.post(
        "/auth/register",
        response_model=CustomerTokenPair,
        status_code=201,
        summary="Register a customer account for this store",
        responses={
            409: {"description": "Email already registered"},
            422: {"description": "Validation error"},
        },
    )
    def auth_register(
        slug: str,
        payload: CustomerRegisterRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> CustomerTokenPair:
        check_rate_limit(request, "customer_register", limit=5, window=60)
        org_id = resolve_storefront(db, slug)
        return customer_auth_service.register(db, org_id, payload)

    @router.post(
        "/auth/login",
        response_model=CustomerTokenPair,
        summary="Login with a customer account for this store",
        responses={401: {"description": "Invalid credentials"}},
    )
    def auth_login(
        slug: str,
        payload: CustomerLoginRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> CustomerTokenPair:
        check_rate_limit(request, "customer_login", limit=10, window=60)
        check_rate_limit(
            request,
            f"customer_login_email:{payload.email.lower()}",
            limit=10,
            window=300,
        )
        org_id = resolve_storefront(db, slug)
        return customer_auth_service.login(db, org_id, payload)

    @router.post(
        "/auth/refresh",
        response_model=CustomerTokenPair,
        summary="Rotate a customer refresh token",
        responses={401: {"description": "Invalid, expired or revoked token"}},
    )
    def auth_refresh(
        slug: str,
        payload: CustomerRefreshRequest,
        db: Session = Depends(get_db),
    ) -> CustomerTokenPair:
        resolve_storefront(db, slug)
        return customer_auth_service.refresh(db, payload.refresh_token)

    @router.post(
        "/auth/logout",
        status_code=204,
        summary="Logout a customer account",
        description="Revokes the presented refresh token. Idempotent.",
    )
    def auth_logout(
        slug: str,
        payload: CustomerLogoutRequest,
        db: Session = Depends(get_db),
    ) -> None:
        resolve_storefront(db, slug)
        customer_auth_service.logout(db, payload.refresh_token)

    @router.get(
        "/auth/me",
        response_model=CustomerMe,
        summary="Current customer account profile",
    )
    def auth_me(
        slug: str,
        account: CustomerAccount = Depends(get_current_customer),
        db: Session = Depends(get_db),
    ) -> dict:
        org_id = resolve_storefront(db, slug)
        if account.organization_id != org_id:
            raise bad_request(
                "WRONG_STORE", "This account belongs to another store"
            )
        return customer_auth_service.account_payload(db, account)

    @router.patch(
        "/auth/me",
        response_model=CustomerMe,
        summary="Update the current customer account profile",
    )
    def auth_update_me(
        slug: str,
        payload: CustomerProfileUpdate,
        account: CustomerAccount = Depends(get_current_customer),
        db: Session = Depends(get_db),
    ) -> dict:
        org_id = resolve_storefront(db, slug)
        if account.organization_id != org_id:
            raise bad_request(
                "WRONG_STORE", "This account belongs to another store"
            )
        return customer_auth_service.update_profile(db, account, payload)

    @router.get(
        "/auth/orders",
        response_model=list[OrderRead],
        summary="Orders placed by the current customer account",
    )
    def auth_orders(
        slug: str,
        account: CustomerAccount = Depends(get_current_customer),
        db: Session = Depends(get_db),
    ) -> list[OrderRead]:
        org_id = resolve_storefront(db, slug)
        if account.organization_id != org_id:
            raise bad_request(
                "WRONG_STORE", "This account belongs to another store"
            )
        orders = db.execute(
            select(Order)
            .where(
                Order.organization_id == org_id,
                Order.customer_id == account.customer_id,
            )
            .order_by(Order.created_at.desc())
            .limit(50)
        ).scalars().all()
        return [_customer_order_read(o) for o in orders]

    # ---- cart ------------------------------------------------------------

    @router.get(
        "/cart",
        response_model=CartRead,
        summary="Read the current cart",
        description="Identified by a customer Bearer token or an X-Cart-Token "
        "header (client-generated anonymous session token).",
    )
    def cart_get(
        slug: str,
        request: Request,
        account: CustomerAccount | None = Depends(optional_current_customer),
        db: Session = Depends(get_db),
    ) -> CartRead:
        org_id = resolve_storefront(db, slug)
        customer, session_token = cart_service.resolve_cart_owner(
            db, org_id, account, request.headers.get("X-Cart-Token")
        )
        cart = cart_service.get_or_create_cart(
            db, org_id, customer=customer, session_token=session_token
        )
        return cart_service.cart_read(db, org_id, cart)

    @router.post(
        "/cart/items",
        response_model=CartRead,
        status_code=201,
        summary="Add an item to the cart",
        responses={404: {"description": "Product not found"}},
    )
    def cart_add_item(
        slug: str,
        payload: CartItemInput,
        request: Request,
        account: CustomerAccount | None = Depends(optional_current_customer),
        db: Session = Depends(get_db),
    ) -> CartRead:
        check_rate_limit(request, "cart_add", limit=30, window=60)
        org_id = resolve_storefront(db, slug)
        customer, session_token = cart_service.resolve_cart_owner(
            db, org_id, account, request.headers.get("X-Cart-Token")
        )
        cart = cart_service.get_or_create_cart(
            db, org_id, customer=customer, session_token=session_token
        )
        return cart_service.add_item(db, org_id, cart, payload)

    @router.patch(
        "/cart/items/{item_id}",
        response_model=CartRead,
        summary="Update an item quantity",
        responses={404: {"description": "Cart item not found"}},
    )
    def cart_update_item(
        slug: str,
        item_id: UUID,
        payload: CartItemUpdate,
        request: Request,
        account: CustomerAccount | None = Depends(optional_current_customer),
        db: Session = Depends(get_db),
    ) -> CartRead:
        org_id = resolve_storefront(db, slug)
        customer, session_token = cart_service.resolve_cart_owner(
            db, org_id, account, request.headers.get("X-Cart-Token")
        )
        cart = cart_service.get_or_create_cart(
            db, org_id, customer=customer, session_token=session_token
        )
        return cart_service.update_item(db, org_id, cart, item_id, payload.quantity)

    @router.delete(
        "/cart/items/{item_id}",
        response_model=CartRead,
        summary="Remove an item from the cart",
        responses={404: {"description": "Cart item not found"}},
    )
    def cart_remove_item(
        slug: str,
        item_id: UUID,
        request: Request,
        account: CustomerAccount | None = Depends(optional_current_customer),
        db: Session = Depends(get_db),
    ) -> CartRead:
        org_id = resolve_storefront(db, slug)
        customer, session_token = cart_service.resolve_cart_owner(
            db, org_id, account, request.headers.get("X-Cart-Token")
        )
        cart = cart_service.get_or_create_cart(
            db, org_id, customer=customer, session_token=session_token
        )
        return cart_service.remove_item(db, cart, item_id)

    @router.delete(
        "/cart",
        response_model=CartRead,
        summary="Clear the cart",
    )
    def cart_clear(
        slug: str,
        request: Request,
        account: CustomerAccount | None = Depends(optional_current_customer),
        db: Session = Depends(get_db),
    ) -> CartRead:
        org_id = resolve_storefront(db, slug)
        customer, session_token = cart_service.resolve_cart_owner(
            db, org_id, account, request.headers.get("X-Cart-Token")
        )
        cart = cart_service.get_or_create_cart(
            db, org_id, customer=customer, session_token=session_token
        )
        return cart_service.clear(db, cart)

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
    account: CustomerAccount | None = Depends(optional_current_customer),
    db: Session = Depends(get_db),
) -> JSONResponse | CheckoutResult:
    check_rate_limit(request, "checkout", limit=5, window=60)
    org_id = resolve_storefront(db, None)

    def _run() -> CheckoutResult:
        result = StorefrontService(db, org_id).checkout(
            payload, customer_account=account
        )
        invalidate_catalog_cache(org_id)
        _clear_cart_after_checkout(db, org_id, account, request)
        return result

    return _idempotent_checkout(org_id, request.headers.get("Idempotency-Key"), _run)


# ---- legacy customer account + cart routes (default store) -------------


@legacy_router.post(
    "/auth/register",
    response_model=CustomerTokenPair,
    status_code=201,
    summary="Register a customer account (default store)",
)
def legacy_auth_register(
    payload: CustomerRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CustomerTokenPair:
    check_rate_limit(request, "customer_register", limit=5, window=60)
    org_id = resolve_storefront(db, None)
    return customer_auth_service.register(db, org_id, payload)


@legacy_router.post(
    "/auth/login",
    response_model=CustomerTokenPair,
    summary="Login with a customer account (default store)",
)
def legacy_auth_login(
    payload: CustomerLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CustomerTokenPair:
    check_rate_limit(request, "customer_login", limit=10, window=60)
    check_rate_limit(
        request,
        f"customer_login_email:{payload.email.lower()}",
        limit=10,
        window=300,
    )
    org_id = resolve_storefront(db, None)
    return customer_auth_service.login(db, org_id, payload)


@legacy_router.post(
    "/auth/refresh",
    response_model=CustomerTokenPair,
    summary="Rotate a customer refresh token (default store)",
)
def legacy_auth_refresh(
    payload: CustomerRefreshRequest,
    db: Session = Depends(get_db),
) -> CustomerTokenPair:
    resolve_storefront(db, None)
    return customer_auth_service.refresh(db, payload.refresh_token)


@legacy_router.post(
    "/auth/logout",
    status_code=204,
    summary="Logout a customer account (default store)",
)
def legacy_auth_logout(
    payload: CustomerLogoutRequest,
    db: Session = Depends(get_db),
) -> None:
    resolve_storefront(db, None)
    customer_auth_service.logout(db, payload.refresh_token)


@legacy_router.get(
    "/auth/me",
    response_model=CustomerMe,
    summary="Current customer account profile (default store)",
)
def legacy_auth_me(
    account: CustomerAccount = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    org_id = resolve_storefront(db, None)
    if account.organization_id != org_id:
        raise bad_request("WRONG_STORE", "This account belongs to another store")
    return customer_auth_service.account_payload(db, account)


@legacy_router.patch(
    "/auth/me",
    response_model=CustomerMe,
    summary="Update the current customer account profile (default store)",
)
def legacy_auth_update_me(
    payload: CustomerProfileUpdate,
    account: CustomerAccount = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> dict:
    org_id = resolve_storefront(db, None)
    if account.organization_id != org_id:
        raise bad_request("WRONG_STORE", "This account belongs to another store")
    return customer_auth_service.update_profile(db, account, payload)


@legacy_router.get(
    "/auth/orders",
    response_model=list[OrderRead],
    summary="Orders placed by the current customer account (default store)",
)
def legacy_auth_orders(
    account: CustomerAccount = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> list[OrderRead]:
    org_id = resolve_storefront(db, None)
    if account.organization_id != org_id:
        raise bad_request("WRONG_STORE", "This account belongs to another store")
    orders = db.execute(
        select(Order)
        .where(
            Order.organization_id == org_id,
            Order.customer_id == account.customer_id,
        )
        .order_by(Order.created_at.desc())
        .limit(50)
    ).scalars().all()
    return [_customer_order_read(o) for o in orders]


@legacy_router.get(
    "/cart",
    response_model=CartRead,
    summary="Read the current cart (default store)",
)
def legacy_cart_get(
    request: Request,
    account: CustomerAccount | None = Depends(optional_current_customer),
    db: Session = Depends(get_db),
) -> CartRead:
    org_id = resolve_storefront(db, None)
    customer, session_token = cart_service.resolve_cart_owner(
        db, org_id, account, request.headers.get("X-Cart-Token")
    )
    cart = cart_service.get_or_create_cart(
        db, org_id, customer=customer, session_token=session_token
    )
    return cart_service.cart_read(db, org_id, cart)


@legacy_router.post(
    "/cart/items",
    response_model=CartRead,
    status_code=201,
    summary="Add an item to the cart (default store)",
)
def legacy_cart_add_item(
    payload: CartItemInput,
    request: Request,
    account: CustomerAccount | None = Depends(optional_current_customer),
    db: Session = Depends(get_db),
) -> CartRead:
    check_rate_limit(request, "cart_add", limit=30, window=60)
    org_id = resolve_storefront(db, None)
    customer, session_token = cart_service.resolve_cart_owner(
        db, org_id, account, request.headers.get("X-Cart-Token")
    )
    cart = cart_service.get_or_create_cart(
        db, org_id, customer=customer, session_token=session_token
    )
    return cart_service.add_item(db, org_id, cart, payload)


@legacy_router.patch(
    "/cart/items/{item_id}",
    response_model=CartRead,
    summary="Update an item quantity (default store)",
)
def legacy_cart_update_item(
    item_id: UUID,
    payload: CartItemUpdate,
    request: Request,
    account: CustomerAccount | None = Depends(optional_current_customer),
    db: Session = Depends(get_db),
) -> CartRead:
    org_id = resolve_storefront(db, None)
    customer, session_token = cart_service.resolve_cart_owner(
        db, org_id, account, request.headers.get("X-Cart-Token")
    )
    cart = cart_service.get_or_create_cart(
        db, org_id, customer=customer, session_token=session_token
    )
    return cart_service.update_item(db, org_id, cart, item_id, payload.quantity)


@legacy_router.delete(
    "/cart/items/{item_id}",
    response_model=CartRead,
    summary="Remove an item from the cart (default store)",
)
def legacy_cart_remove_item(
    item_id: UUID,
    request: Request,
    account: CustomerAccount | None = Depends(optional_current_customer),
    db: Session = Depends(get_db),
) -> CartRead:
    org_id = resolve_storefront(db, None)
    customer, session_token = cart_service.resolve_cart_owner(
        db, org_id, account, request.headers.get("X-Cart-Token")
    )
    cart = cart_service.get_or_create_cart(
        db, org_id, customer=customer, session_token=session_token
    )
    return cart_service.remove_item(db, cart, item_id)


@legacy_router.delete(
    "/cart",
    response_model=CartRead,
    summary="Clear the cart (default store)",
)
def legacy_cart_clear(
    request: Request,
    account: CustomerAccount | None = Depends(optional_current_customer),
    db: Session = Depends(get_db),
) -> CartRead:
    org_id = resolve_storefront(db, None)
    customer, session_token = cart_service.resolve_cart_owner(
        db, org_id, account, request.headers.get("X-Cart-Token")
    )
    cart = cart_service.get_or_create_cart(
        db, org_id, customer=customer, session_token=session_token
    )
    return cart_service.clear(db, cart)


router = _make_slug_routes()
