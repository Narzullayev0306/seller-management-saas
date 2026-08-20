"""In-app notification helpers.

Notifications are written directly to the database (source of truth) and
displayed via the in-app bell; email delivery is optional and configured
separately in `email_service`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.role import role_permissions
from app.models.user import User

if TYPE_CHECKING:
    from app.models.notification_preference import NotificationPreference

if TYPE_CHECKING:
    from app.models.notification_preference import NotificationPreference


def notify(
    db: Session,
    *,
    organization_id: UUID,
    user_id: UUID,
    type: str,
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> Notification:
    notification = Notification(
        organization_id=organization_id,
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        data=data,
    )
    db.add(notification)
    db.flush()
    return notification


def users_with_permission(
    db: Session, organization_id: UUID, permission_code: str, exclude_user_id: UUID | None = None
) -> list[User]:
    """All active organization users whose roles grant a permission."""
    from app.models.role import Permission, Role

    stmt = (
        select(User)
        .join(User.roles)
        .join(role_permissions, role_permissions.c.role_id == Role.id)
        .join(Permission, Permission.id == role_permissions.c.permission_id)
        .where(
            User.organization_id == organization_id,
            User.is_active.is_(True),
            Permission.code == permission_code,
        )
    )
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    return list(db.execute(stmt).scalars().unique().all())


def notify_permission_holders(
    db: Session,
    *,
    organization_id: UUID,
    permission_code: str,
    exclude_user_id: UUID | None,
    type: str,
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> None:
    from app.models.notification_preference import NotificationPreference

    prefs = {
        p.user_id: p
        for p in db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id.in_(
                    select(User.id).where(User.organization_id == organization_id)
                )
            )
        ).scalars()
    }
    for user in users_with_permission(db, organization_id, permission_code, exclude_user_id):
        pref = prefs.get(user.id)
        if pref is not None and not pref.in_app_enabled:
            continue
        if pref is not None and type in ("new_order", "order_cancelled") and not pref.new_order_alerts:
            continue
        if pref is not None and type == "low_stock" and not pref.low_stock_alerts:
            continue
        notify(
            db,
            organization_id=organization_id,
            user_id=user.id,
            type=type,
            title=title,
            message=message,
            data=data,
        )


def has_unread_for_product(
    db: Session, organization_id: UUID, product_id: UUID
) -> bool:
    """True when an unread low-stock notification already exists for a product."""
    rows = db.execute(
        select(Notification).where(
            Notification.organization_id == organization_id,
            Notification.type == "low_stock",
            Notification.read_at.is_(None),
        ).limit(100)
    ).scalars()
    pid = str(product_id)
    return any((n.data or {}).get("product_id") == pid for n in rows)


def notify_low_stock(db: Session, organization_id: UUID, product_id: UUID) -> None:
    """Notify stock managers when a product is at or below its low-stock threshold.

    De-duplicated: a product only triggers once while its alert is unread.
    """
    from app.models.product import Product

    if has_unread_for_product(db, organization_id, product_id):
        return
    product = db.get(Product, product_id)
    if product is None or product.stock_quantity > product.low_stock_threshold:
        return
    notify_permission_holders(
        db,
        organization_id=organization_id,
        permission_code="inventory.read",
        exclude_user_id=None,
        type="low_stock",
        title=f'"{product.name}" is running low',
        message=f"Only {product.stock_quantity} unit(s) remaining (threshold: {product.low_stock_threshold}).",
        data={"product_id": str(product.id), "sku": product.sku},
    )


def notify_new_order(db: Session, organization_id: UUID, order_number: str, order_id: UUID, actor_user_id: UUID | None) -> None:
    notify_permission_holders(
        db,
        organization_id=organization_id,
        permission_code="orders.read",
        exclude_user_id=actor_user_id,
        type="new_order",
        title="New order received",
        message=f"Order {order_number} has been placed.",
        data={"order_id": str(order_id), "order_number": order_number},
    )


def notify_order_cancelled(db: Session, organization_id: UUID, order_number: str, order_id: UUID, actor_user_id: UUID | None) -> None:
    notify_permission_holders(
        db,
        organization_id=organization_id,
        permission_code="orders.read",
        exclude_user_id=actor_user_id,
        type="order_cancelled",
        title="Order cancelled",
        message=f"Order {order_number} was cancelled.",
        data={"order_id": str(order_id), "order_number": order_number},
    )


def notify_team_invited(
    db: Session, organization_id: UUID, actor_user_id: UUID, email: str, role_names: list[str]
) -> None:
    notify_permission_holders(
        db,
        organization_id=organization_id,
        permission_code="users.read",
        exclude_user_id=actor_user_id,
        type="team_invitation",
        title="Team member invited",
        message=f"{email} was invited as {', '.join(role_names)}.",
        data={"email": email, "roles": role_names},
    )


def notify_team_owner_transferred(
    db: Session, organization_id: UUID, actor_user_id: UUID, new_owner_email: str
) -> None:
    notify_permission_holders(
        db,
        organization_id=organization_id,
        permission_code="users.read",
        exclude_user_id=actor_user_id,
        type="ownership_transferred",
        title="Ownership transferred",
        message=f"Ownership was transferred to {new_owner_email}.",
        data={"new_owner": new_owner_email},
    )


def get_preferences(db: Session, user: User) -> NotificationPreference:
    """Return the user's notification preferences, creating defaults if needed."""
    from app.models.notification_preference import NotificationPreference

    pref = db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user.id
        )
    ).scalar_one_or_none()
    if pref is None:
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)
        db.flush()
    return pref


def update_preferences(db: Session, user: User, values: dict) -> NotificationPreference:
    """Apply partial updates to the user's notification preferences."""
    pref = get_preferences(db, user)
    for field, value in values.items():
        if value is not None and hasattr(pref, field):
            setattr(pref, field, value)
    db.commit()
    db.refresh(pref)
    return pref
