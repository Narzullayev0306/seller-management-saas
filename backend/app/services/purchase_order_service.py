"""Purchase orders: create from a supplier, receive stock on arrival."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderItemRead,
    PurchaseOrderRead,
)

PO_TRANSITIONS = {
    "draft": ("ordered", "cancelled"),
    "ordered": ("received", "cancelled"),
    "received": (),
    "cancelled": (),
}


def _next_po_number(db: Session, org_id: UUID) -> str:
    latest = db.execute(
        select(PurchaseOrder.po_number)
        .where(PurchaseOrder.organization_id == org_id)
        .order_by(PurchaseOrder.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    n = 1
    if latest and latest.startswith("PO-"):
        try:
            n = int(latest.split("-")[1]) + 1
        except (IndexError, ValueError):
            n = 1
    return f"PO-{n:06d}"


def _get_po(db: Session, org_id: UUID, po_id: UUID) -> PurchaseOrder:
    po = db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.organization_id == org_id, PurchaseOrder.id == po_id
        )
    ).scalar_one_or_none()
    if po is None:
        raise not_found("PurchaseOrder")
    return po


def create_purchase_order(
    db: Session, org_id: UUID, payload: PurchaseOrderCreate, actor: User
) -> PurchaseOrder:
    if payload.supplier_id is not None:
        supplier = db.get(Supplier, payload.supplier_id)
        if supplier is None or supplier.organization_id != org_id:
            raise not_found("Supplier")
    for item in payload.items:
        product = db.get(Product, item.product_id)
        if product is None or product.organization_id != org_id:
            raise not_found("Product")

    po = PurchaseOrder(
        organization_id=org_id,
        supplier_id=payload.supplier_id,
        po_number=_next_po_number(db, org_id),
        status="draft",
        expected_date=payload.expected_date,
        notes=payload.notes,
        created_by=actor.id,
    )
    db.add(po)
    db.flush()
    total = Decimal("0")
    for item in payload.items:
        subtotal = item.unit_cost * item.quantity
        total += subtotal
        db.add(
            PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                subtotal=subtotal,
            )
        )
    po.total = total
    db.commit()
    return po


def update_po_status(
    db: Session, org_id: UUID, po_id: UUID, new_status: str, actor: User
) -> PurchaseOrder:
    po = _get_po(db, org_id, po_id)
    if new_status not in PO_TRANSITIONS.get(po.status, ()):
        raise bad_request(
            "PO_BAD_TRANSITION",
            f"Cannot move purchase order from '{po.status}' to '{new_status}'",
        )
    if new_status == "received":
        for item in po.items:
            product = db.get(Product, item.product_id)
            if product is None:
                continue
            product.stock_quantity += item.quantity
            db.add(
                InventoryMovement(
                    organization_id=org_id,
                    product_id=item.product_id,
                    type="purchase",
                    quantity=item.quantity,
                    reason=f"purchase order {po.po_number}",
                )
            )
        po.received_at = datetime.now(UTC)
    po.status = new_status
    db.commit()
    return po


def delete_po(db: Session, org_id: UUID, po_id: UUID) -> None:
    po = _get_po(db, org_id, po_id)
    if po.status == "received":
        raise bad_request(
            "PO_RECEIVED", "Received purchase orders cannot be deleted"
        )
    db.delete(po)
    db.commit()


def list_pos(db: Session, org_id: UUID) -> list[PurchaseOrder]:
    return list(
        db.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.organization_id == org_id)
            .order_by(PurchaseOrder.created_at.desc())
        ).scalars()
    )


def po_read(po: PurchaseOrder) -> PurchaseOrderRead:
    return PurchaseOrderRead(
        id=po.id,
        supplier_id=po.supplier_id,
        supplier_name=po.supplier.name if po.supplier else None,
        po_number=po.po_number,
        status=po.status,
        expected_date=po.expected_date,
        notes=po.notes,
        total=po.total,
        created_by=po.created_by,
        created_at=po.created_at,
        updated_at=po.updated_at,
        received_at=po.received_at,
        items=[
            PurchaseOrderItemRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "",
                sku=item.product.sku if item.product else "",
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                subtotal=item.subtotal,
            )
            for item in po.items
        ],
    )
