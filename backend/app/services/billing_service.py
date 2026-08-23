"""Billing: plan catalog, subscription, plan limits and feature flags.

Plans are defined in code (PLAN_CATALOG) and the organization's plan is
stored on ``organizations.plan``. A ``Subscription`` row is created lazily
and a ``Invoice`` row is recorded on every plan change. Limits are enforced
through :func:`check_usage_limit` before resource creation and features via
:func:`require_feature`.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import forbidden, payment_required
from app.models.billing import Invoice, Subscription
from app.models.organization import Organization
from app.models.product import Product
from app.models.user import User
from app.services.audit_service import log_action

FREE = "free"
PRO = "pro"
ENTERPRISE = "enterprise"

ALL_FEATURES = [
    "webhooks",
    "api_keys",
    "custom_domain",
    "advanced_analytics",
    "export",
    "priority_support",
]

PLAN_CATALOG: dict[str, dict] = {
    FREE: {
        "name": "Free",
        "price": Decimal("0.00"),
        "description": "For solo sellers getting started",
        "limits": {
            "users": 25,
            "products": 500,
            "orders_per_month": 2000,
        },
        "features": ["advanced_analytics"],
    },
    PRO: {
        "name": "Pro",
        "price": Decimal("29.00"),
        "description": "For growing teams",
        "limits": {
            "users": 100,
            "products": 5000,
            "orders_per_month": 50000,
        },
        "features": [
            "webhooks",
            "api_keys",
            "custom_domain",
            "advanced_analytics",
            "export",
        ],
    },
    ENTERPRISE: {
        "name": "Enterprise",
        "price": Decimal("99.00"),
        "description": "Unlimited everything, priority support",
        "limits": {
            "users": None,
            "products": None,
            "orders_per_month": None,
        },
        "features": list(ALL_FEATURES),
    },
}


def get_plan_catalog() -> list[dict]:
    return [
        {
            "code": code,
            "name": info["name"],
            "price": info["price"],
            "description": info["description"],
            "features": info["features"],
            "limits": info["limits"],
        }
        for code, info in PLAN_CATALOG.items()
    ]


def plan_info(plan: str) -> dict:
    return PLAN_CATALOG.get(plan, PLAN_CATALOG[FREE])


def plan_price(plan: str) -> Decimal:
    return plan_info(plan)["price"]


def get_or_create_subscription(db: Session, org_id: UUID) -> Subscription:
    subscription = db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    ).scalar_one_or_none()
    if subscription is None:
        org = db.get(Organization, org_id)
        subscription = Subscription(organization_id=org_id, plan=org.plan)
        db.add(subscription)
        db.flush()
    return subscription


def count_usage(db: Session, org_id: UUID) -> dict:
    """Current usage counts for the organization."""
    user_count = db.execute(
        select(func.count(User.id)).where(
            User.organization_id == org_id,
            User.is_active.is_(True),
        )
    ).scalar_one()
    product_count = db.execute(
        select(func.count(Product.id)).where(
            Product.organization_id == org_id,
            Product.status.in_(["active", "draft"]),
        )
    ).scalar_one()
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    from app.models.order import Order

    orders_this_month = db.execute(
        select(func.count(Order.id)).where(
            Order.organization_id == org_id,
            Order.created_at >= month_start,
        )
    ).scalar_one()
    return {
        "users": user_count,
        "products": product_count,
        "orders_per_month": orders_this_month,
    }


def check_usage_limit(
    db: Session, org_id: UUID, resource: str, extra: int = 1
) -> None:
    """Raise 402 PLAN_LIMIT when the org is at/over its plan limit.

    ``None`` means unlimited. ``extra`` accounts for the record about to be
    created (default 1).
    """
    org = db.get(Organization, org_id)
    if org is None:
        return
    limit = plan_info(org.plan)["limits"].get(resource)
    if limit is None:
        return
    usage = count_usage(db, org_id)[resource]
    if usage + extra > limit:
        raise payment_required(
            "PLAN_LIMIT",
            f"You have reached the {resource.replace('_', ' ')} limit of your "
            f"{org.plan} plan ({limit}). Upgrade to raise the limit.",
            details={"resource": resource, "limit": limit, "usage": usage},
        )


def require_feature(db: Session, org_id: UUID, feature: str) -> None:
    """Raise 403 PLAN_FEATURE when the org's plan does not include a feature."""
    org = db.get(Organization, org_id)
    if org is None:
        return
    features = plan_info(org.plan)["features"]
    if feature not in features:
        raise forbidden(
            "PLAN_FEATURE",
            f"The {feature.replace('_', ' ')} feature requires the Pro plan.",
            details={"feature": feature, "plan": org.plan},
        )


def has_feature(db: Session, org_id: UUID, feature: str) -> bool:
    org = db.get(Organization, org_id)
    if org is None:
        return False
    return feature in plan_info(org.plan)["features"]


def _next_period() -> tuple[datetime, datetime]:
    start = datetime.now(UTC)
    end = start + timedelta(days=30)
    return start, end


def change_plan(
    db: Session,
    org_id: UUID,
    new_plan: str,
    *,
    actor_user_id: UUID,
) -> tuple[Organization, Subscription, Invoice]:
    """Switch the org plan, refresh the subscription and issue an invoice."""
    org = db.get(Organization, org_id)
    old_plan = org.plan

    subscription = get_or_create_subscription(db, org_id)
    start, end = _next_period()
    subscription.plan = new_plan
    subscription.status = "active"
    subscription.current_period_start = start
    subscription.current_period_end = end

    invoice = Invoice(
        organization_id=org_id,
        invoice_number=_invoice_number(db, org_id),
        plan=new_plan,
        amount=plan_price(new_plan),
        currency=org.currency or "USD",
        status="paid",
        period_start=start,
        period_end=end,
    )
    db.add(invoice)

    org.plan = new_plan
    log_action(
        db,
        organization_id=org_id,
        user_id=actor_user_id,
        action="organization.plan_changed",
        entity_type="organization",
        entity_id=org.id,
        meta={"from": old_plan, "to": new_plan, "invoice": str(invoice.id)},
    )
    db.commit()
    db.refresh(org)
    return org, subscription, invoice


def _invoice_number(db: Session, org_id: UUID) -> str:
    count = db.execute(
        select(func.count(Invoice.id)).where(Invoice.organization_id == org_id)
    ).scalar_one()
    return f"INV-{count + 1:05d}-{secrets.token_hex(2).upper()}"


def list_invoices(db: Session, org_id: UUID) -> list[Invoice]:
    return (
        db.execute(
            select(Invoice)
            .where(Invoice.organization_id == org_id)
            .order_by(Invoice.created_at.desc())
        )
        .scalars()
        .all()
    )
