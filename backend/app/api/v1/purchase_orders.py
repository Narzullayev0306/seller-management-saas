from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.redis import cache_invalidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderRead,
    PurchaseOrderStatusUpdate,
)
from app.services import purchase_order_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.get(
    "",
    response_model=list[PurchaseOrderRead],
    summary="List purchase orders",
)
def list_purchase_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("inventory.read")),
) -> list[PurchaseOrderRead]:
    return [
        purchase_order_service.po_read(po)
        for po in purchase_order_service.list_pos(db, user.effective_organization_id)
    ]


@router.post(
    "",
    response_model=PurchaseOrderRead,
    status_code=201,
    summary="Create a purchase order (draft)",
)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("inventory.update")),
) -> PurchaseOrderRead:
    po = purchase_order_service.create_purchase_order(
        db, actor.effective_organization_id, payload, actor
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="purchase_order.created", entity_type="purchase_order",
        entity_id=po.id, meta={"po_number": po.po_number, "total": str(po.total)},
    )
    db.commit()
    return purchase_order_service.po_read(po)


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderRead,
    summary="Get a purchase order",
)
def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("inventory.read")),
) -> PurchaseOrderRead:
    po = purchase_order_service._get_po(db, user.effective_organization_id, po_id)
    return purchase_order_service.po_read(po)


@router.patch(
    "/{po_id}",
    response_model=PurchaseOrderRead,
    summary="Order, receive or cancel a purchase order",
    description="Receiving adds the ordered quantities to product stock and "
    "records 'purchase' inventory movements.",
)
def update_purchase_order(
    po_id: UUID,
    payload: PurchaseOrderStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("inventory.update")),
) -> PurchaseOrderRead:
    po = purchase_order_service.update_po_status(
        db, actor.effective_organization_id, po_id, payload.status, actor
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="purchase_order.status_changed", entity_type="purchase_order",
        entity_id=po.id, meta={"status": payload.status},
    )
    db.commit()
    cache_invalidate("sf:catalog:*")
    return purchase_order_service.po_read(po)


@router.delete(
    "/{po_id}",
    status_code=204,
    summary="Delete a draft/ordered purchase order",
)
def delete_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("inventory.update")),
) -> None:
    purchase_order_service.delete_po(db, actor.effective_organization_id, po_id)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="purchase_order.deleted", entity_type="purchase_order",
        entity_id=po_id, meta={"id": str(po_id)},
    )
    db.commit()
