from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.organization import Organization


class Wishlist(Base):
    """A storefront wishlist owned by a customer account or a guest session."""

    __tablename__ = "wishlists"
    __table_args__ = (
        UniqueConstraint("organization_id", "customer_id", name="uq_wishlists_org_customer"),
        UniqueConstraint("organization_id", "session_token", name="uq_wishlists_org_session"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    session_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped[Organization] = relationship(back_populates="wishlists")
    customer: Mapped[Customer | None] = relationship(back_populates="wishlists")
    items: Mapped[list[WishlistItem]] = relationship(
        back_populates="wishlist", cascade="all, delete-orphan"
    )


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (
        UniqueConstraint(
            "wishlist_id", "product_id", "product_variant_id",
            name="uq_wishlist_items_wishlist_product_variant",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    wishlist_id: Mapped[UUID] = mapped_column(
        ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    product_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    wishlist: Mapped[Wishlist] = relationship(back_populates="items")
