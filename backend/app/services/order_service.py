from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ApiError, bad_request, not_found
from app.models.customer import Customer
from app.models.inventory import InventoryMovement
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sale import Sale
from app.models.seller import Seller
from app.schemas.order import OrderCreate
from app.services.audit_service import log_action
from app.services.coupon_service import apply_coupon
from app.services.order_state_machine import OrderStateMachine
from app.services.outbox_service import emit


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ---- create ---------------------------------------------------------

    def create_order(
        self,
        organization_id: UUID,
        payload: OrderCreate,
        actor_user_id: UUID | None,
        seller_scope: UUID | None = None,
    ) -> Order:
        customer = self._get_customer(organization_id, payload.customer_id)
        seller = None
        if payload.seller_id is not None:
            seller = self._get_seller(organization_id, payload.seller_id)
            if seller_scope is not None and seller.id != seller_scope:
                raise ApiError(403, "PERMISSION_DENIED", "You can only create orders for yourself")

        product_ids = [i.product_id for i in payload.items]
        products = self._get_products(organization_id, product_ids, for_update=True)
        variant_ids = [i.product_variant_id for i in payload.items if i.product_variant_id]
        variants = self._get_variants(
            organization_id, product_ids, variant_ids, for_update=True
        ) if variant_ids else {}

        order = Order(
            organization_id=organization_id,
            order_number=self._next_order_number(),
            seller_id=seller.id if seller else None,
            customer_id=customer.id,
            created_by=actor_user_id,
            status="pending",
            payment_status=payload.payment_status,
        )
        self.db.add(order)
        self.db.flush()

        subtotal = Decimal("0")
        items: list[OrderItem] = []
        low_stock_products: list[UUID] = []
        for item in payload.items:
            product = products[item.product_id]
            variant = variants.get(item.product_variant_id) if item.product_variant_id else None
            if item.product_variant_id and variant is None:
                raise bad_request(
                    "VARIANT_NOT_FOUND",
                    "Product variant does not belong to this product",
                )
            if variant is not None:
                if not variant.active:
                    raise ApiError(
                        409, "VARIANT_INACTIVE", f"Variant '{variant.name}' is inactive"
                    )
                if variant.stock_quantity < item.quantity:
                    raise ApiError(
                        409,
                        "INSUFFICIENT_STOCK",
                        f"Variant '{variant.name}' has only {variant.stock_quantity} in stock",
                        {"product_id": str(product.id), "available": variant.stock_quantity},
                    )
                variant.stock_quantity -= item.quantity
                unit_price = variant.price
            else:
                if product.stock_quantity < item.quantity:
                    raise ApiError(
                        409,
                        "INSUFFICIENT_STOCK",
                        f"Product '{product.name}' has only {product.stock_quantity} in stock",
                        {"product_id": str(product.id), "available": product.stock_quantity},
                    )
                product.stock_quantity -= item.quantity
                if product.stock_quantity <= product.low_stock_threshold:
                    low_stock_products.append(product.id)
                unit_price = product.price
            self.db.add(
                InventoryMovement(
                    organization_id=organization_id,
                    product_id=product.id,
                    type="sale",
                    quantity=-item.quantity,
                    reason="order created",
                    reference_id=order.id,
                )
            )
            line_total = unit_price * item.quantity
            subtotal += line_total
            items.append(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_variant_id=variant.id if variant else None,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=line_total,
                )
            )

        if payload.discount > subtotal:
            raise ApiError(
                422, "VALIDATION_ERROR", "Discount cannot exceed subtotal"
            )

        discount = payload.discount
        if payload.coupon_code:
            if discount > 0:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "Use either discount or coupon_code, not both",
                )
            discount = apply_coupon(
                self.db, organization_id, order, customer.id, payload.coupon_code, subtotal
            )

        order.items = items
        order.subtotal = subtotal
        order.discount = discount
        order.tax = payload.tax
        order.shipping_fee = payload.shipping_fee
        order.total = subtotal - discount + payload.tax + payload.shipping_fee
        self.db.flush()

        log_action(
            self.db,
            organization_id=organization_id,
            user_id=actor_user_id,
            action="order.created",
            entity_type="order",
            entity_id=order.id,
            meta={"order_number": order.order_number, "total": str(order.total)},
        )
        for product_id in low_stock_products:
            emit(
                self.db,
                organization_id=organization_id,
                event_type="stock.low",
                aggregate_type="product",
                aggregate_id=product_id,
            )
        emit(
            self.db,
            organization_id=organization_id,
            event_type="order.created",
            aggregate_type="order",
            aggregate_id=order.id,
            payload={
                "order_number": order.order_number,
                "actor_user_id": str(actor_user_id) if actor_user_id else None,
            },
        )
        self.db.commit()
        return self._reload(order.id)

    # ---- status transitions ---------------------------------------------

    def update_status(
        self,
        organization_id: UUID,
        order_id: UUID,
        new_status: str,
        actor_user_id: UUID,
        seller_scope: UUID | None = None,
    ) -> Order:
        order = self._get_order(organization_id, order_id)
        if seller_scope is not None and order.seller_id != seller_scope:
            raise ApiError(403, "PERMISSION_DENIED", "You can only update your own orders")
        if order.status == new_status:
            return order
        old_status = order.status
        OrderStateMachine.assert_transition(old_status, new_status)

        if new_status == "delivered":
            self._finalize_delivery(organization_id, order)
        elif new_status == "cancelled":
            self._cancel_order(organization_id, order)

        order.status = new_status
        log_action(
            self.db,
            organization_id=organization_id,
            user_id=actor_user_id,
            action="order.status_changed",
            entity_type="order",
            entity_id=order.id,
            meta={"from": old_status, "to": new_status},
        )
        if new_status == "cancelled":
            emit(
                self.db,
                organization_id=organization_id,
                event_type="order.cancelled",
                aggregate_type="order",
                aggregate_id=order.id,
                payload={
                    "order_number": order.order_number,
                    "actor_user_id": str(actor_user_id) if actor_user_id else None,
                },
            )
        self.db.commit()
        return self._reload(order.id)

    def delete_order(
        self, organization_id: UUID, order_id: UUID, actor_user_id: UUID
    ) -> None:
        order = self._get_order(organization_id, order_id)
        old_status = order.status
        OrderStateMachine.assert_transition(old_status, "cancelled")
        self._cancel_order(organization_id, order)
        order.status = "cancelled"
        log_action(
            self.db,
            organization_id=organization_id,
            user_id=actor_user_id,
            action="order.cancelled",
            entity_type="order",
            entity_id=order.id,
            meta={"from": old_status, "to": "cancelled"},
        )
        emit(
            self.db,
            organization_id=organization_id,
            event_type="order.cancelled",
            aggregate_type="order",
            aggregate_id=order.id,
            payload={
                "order_number": order.order_number,
                "actor_user_id": str(actor_user_id) if actor_user_id else None,
            },
        )
        self.db.commit()

    def update_payment_status(
        self,
        organization_id: UUID,
        order_id: UUID,
        new_payment_status: str,
        actor_user_id: UUID,
    ) -> Order:
        order = self._get_order(organization_id, order_id)
        if order.payment_status == new_payment_status:
            return order
        order.payment_status = new_payment_status
        log_action(
            self.db,
            organization_id=organization_id,
            user_id=actor_user_id,
            action="order.payment_status_changed",
            entity_type="order",
            entity_id=order.id,
            meta={"to": new_payment_status},
        )
        self.db.commit()
        return self._reload(order.id)

    # ---- lifecycle internals --------------------------------------------

    def _finalize_delivery(self, organization_id: UUID, order: Order) -> None:
        if order.sale is not None:
            return
        commission = Decimal("0")
        if order.seller is not None:
            commission = (
                order.total * order.seller.commission_rate / Decimal("100")
            ).quantize(Decimal("0.01"))
            order.seller.total_sales += order.total
            order.seller.total_orders += 1
        order.customer.total_orders += 1
        order.customer.total_spent += order.total
        self.db.add(
            Sale(
                organization_id=organization_id,
                order_id=order.id,
                seller_id=order.seller_id,
                customer_id=order.customer_id,
                amount=order.total,
                commission_amount=commission,
            )
        )

    def _cancel_order(self, organization_id: UUID, order: Order) -> None:
        product_ids = [item.product_id for item in order.items]
        products = self._get_products(organization_id, product_ids, for_update=True)
        variant_ids = [
            item.product_variant_id for item in order.items if item.product_variant_id
        ]
        variants = (
            self._get_variants(
                organization_id, product_ids, variant_ids, for_update=True
            )
            if variant_ids
            else {}
        )
        for item in order.items:
            product = products.get(item.product_id)
            variant = variants.get(item.product_variant_id) if item.product_variant_id else None
            if variant is not None:
                variant.stock_quantity += item.quantity
            elif product is not None:
                product.stock_quantity += item.quantity
            if product is not None:
                self.db.add(
                    InventoryMovement(
                        organization_id=organization_id,
                        product_id=product.id,
                        type="return",
                        quantity=item.quantity,
                        reason="order cancelled",
                        reference_id=order.id,
                    )
                )
        if order.sale is not None:
            sale = order.sale
            if sale.seller_id is not None and order.seller is not None:
                order.seller.total_sales -= sale.amount
                order.seller.total_orders = max(0, order.seller.total_orders - 1)
            order.customer.total_orders = max(0, order.customer.total_orders - 1)
            order.customer.total_spent -= sale.amount
            self.db.delete(sale)

    # ---- helpers ---------------------------------------------------------

    def _reload(self, order_id: UUID) -> Order:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.seller),
                selectinload(Order.customer),
                selectinload(Order.creator),
            )
            .where(Order.id == order_id)
        )
        return self.db.execute(stmt).scalar_one()

    def _get_order(self, organization_id: UUID, order_id: UUID) -> Order:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.seller),
                selectinload(Order.customer),
                selectinload(Order.sale),
            )
            .where(Order.organization_id == organization_id, Order.id == order_id)
        )
        order = self.db.execute(stmt).scalar_one_or_none()
        if order is None:
            raise not_found("Order")
        return order

    def _get_customer(self, organization_id: UUID, customer_id: UUID) -> Customer:
        customer = self.db.execute(
            select(Customer).where(
                Customer.organization_id == organization_id,
                Customer.id == customer_id,
            )
        ).scalar_one_or_none()
        if customer is None:
            raise not_found("Customer")
        return customer

    def _get_seller(self, organization_id: UUID, seller_id: UUID) -> Seller:
        seller = self.db.execute(
            select(Seller).where(
                Seller.organization_id == organization_id, Seller.id == seller_id
            )
        ).scalar_one_or_none()
        if seller is None:
            raise not_found("Seller")
        return seller

    def _get_products(
        self, organization_id: UUID, product_ids: list[UUID], for_update: bool = False
    ) -> dict[UUID, Product]:
        stmt = select(Product).where(
            Product.organization_id == organization_id,
            Product.id.in_(set(product_ids)),
        )
        if for_update:
            stmt = stmt.with_for_update()
        rows = self.db.execute(stmt).scalars()
        products = {p.id: p for p in rows}
        missing = set(product_ids) - set(products)
        if missing:
            raise not_found("Product")
        return products

    def _get_variants(
        self,
        organization_id: UUID,
        product_ids: list[UUID],
        variant_ids: list[UUID],
        for_update: bool = False,
    ) -> dict[UUID, ProductVariant]:
        stmt = select(ProductVariant).where(
            ProductVariant.organization_id == organization_id,
            ProductVariant.id.in_(set(variant_ids)),
            ProductVariant.product_id.in_(set(product_ids)),
        )
        if for_update:
            stmt = stmt.with_for_update()
        rows = self.db.execute(stmt).scalars()
        return {v.id: v for v in rows}

    def _next_order_number(self) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%d")
        return f"ORD-{stamp}-{uuid4().hex[:6].upper()}"
