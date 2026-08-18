from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.order import Order


class Coupon(TimestampMixin, Base):
    __tablename__ = "coupons"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_coupons_org_code"),
        CheckConstraint(
            "discount_type IN ('percent', 'fixed')",
            name="ck_coupons_discount_type",
        ),
        CheckConstraint(
            "(discount_type = 'percent' AND discount_value <= 100) OR discount_type = 'fixed'",
            name="ck_coupons_discount_value_range",
        ),
        CheckConstraint("discount_value > 0", name="ck_coupons_discount_value_positive"),
        CheckConstraint("min_subtotal >= 0", name="ck_coupons_min_subtotal_non_negative"),
        CheckConstraint(
            "max_redemptions IS NULL OR max_redemptions > 0",
            name="ck_coupons_max_redemptions_positive",
        ),
        CheckConstraint(
            "max_per_customer IS NULL OR max_per_customer > 0",
            name="ck_coupons_max_per_customer_positive",
        ),
        Index("ix_coupons_org_status", "organization_id", "active"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    discount_type: Mapped[str] = mapped_column(String(10), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    min_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    max_redemptions: Mapped[int | None] = mapped_column(nullable=True)
    max_per_customer: Mapped[int | None] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    redemptions: Mapped[list[CouponRedemption]] = relationship(
        back_populates="coupon", cascade="all, delete-orphan"
    )

    @property
    def usage_count(self) -> int:
        return len(self.redemptions)


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "order_id", name="uq_coupon_redemptions_org_order"
        ),
        Index("ix_coupon_redemptions_org_coupon", "organization_id", "coupon_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    coupon_id: Mapped[UUID] = mapped_column(
        ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(), nullable=False
    )

    coupon: Mapped[Coupon] = relationship(back_populates="redemptions")
    order: Mapped[Order] = relationship()
    customer: Mapped[Customer | None] = relationship()
