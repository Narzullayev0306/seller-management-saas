from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.product_variant import ProductVariant


class Cart(TimestampMixin, Base):
    """A shopper's cart. Either a registered customer's cart (customer_id set)
    or an anonymous guest cart identified by a client-generated session token."""

    __tablename__ = "carts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "customer_id", name="uq_carts_org_customer"
        ),
        UniqueConstraint(
            "organization_id", "session_token", name="uq_carts_org_session"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    session_token: Mapped[str | None] = mapped_column(String(64), nullable=True)

    customer: Mapped[Customer | None] = relationship()
    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", lazy="selectin"
    )


class CartItem(TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "product_id",
            "product_variant_id",
            name="uq_cart_items_cart_product_variant",
        ),
        CheckConstraint(
            "quantity > 0 AND quantity <= 100", name="ck_cart_items_quantity_range"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    cart_id: Mapped[UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    product_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(nullable=False)

    cart: Mapped[Cart] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
    variant: Mapped[ProductVariant | None] = relationship()
