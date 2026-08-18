from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import not_found
from app.models.order import Order, OrderItem
from app.repositories.base import OrgRepository, parse_sort_params

ORDER_SORTS = {
    "order_number": Order.order_number,
    "status": Order.status,
    "subtotal": Order.subtotal,
    "total": Order.total,
    "created_at": Order.created_at,
}


class OrderRepository(OrgRepository[Order]):
    model = Order

    def get_full(self, organization_id: UUID, order_id: UUID) -> Order:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.seller),
                selectinload(Order.customer),
                selectinload(Order.creator),
            )
            .where(Order.organization_id == organization_id, Order.id == order_id)
        )
        order = self.db.execute(stmt).scalar_one_or_none()
        if order is None:
            raise not_found("Order")
        return order

    def list_page(
        self,
        organization_id,
        *,
        page,
        page_size,
        search=None,
        status=None,
        payment_status=None,
        seller_id=None,
        customer_id=None,
        date_from=None,
        date_to=None,
        sort_by=None,
        sort_order=None,
        seller_scope: UUID | None = None,
    ):
        sort_by, sort_order = parse_sort_params(sort_by, sort_order, ORDER_SORTS)
        filters = []
        if status:
            filters.append(Order.status == status)
        if payment_status:
            filters.append(Order.payment_status == payment_status)
        if seller_id:
            filters.append(Order.seller_id == seller_id)
        if customer_id:
            filters.append(Order.customer_id == customer_id)
        if date_from:
            filters.append(Order.created_at >= date_from)
        if date_to:
            filters.append(Order.created_at <= date_to)
        if seller_scope:
            filters.append(Order.seller_id == seller_scope)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sorts=ORDER_SORTS,
            search=search,
            search_fields=[Order.order_number],
            filters=filters,
        )


class OrderItemRepository:
    def __init__(self, db) -> None:
        self.db = db

    def by_order(self, order_id: UUID) -> list[OrderItem]:
        stmt = (
            select(OrderItem)
            .options(selectinload(OrderItem.product))
            .where(OrderItem.order_id == order_id)
            .order_by(OrderItem.id)
        )
        return list(self.db.execute(stmt).scalars())
