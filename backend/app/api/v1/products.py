from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import bad_request
from app.core.redis import cache_invalidate
from app.db.session import get_db
from app.models.category import Category
from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.storefront import Brand, PriceHistory
from app.models.user import User
from app.repositories.product_repo import ProductRepository
from app.schemas.common import Page
from app.schemas.product import (
    ProductCreate,
    ProductListParams,
    ProductRead,
    ProductUpdate,
    ProductVariantInput,
    ProductVariantRead,
)
from app.services.audit_service import log_action
from app.services.outbox_service import emit

router = APIRouter(prefix="/products", tags=["products"])


def _ensure_brand(db: Session, organization_id: UUID, brand_id: UUID | None) -> None:
    if brand_id is None:
        return
    exists = db.execute(
        select(Brand.id).where(
            Brand.organization_id == organization_id, Brand.id == brand_id
        )
    ).scalar_one_or_none()
    if exists is None:
        raise bad_request("BRAND_NOT_FOUND", "Brand does not exist in this organization")


def _ensure_category(
    db: Session, organization_id: UUID, category_id: UUID | None
) -> str | None:
    """Validate the category belongs to the org; returns its name."""
    if category_id is None:
        return None
    category = db.execute(
        select(Category).where(
            Category.organization_id == organization_id, Category.id == category_id
        )
    ).scalar_one_or_none()
    if category is None:
        raise bad_request(
            "CATEGORY_NOT_FOUND", "Category does not exist in this organization"
        )
    return category.name


def _category_name(payload: ProductCreate | ProductUpdate, org_name: str | None) -> str | None:
    if org_name is not None:
        return org_name
    return getattr(payload, "category", None)


def _to_read(product: Product) -> ProductRead:
    return ProductRead(
        id=product.id,
        name=product.name,
        sku=product.sku,
        description=product.description,
        category=product.category,
        price=product.price,
        cost_price=product.cost_price,
        stock_quantity=product.stock_quantity,
        low_stock_threshold=product.low_stock_threshold,
        status=product.status,
        stock_status=product.stock_status,
        image_url=product.image_url,
        brand_id=product.brand_id,
        category_id=product.category_id,
        featured=product.featured,
        variants=[
            ProductVariantRead(
                id=v.id,
                sku=v.sku,
                name=v.name,
                attributes=v.attributes,
                price=v.price,
                cost_price=v.cost_price,
                stock_quantity=v.stock_quantity,
                active=v.active,
                created_at=v.created_at,
            )
            for v in product.variants
        ],
        created_at=product.created_at,
    )


def _ensure_variant_skus(
    db: Session, organization_id: UUID, variants: list[ProductVariantInput], exclude_product_id: UUID | None = None
) -> None:
    if not variants:
        return
    seen: set[str] = set()
    for v in variants:
        if v.sku in seen:
            raise bad_request("VARIANT_SKU_DUPLICATE", f"Duplicate variant SKU: {v.sku}")
        seen.add(v.sku)
    stmt = select(ProductVariant.id).where(
        ProductVariant.organization_id == organization_id,
        ProductVariant.sku.in_(seen),
    )
    if exclude_product_id is not None:
        stmt = stmt.where(ProductVariant.product_id != exclude_product_id)
    existing = db.execute(stmt).scalars().all()
    if existing:
        raise bad_request("VARIANT_SKU_TAKEN", "A variant with this SKU already exists")


def _sync_variants(
    db: Session,
    organization_id: UUID,
    product: Product,
    variants: list[ProductVariantInput],
) -> None:
    incoming = {v.sku: v for v in variants}
    existing = {v.sku: v for v in product.variants}
    for sku, v in incoming.items():
        if sku in existing:
            old = existing[sku]
            old.name = v.name
            old.attributes = v.attributes
            old.price = v.price
            old.cost_price = v.cost_price
            old.active = v.active
            if v.stock_quantity != old.stock_quantity:
                delta = v.stock_quantity - old.stock_quantity
                old.stock_quantity = v.stock_quantity
                db.add(
                    InventoryMovement(
                        organization_id=organization_id,
                        product_id=product.id,
                        type="adjustment",
                        quantity=delta,
                        reason="variant stock edit",
                    )
                )
        else:
            db.add(
                ProductVariant(
                    organization_id=organization_id,
                    product_id=product.id,
                    sku=v.sku,
                    name=v.name,
                    attributes=v.attributes,
                    price=v.price,
                    cost_price=v.cost_price,
                    stock_quantity=v.stock_quantity,
                    active=v.active,
                )
            )
    for sku, old in existing.items():
        if sku not in incoming:
            db.delete(old)


@router.get(
    "",
    response_model=Page[ProductRead],
    summary="List products",
    description="Paginated, searchable with category/status/stock filters and sorting.",
)
def list_products(
    params: ProductListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("products.read")),
) -> Page[ProductRead]:
    repo = ProductRepository(db)
    page = repo.list_page(
        user.effective_organization_id,
        page=params.page, page_size=params.page_size,
        search=params.search, category=params.category,
        status=params.status, stock_status=params.stock_status,
        sort_by=params.sort_by, sort_order=params.sort_order,
    )
    return Page[ProductRead](
        items=[_to_read(p) for p in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/categories",
    response_model=list[str],
    summary="List product categories",
)
def list_categories(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("products.read")),
) -> list[str]:
    return ProductRepository(db).categories(user.effective_organization_id)


@router.post(
    "", response_model=ProductRead, status_code=201, summary="Create a product",
    description="Creates the product and records the initial stock as a 'purchase' movement.",
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.create")),
) -> ProductRead:
    from app.services.billing_service import check_usage_limit

    check_usage_limit(db, actor.effective_organization_id, "products")
    repo = ProductRepository(db)
    existing = db.execute(
        select(Product).where(
            Product.organization_id == actor.effective_organization_id,
            Product.sku == payload.sku,
        )
    ).scalar_one_or_none()
    if existing:
        raise bad_request("SKU_TAKEN", "A product with this SKU already exists")
    _ensure_brand(db, actor.effective_organization_id, payload.brand_id)
    _ensure_variant_skus(db, actor.effective_organization_id, payload.variants)
    category_name = _ensure_category(
        db, actor.effective_organization_id, payload.category_id
    )

    product = repo.create(
        actor.effective_organization_id,
        name=payload.name,
        sku=payload.sku,
        description=payload.description,
        category=_category_name(payload, category_name),
        category_id=payload.category_id,
        price=payload.price,
        cost_price=payload.cost_price,
        stock_quantity=payload.stock_quantity,
        low_stock_threshold=payload.low_stock_threshold,
        status=payload.status,
    )
    if payload.stock_quantity > 0:
        db.add(
            InventoryMovement(
                organization_id=actor.effective_organization_id,
                product_id=product.id,
                type="purchase",
                quantity=payload.stock_quantity,
                reason="initial stock",
            )
        )
    _sync_variants(db, actor.effective_organization_id, product, payload.variants)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="product.created", entity_type="product", entity_id=product.id,
        meta={"sku": product.sku, "name": product.name},
    )
    db.commit()
    if product.stock_quantity <= product.low_stock_threshold:
        emit(
            db,
            organization_id=actor.effective_organization_id,
            event_type="stock.low",
            aggregate_type="product",
            aggregate_id=product.id,
        )
        db.commit()
    cache_invalidate("sf:catalog:*")
    return _to_read(product)


@router.get("/{product_id}", response_model=ProductRead, summary="Get a product")
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("products.read")),
) -> ProductRead:
    product = ProductRepository(db).get(user.effective_organization_id, product_id)
    return _to_read(product)


@router.patch("/{product_id}", response_model=ProductRead, summary="Update a product")
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.update")),
) -> ProductRead:
    repo = ProductRepository(db)
    product = repo.get(actor.effective_organization_id, product_id)
    variant_payload = payload.variants
    data = payload.model_dump(exclude_none=True, exclude={"variants"})
    if "brand_id" in data:
        _ensure_brand(db, actor.effective_organization_id, data["brand_id"])
    if "category_id" in data:
        category_name = _ensure_category(
            db, actor.effective_organization_id, data["category_id"]
        )
        data["category"] = category_name

    if "sku" in data:
        existing = db.execute(
            select(Product).where(
                Product.organization_id == actor.effective_organization_id,
                Product.sku == data["sku"],
                Product.id != product.id,
            )
        ).scalar_one_or_none()
        if existing:
            raise bad_request("SKU_TAKEN", "A product with this SKU already exists")

    stock_delta = data.pop("stock_quantity", None)
    if variant_payload is not None:
        _ensure_variant_skus(
            db, actor.effective_organization_id, variant_payload, exclude_product_id=product.id
        )
    restocked = False
    if stock_delta is not None and stock_delta != product.stock_quantity:
        old_stock = product.stock_quantity
        diff = stock_delta - product.stock_quantity
        if product.stock_quantity + diff < 0:
            raise bad_request("INSUFFICIENT_STOCK", "Stock cannot go below zero")
        product.stock_quantity += diff
        restocked = old_stock == 0 and product.stock_quantity > 0
        db.add(
            InventoryMovement(
                organization_id=actor.effective_organization_id,
                product_id=product.id,
                type="adjustment",
                quantity=diff,
                reason="manual stock edit",
            )
        )

    price_old = product.price if "price" in data else None
    for field, value in data.items():
        setattr(product, field, value)
    if variant_payload is not None:
        _sync_variants(db, actor.effective_organization_id, product, variant_payload)
    if price_old is not None and product.price != price_old:
        db.add(
            PriceHistory(
                organization_id=actor.effective_organization_id,
                product_id=product.id,
                old_price=price_old,
                new_price=product.price,
            )
        )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="product.updated", entity_type="product", entity_id=product.id,
        meta=data,
    )
    db.commit()
    if restocked:
        emit(
            db,
            organization_id=actor.effective_organization_id,
            event_type="inventory.restocked",
            aggregate_type="product",
            aggregate_id=product.id,
        )
        db.commit()
    if product.stock_quantity <= product.low_stock_threshold:
        emit(
            db,
            organization_id=actor.effective_organization_id,
            event_type="stock.low",
            aggregate_type="product",
            aggregate_id=product.id,
        )
        db.commit()
    cache_invalidate("sf:catalog:*")
    return _to_read(repo.get(actor.effective_organization_id, product_id))


@router.delete(
    "/{product_id}",
    status_code=204,
    summary="Deactivate a product",
)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.delete")),
) -> None:
    repo = ProductRepository(db)
    product = repo.get(actor.effective_organization_id, product_id)
    if product.status != "inactive":
        product.status = "inactive"
        log_action(
            db, organization_id=actor.effective_organization_id, user_id=actor.id,
            action="product.deactivated", entity_type="product", entity_id=product.id,
        )
        db.commit()
        cache_invalidate("sf:catalog:*")
