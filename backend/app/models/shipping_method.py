from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class ShippingMethod(TimestampMixin, Base):
    """Delivery option offered to storefront customers."""

    __tablename__ = "shipping_methods"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_shipping_methods_org_name"),
        CheckConstraint("price >= 0", name="ck_shipping_methods_price_non_negative"),
        CheckConstraint(
            "min_order_amount >= 0", name="ck_shipping_methods_min_order_non_negative"
        ),
        CheckConstraint(
            "max_order_amount >= 0", name="ck_shipping_methods_max_order_non_negative"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    min_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    estimated_delivery_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="shipping_methods")
