"""Coupon validation and redemption.

Validation is pure (read-only). Applying a coupon locks the coupon row
(FOR UPDATE) so concurrent redemptions cannot exceed the limits, and
records a redemption in the same transaction as the order.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.models.coupon import Coupon, CouponRedemption
from app.models.order import Order


def _now() -> datetime:
    return datetime.now(UTC)


def validate_coupon(
    db: Session,
    organization_id: UUID,
    code: str,
    subtotal: Decimal,
    customer_id: UUID | None = None,
    coupon_row: Coupon | None = None,
) -> Coupon:
    """Validate a coupon for a subtotal. Raises ApiError with a stable code
    on any violation; returns the coupon row when valid."""
    coupon = coupon_row
    if coupon is None:
        coupon = db.execute(
            select(Coupon).where(
                Coupon.organization_id == organization_id,
                func.upper(Coupon.code) == code.strip().upper(),
            )
        ).scalar_one_or_none()
        if coupon is None:
            raise bad_request("COUPON_NOT_FOUND", "Coupon code is invalid")
    if not coupon.active:
        raise bad_request("COUPON_INACTIVE", "This coupon is no longer active")
    now = _now()
    if coupon.starts_at is not None and now < coupon.starts_at:
        raise bad_request("COUPON_NOT_STARTED", "This coupon is not active yet")
    if coupon.expires_at is not None and now > coupon.expires_at:
        raise bad_request("COUPON_EXPIRED", "This coupon has expired")
    if subtotal < coupon.min_subtotal:
        raise bad_request(
            "COUPON_MIN_SUBTOTAL",
            f"Minimum order subtotal for this coupon is {coupon.min_subtotal}",
        )
    if coupon.max_redemptions is not None:
        used = db.execute(
            select(func.count(CouponRedemption.id)).where(
                CouponRedemption.organization_id == organization_id,
                CouponRedemption.coupon_id == coupon.id,
            )
        ).scalar_one()
        if used >= coupon.max_redemptions:
            raise bad_request("COUPON_USED_UP", "This coupon has been fully redeemed")
    if coupon.max_per_customer is not None and customer_id is not None:
        per_customer = db.execute(
            select(func.count(CouponRedemption.id)).where(
                CouponRedemption.organization_id == organization_id,
                CouponRedemption.coupon_id == coupon.id,
                CouponRedemption.customer_id == customer_id,
            )
        ).scalar_one()
        if per_customer >= coupon.max_per_customer:
            raise bad_request(
                "COUPON_LIMIT_REACHED",
                "You have already used this coupon",
            )
    return coupon


def compute_discount(coupon: Coupon, subtotal: Decimal) -> Decimal:
    if coupon.discount_type == "percent":
        amount = subtotal * coupon.discount_value / Decimal("100")
    else:
        amount = coupon.discount_value
    return min(amount, subtotal).quantize(Decimal("0.01"))


def apply_coupon(
    db: Session,
    organization_id: UUID,
    order: Order,
    customer_id: UUID,
    code: str,
    subtotal: Decimal,
) -> Decimal:
    """Validate (with FOR UPDATE) and apply a coupon to an order.

    Returns the discount amount, set on the order's discount field, and
    records the redemption. Must be called inside the order transaction.
    """
    coupon = db.execute(
        select(Coupon)
        .where(
            Coupon.organization_id == organization_id,
            func.upper(Coupon.code) == code.strip().upper(),
        )
        .with_for_update()
    ).scalar_one_or_none()
    if coupon is None:
        raise bad_request("COUPON_NOT_FOUND", "Coupon code is invalid")

    already = db.execute(
        select(CouponRedemption).where(
            CouponRedemption.organization_id == organization_id,
            CouponRedemption.order_id == order.id,
        )
    ).scalar_one_or_none()
    if already is not None:
        return already.discount_amount

    validate_coupon(
        db, organization_id, code, subtotal, customer_id, coupon_row=coupon
    )
    discount = compute_discount(coupon, subtotal)
    db.add(
        CouponRedemption(
            organization_id=organization_id,
            coupon_id=coupon.id,
            order_id=order.id,
            customer_id=customer_id,
            discount_amount=discount,
        )
    )
    return discount


def get_coupon(db: Session, organization_id: UUID, coupon_id: UUID) -> Coupon:
    coupon = db.execute(
        select(Coupon).where(
            Coupon.organization_id == organization_id, Coupon.id == coupon_id
        )
    ).scalar_one_or_none()
    if coupon is None:
        raise not_found("Coupon")
    return coupon
