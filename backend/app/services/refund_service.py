"""Return requests and refunds: customer-facing request flow + admin workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.models.customer_account import CustomerAccount
from app.models.order import Order, OrderItem
from app.models.refund import Refund, ReturnRequest
from app.models.user import User
from app.schemas.refund import RefundRead, ReturnRequestRead

RETURN_STATUSES = ("pending", "approved", "received", "completed", "rejected")
RETURN_ORDERABLE_STATUSES = ("shipped", "delivered")

TRANSITIONS = {
    "pending": ("approve", "reject"),
    "approved": ("receive",),
    "received": ("complete",),
}


def _get_order(db: Session, org_id: UUID, order_id: UUID) -> Order:
    order = db.execute(
        select(Order).where(Order.organization_id == org_id, Order.id == order_id)
    ).scalar_one_or_none()
    if order is None:
        raise not_found("Order")
    return order


def _get_return(db: Session, org_id: UUID, return_id: UUID) -> ReturnRequest:
    request = db.execute(
        select(ReturnRequest).where(
            ReturnRequest.organization_id == org_id, ReturnRequest.id == return_id
        )
    ).scalar_one_or_none()
    if request is None:
        raise not_found("ReturnRequest")
    return request


def _returned_quantity(db: Session, order_item_id: UUID) -> int:
    total = db.execute(
        select(func.coalesce(func.sum(ReturnRequest.quantity), 0)).where(
            ReturnRequest.order_item_id == order_item_id,
            ReturnRequest.status.in_(("pending", "approved", "received", "completed")),
        )
    ).scalar_one()
    return int(total)


def request_return(
    db: Session,
    org_id: UUID,
    account: CustomerAccount,
    order_id: UUID,
    order_item_id: UUID,
    quantity: int,
    reason: str | None,
    condition: str,
) -> ReturnRequest:
    order = _get_order(db, org_id, order_id)
    if order.customer_id != account.customer_id:
        raise forbidden("RETURN_FORBIDDEN", "This order does not belong to your account")
    if order.status not in RETURN_ORDERABLE_STATUSES:
        raise bad_request(
            "RETURN_NOT_ELIGIBLE",
            f"Returns are only allowed for orders in: {', '.join(RETURN_ORDERABLE_STATUSES)}",
        )
    item = db.execute(
        select(OrderItem).where(
            OrderItem.id == order_item_id, OrderItem.order_id == order.id
        )
    ).scalar_one_or_none()
    if item is None:
        raise not_found("OrderItem")
    already = _returned_quantity(db, item.id)
    if already + quantity > item.quantity:
        raise bad_request(
            "RETURN_QUANTITY_EXCEEDED",
            f"Only {item.quantity - already} more units of this item can be returned",
        )
    request = ReturnRequest(
        organization_id=org_id,
        order_id=order.id,
        order_item_id=item.id,
        product_id=item.product_id,
        product_variant_id=item.product_variant_id,
        quantity=quantity,
        reason=reason,
        condition=condition,
        status="pending",
    )
    db.add(request)
    db.commit()
    return request


def decide_return(
    db: Session, org_id: UUID, return_id: UUID, action: str, actor: User
) -> ReturnRequest:
    request = _get_return(db, org_id, return_id)
    allowed = TRANSITIONS.get(request.status, ())
    if action not in allowed:
        raise bad_request(
            "RETURN_BAD_TRANSITION",
            f"Cannot '{action}' a return in status '{request.status}'",
        )
    if action == "approve":
        request.status = "approved"
        request.decided_at = datetime.now(UTC)
        request.decided_by = actor.id
        refund = Refund(
            organization_id=org_id,
            order_id=request.order_id,
            return_request_id=request.id,
            amount=_refund_amount(db, request),
            reason="Return approved",
        )
        db.add(refund)
    elif action == "reject":
        request.status = "rejected"
        request.decided_at = datetime.now(UTC)
        request.decided_by = actor.id
    elif action == "receive":
        request.status = "received"
    elif action == "complete":
        request.status = "completed"
    db.commit()
    return request


def _refund_amount(db: Session, request: ReturnRequest) -> Decimal:
    item = db.get(OrderItem, request.order_item_id)
    return item.unit_price * request.quantity


def list_returns(db: Session, org_id: UUID) -> list[ReturnRequest]:
    return list(
        db.execute(
            select(ReturnRequest)
            .where(ReturnRequest.organization_id == org_id)
            .order_by(ReturnRequest.created_at.desc())
        ).scalars()
    )


def list_customer_returns(
    db: Session, org_id: UUID, customer_id: UUID
) -> list[ReturnRequest]:
    return list(
        db.execute(
            select(ReturnRequest)
            .where(
                ReturnRequest.organization_id == org_id,
                ReturnRequest.order_id.in_(
                    select(Order.id).where(Order.customer_id == customer_id)
                ),
            )
            .order_by(ReturnRequest.created_at.desc())
        ).scalars()
    )


# ---- refunds ---------------------------------------------------------------


def _sum_refunds(db: Session, order_id: UUID) -> Decimal:
    total = db.execute(
        select(func.coalesce(func.sum(Refund.amount), 0)).where(
            Refund.order_id == order_id,
            Refund.status.in_(("pending", "processed")),
        )
    ).scalar_one()
    return Decimal(total)


def create_manual_refund(
    db: Session,
    org_id: UUID,
    order_id: UUID,
    amount: Decimal,
    reason: str | None,
    payment_id: UUID | None,
    actor: User,
) -> Refund:
    order = _get_order(db, org_id, order_id)
    remaining = order.total - _sum_refunds(db, order.id)
    if amount > remaining:
        raise bad_request(
            "REFUND_EXCEEDS_ORDER",
            f"Refund of {amount} exceeds the refundable balance of {remaining}",
        )
    refund = Refund(
        organization_id=org_id,
        order_id=order.id,
        payment_id=payment_id,
        amount=amount,
        reason=reason,
        status="pending",
        refunded_by=actor.id,
    )
    db.add(refund)
    db.commit()
    return refund


def act_on_refund(
    db: Session, org_id: UUID, refund_id: UUID, action: str, actor: User
) -> Refund:
    refund = db.execute(
        select(Refund).where(Refund.organization_id == org_id, Refund.id == refund_id)
    ).scalar_one_or_none()
    if refund is None:
        raise not_found("Refund")
    if action == "process":
        if refund.status == "processed":
            raise bad_request("REFUND_ALREADY_PROCESSED", "Refund already processed")
        refund.status = "processed"
        refund.processed_at = datetime.now(UTC)
        refund.refunded_by = actor.id
    elif action == "fail":
        refund.status = "failed"
    db.commit()
    return refund


def list_refunds(db: Session, org_id: UUID) -> list[Refund]:
    return list(
        db.execute(
            select(Refund)
            .where(Refund.organization_id == org_id)
            .order_by(Refund.created_at.desc())
        ).scalars()
    )


# ---- read models -----------------------------------------------------------


def return_read(request: ReturnRequest) -> ReturnRequestRead:
    product = request.product
    return ReturnRequestRead(
        id=request.id,
        order_id=request.order_id,
        order_item_id=request.order_item_id,
        product_id=request.product_id,
        product_variant_id=request.product_variant_id,
        product_name=product.name if product else "",
        quantity=request.quantity,
        reason=request.reason,
        condition=request.condition,
        status=request.status,
        created_at=request.created_at,
        decided_at=request.decided_at,
    )


def refund_read(refund: Refund) -> RefundRead:
    return RefundRead(
        id=refund.id,
        order_id=refund.order_id,
        order_number=refund.order.order_number if refund.order else "",
        return_request_id=refund.return_request_id,
        payment_id=refund.payment_id,
        amount=refund.amount,
        reason=refund.reason,
        status=refund.status,
        created_at=refund.created_at,
        processed_at=refund.processed_at,
    )
