from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.payment import Payment
    from app.models.product import Product
    from app.models.refund import Refund, ReturnRequest
    from app.models.sale import Sale
    from app.models.seller import Seller
    from app.models.user import User


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "order_number", name="uq_orders_org_number"),
        CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_non_negative"),
        CheckConstraint("discount >= 0", name="ck_orders_discount_non_negative"),
        CheckConstraint("tax >= 0", name="ck_orders_tax_non_negative"),
        CheckConstraint("total >= 0", name="ck_orders_total_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_number: Mapped[str] = mapped_column(String(30), nullable=False)
    seller_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    payment_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    tax: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    shipping_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0")
    )
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    seller: Mapped[Seller | None] = relationship(back_populates="orders")
    customer: Mapped[Customer] = relationship(back_populates="orders")
    creator: Mapped[User | None] = relationship()
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )
    sale: Mapped[Sale | None] = relationship(
        back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(back_populates="order")
    return_requests: Mapped[list[ReturnRequest]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    refunds: Mapped[list[Refund]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    product_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")
