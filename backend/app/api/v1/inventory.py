from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.redis import cache_invalidate
from app.db.session import get_db
from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.models.user import User
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.common import Page
from app.schemas.inventory import (
    AdjustmentCreate,
    InventoryListParams,
    MovementListParams,
    MovementRead,
    StockItemRead,
)
from app.services.inventory_service import InventoryService
from app.services.notification_service import notify_low_stock

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _stock_levels(db: Session, organization_id, movements) -> dict:
    """Map movement id -> (previous_stock, new_stock) by replaying the ledger."""
    product_ids = {m.product_id for m in movements}
    if not product_ids:
        return {}
    current = {
        p.id: p.stock_quantity
        for p in db.execute(
            select(Product).where(
                Product.organization_id == organization_id,
                Product.id.in_(product_ids),
            )
        ).scalars()
    }
    rows = db.execute(
        select(InventoryMovement).where(
            InventoryMovement.organization_id == organization_id,
            InventoryMovement.product_id.in_(product_ids),
        ).order_by(InventoryMovement.created_at, InventoryMovement.id)
    ).scalars().all()
    by_product: dict = defaultdict(list)
    for m in rows:
        by_product[m.product_id].append(m)
    levels: dict = {}
    for pid, movs in by_product.items():
        total = sum(m.quantity for m in movs)
        prev = current.get(pid, 0) - total
        for m in movs:
            levels[m.id] = (prev, prev + m.quantity)
            prev += m.quantity
    return levels


def _movement_to_read(movement, product_name: str, levels: dict | None = None) -> MovementRead:
    prev_new = (levels or {}).get(movement.id)
    return MovementRead(
        id=movement.id,
        product_id=movement.product_id,
        product_name=product_name,
        type=movement.type,
        quantity=movement.quantity,
        reason=movement.reason,
        reference_id=movement.reference_id,
        previous_stock=prev_new[0] if prev_new else None,
        new_stock=prev_new[1] if prev_new else None,
        created_at=movement.created_at,
    )


@router.get(
    "",
    response_model=Page[StockItemRead],
    summary="Stock overview",
    description="Paginated stock levels with low/out-of-stock filters.",
)
def stock_overview(
    params: InventoryListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("inventory.read")),
) -> Page[StockItemRead]:
    repo = InventoryRepository(db)
    page = repo.stock_overview(
        user.effective_organization_id,
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


@router.get(
    "/movements",
    response_model=Page[MovementRead],
    summary="Stock movement history",
    description="Signed quantities: negative for sales, positive for purchases/returns.",
)
def list_movements(
    params: MovementListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("inventory.read")),
) -> Page[MovementRead]:
    repo = InventoryRepository(db)
    page = repo.list_movements(
        user.effective_organization_id,
        page=params.page, page_size=params.page_size,
        product_id=params.product_id, movement_type=params.type,
        sort_by=params.sort_by, sort_order=params.sort_order,
    )
    names = {
        p.id: p.name
        for p in db.execute(
            select(Product).where(Product.organization_id == user.effective_organization_id)
        ).scalars()
    }
    levels = _stock_levels(db, user.effective_organization_id, page.items)
    return Page[MovementRead](
        items=[_movement_to_read(m, names.get(m.product_id, ""), levels) for m in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.post(
    "/adjustments",
    response_model=StockItemRead,
    status_code=201,
    summary="Adjust stock",
    description=(
        "purchase/return increase stock, adjustment decreases it. "
        "Stock can never go below zero."
    ),
    responses={409: {"description": "Insufficient stock or product not found"}},
)
def adjust_stock(
    payload: AdjustmentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("inventory.update")),
) -> StockItemRead:
    product = InventoryService(db).apply_adjustment(
        actor.effective_organization_id, payload, actor.id
    )
    if product.stock_quantity <= product.low_stock_threshold:
        notify_low_stock(db, actor.effective_organization_id, product.id)
        db.commit()
    cache_invalidate("sf:catalog:*")
    return StockItemRead(
        id=product.id, name=product.name, sku=product.sku,
        category=product.category, stock_quantity=product.stock_quantity,
        low_stock_threshold=product.low_stock_threshold,
        status=product.status, stock_status=product.stock_status,
    )
