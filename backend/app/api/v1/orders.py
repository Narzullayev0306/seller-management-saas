from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import ApiError, forbidden
from app.core.redis import cache_invalidate
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.payment import Payment
from app.models.seller import Seller
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.schemas.common import Page
from app.schemas.order import (
    OrderCreate,
    OrderHistoryEntry,
    OrderListParams,
    OrderPaymentUpdate,
    OrderRead,
    OrderStatusUpdate,
    PaymentRead,
)
from app.services.idempotency_service import (
    claim_idempotency_key,
    store_response,
    wait_for_response,
)
from app.services.order_service import OrderService
from app.services.rbac_service import user_role_codes

router = APIRouter(prefix="/orders", tags=["orders"])


def _to_read(order) -> OrderRead:
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


def _linked_seller(db: Session, user: User) -> Seller | None:
    if "seller" not in user_role_codes(user):
        return None
    return db.execute(
        select(Seller).where(
            Seller.organization_id == user.effective_organization_id,
            Seller.user_id == user.id,
        )
    ).scalar_one_or_none()


@router.get(
    "",
    response_model=Page[OrderRead],
    summary="List orders",
    description=(
        "Paginated with status/seller/customer/date filters and sorting. "
        "Users with the 'seller' role only see their own orders."
    ),
)
def list_orders(
    params: OrderListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("orders.read")),
) -> Page[OrderRead]:
    repo = OrderRepository(db)
    seller = _linked_seller(db, user)
    if "seller" in user_role_codes(user):
        if seller is None:
            return Page[OrderRead](items=[], page=params.page, page_size=params.page_size, total=0, total_pages=0)
        params.seller_id = seller.id
    page = repo.list_page(
        user.effective_organization_id,
        page=params.page, page_size=params.page_size,
        search=params.search, status=params.status,
        payment_status=params.payment_status,
        seller_id=params.seller_id, customer_id=params.customer_id,
        date_from=params.date_from, date_to=params.date_to,
        sort_by=params.sort_by, sort_order=params.sort_order,
    )
    return Page[OrderRead](
        items=[_to_read(o) for o in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.post(
    "",
    response_model=OrderRead,
    status_code=201,
    summary="Create an order",
    description=(
        "Transactional: validates products and stock, decrements inventory, "
        "computes totals and records movements. Rolled back entirely on failure."
    ),
    responses={
        404: {"description": "Product, seller or customer not found"},
        409: {"description": "Insufficient stock"},
        422: {"description": "Validation error (e.g. discount > subtotal)"},
    },
)
def create_order(
    payload: OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("orders.create")),
) -> JSONResponse | OrderRead:
    from app.services.billing_service import check_usage_limit

    check_usage_limit(db, actor.effective_organization_id, "orders_per_month")
    seller = _linked_seller(db, actor)
    if "seller" in user_role_codes(actor):
        if seller is None:
            raise forbidden(
                "SELLER_NOT_LINKED",
                "Your account is not linked to a seller profile",
            )
        payload.seller_id = seller.id
    elif payload.seller_id is not None:
        exists = db.execute(
            select(Seller.id).where(
                Seller.organization_id == actor.effective_organization_id,
                Seller.id == payload.seller_id,
            )
        ).scalar_one_or_none()
        if not exists:
            raise ApiError(404, "SELLER_NOT_FOUND", "Seller not found")

    def _run() -> OrderRead:
        order = OrderService(db).create_order(
            actor.effective_organization_id, payload, actor.id
        )
        cache_invalidate("sf:catalog:*")
        return _to_read(order)

    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        org_id = actor.effective_organization_id
        if not claim_idempotency_key(org_id, idem_key, user_id=actor.id):
            stored = wait_for_response(org_id, idem_key)
            if stored is not None:
                status, body = stored
                return JSONResponse(content=body, status_code=status)
            raise ApiError(
                409,
                "IDEMPOTENCY_IN_PROGRESS",
                "This request is still being processed, please retry shortly",
            )
        result = _run()
        body = result.model_dump(mode="json")
        store_response(org_id, idem_key, 201, body)
        return JSONResponse(content=body, status_code=201)

    return _run()


@router.get("/{order_id}", response_model=OrderRead, summary="Get an order")
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("orders.read")),
) -> OrderRead:
    repo = OrderRepository(db)
    order = repo.get_full(user.effective_organization_id, order_id)
    seller = _linked_seller(db, user)
    if "seller" in user_role_codes(user) and (seller is None or order.seller_id != seller.id):
        raise forbidden("PERMISSION_DENIED", "You can only view your own orders")
    return _to_read(order)


@router.patch(
    "/{order_id}",
    response_model=OrderRead,
    summary="Update order status",
    description=(
        "delivered finalizes the sale (sales row, seller/customer counters); "
        "cancelled restores stock and reverses the sale."
    ),
)
def update_order_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("orders.update")),
) -> OrderRead:
    seller = _linked_seller(db, actor)
    order = OrderService(db).update_status(
        actor.effective_organization_id,
        order_id,
        payload.status,
        actor.id,
        seller_scope=seller.id if seller else None,
    )
    cache_invalidate("sf:catalog:*")
    return _to_read(order)


@router.delete(
    "/{order_id}",
    status_code=204,
    summary="Cancel an order",
    description="Cancels a non-final order, restores stock and reverses any sale.",
)
def delete_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("orders.delete")),
) -> None:
    OrderService(db).delete_order(actor.effective_organization_id, order_id, actor.id)
    cache_invalidate("sf:catalog:*")


@router.patch(
    "/{order_id}/payment",
    response_model=OrderRead,
    summary="Update the payment status",
    description="Moves payment between pending / paid / partially paid / refunded.",
)
def update_order_payment(
    order_id: UUID,
    payload: OrderPaymentUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("orders.update")),
) -> OrderRead:
    order = OrderService(db).update_payment_status(
        actor.effective_organization_id, order_id, payload.payment_status, actor.id
    )
    return _to_read(order)


@router.get(
    "/{order_id}/payments",
    response_model=list[PaymentRead],
    summary="Order payments",
    description="Payments recorded against the order (checkout charges and "
    "provider results).",
)
def order_payments(
    order_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("orders.read")),
) -> list[PaymentRead]:
    repo = OrderRepository(db)
    order = repo.get_full(user.effective_organization_id, order_id)
    seller = _linked_seller(db, user)
    if "seller" in user_role_codes(user) and (seller is None or order.seller_id != seller.id):
        raise forbidden("PERMISSION_DENIED", "You can only view your own orders")
    rows = db.execute(
        select(Payment)
        .where(
            Payment.organization_id == user.effective_organization_id,
            Payment.order_id == order_id,
        )
        .order_by(Payment.created_at.desc())
    ).scalars().all()
    return [
        PaymentRead(
            id=p.id,
            provider=p.provider,
            provider_payment_id=p.provider_payment_id,
            amount=p.amount,
            currency=p.currency,
            status=p.status,
            failure_message=p.failure_message,
            paid_at=p.paid_at,
            created_at=p.created_at,
        )
        for p in rows
    ]


@router.get(
    "/{order_id}/history",
    response_model=list[OrderHistoryEntry],
    summary="Order history",
    description="Chronological audit trail for a single order (created, status and "
    "payment changes).",
)
def order_history(
    order_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("orders.read")),
) -> list[OrderHistoryEntry]:
    repo = OrderRepository(db)
    order = repo.get_full(user.effective_organization_id, order_id)
    seller = _linked_seller(db, user)
    if "seller" in user_role_codes(user) and (seller is None or order.seller_id != seller.id):
        raise forbidden("PERMISSION_DENIED", "You can only view your own orders")
    rows = db.execute(
        select(AuditLog)
        .where(
            AuditLog.organization_id == user.effective_organization_id,
            AuditLog.entity_type == "order",
            AuditLog.entity_id == order_id,
        )
        .order_by(AuditLog.created_at.desc())
    ).scalars().all()
    user_ids = {r.user_id for r in rows if r.user_id is not None}
    users = {
        u.id: u.full_name
        for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars()
    } if user_ids else {}
    return [
        OrderHistoryEntry(
            id=row.id,
            user_id=row.user_id,
            user_name=users.get(row.user_id) if row.user_id else None,
            action=row.action,
            meta=row.meta,
            created_at=row.created_at,
        )
        for row in rows
    ]
