from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_api_key_scopes
from app.api.v1.products import _to_read as _product_to_read
from app.db.session import get_db
from app.models.api_key import ApiKey
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.common import Page
from app.schemas.inventory import InventoryListParams, StockItemRead
from app.schemas.product import ProductListParams, ProductRead

router = APIRouter(prefix="/public", tags=["public-api"])


@router.get(
    "/products",
    response_model=Page[ProductRead],
    summary="List products (API key)",
    description="Read-only product listing for integrations authenticated with an API key.",
)
def public_list_products(
    params: ProductListParams = Depends(),
    db: Session = Depends(get_db),
    key: ApiKey = Depends(require_api_key_scopes("products.read")),
) -> Page[ProductRead]:
    page = ProductRepository(db).list_page(
        key.effective_organization_id,
        page=params.page, page_size=params.page_size,
        search=params.search, category=params.category,
        status=params.status, stock_status=params.stock_status,
        sort_by=params.sort_by, sort_order=params.sort_order,
    )
    return Page[ProductRead](
        items=[_product_to_read(p) for p in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductRead,
    summary="Get a product (API key)",
)
def public_get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    key: ApiKey = Depends(require_api_key_scopes("products.read")),
) -> ProductRead:
    return _product_to_read(
        ProductRepository(db).get(key.effective_organization_id, product_id)
    )


@router.get(
    "/inventory",
    response_model=Page[StockItemRead],
    summary="Stock overview (API key)",
)
def public_stock_overview(
    params: InventoryListParams = Depends(),
    db: Session = Depends(get_db),
    key: ApiKey = Depends(require_api_key_scopes("inventory.read")),
) -> Page[StockItemRead]:
    page = InventoryRepository(db).stock_overview(
        key.effective_organization_id,
        page=params.page, page_size=params.page_size,
        search=params.search, stock_status=params.stock_status,
        category=params.category, sort_by=params.sort_by, sort_order=params.sort_order,
    )
    return Page[StockItemRead](
        items=[
            StockItemRead(
                id=p.id, name=p.name, sku=p.sku, category=p.category,
                stock_quantity=p.stock_quantity,
                low_stock_threshold=p.low_stock_threshold,
                status=p.status, stock_status=p.stock_status,
            )
            for p in page.items
        ],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )
