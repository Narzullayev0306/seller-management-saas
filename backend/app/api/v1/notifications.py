from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import not_found
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import Page
from app.schemas.notification import (
    NotificationListParams,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationRead,
    UnreadCount,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_read(n: Notification) -> NotificationRead:
    return NotificationRead(
        id=n.id,
        type=n.type,
        title=n.title,
        message=n.message,
        data=n.data,
        read=n.read_at is not None,
        created_at=n.created_at,
    )


@router.get(
    "",
    response_model=Page[NotificationRead],
    summary="List notifications",
    description="Paginated list of the caller's in-app notifications.",
)
def list_notifications(
    params: NotificationListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("notifications.read")),
) -> Page[NotificationRead]:
    base = select(Notification).where(
        Notification.organization_id == user.effective_organization_id,
        Notification.user_id == user.id,
    )
    if params.unread_only:
        base = base.where(Notification.read_at.is_(None))
    total = db.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()
    rows = db.execute(
        base.order_by(Notification.created_at.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    ).scalars().all()
    return Page[NotificationRead](
        items=[_to_read(n) for n in rows],
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=(total + params.page_size - 1) // params.page_size,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCount,
    summary="Count unread notifications",
)
def unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("notifications.read")),
) -> UnreadCount:
    count = db.execute(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.organization_id == user.effective_organization_id,
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
    ).scalar_one()
    return UnreadCount(count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark a notification as read",
)
def mark_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("notifications.read")),
) -> NotificationRead:
    notification = db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.organization_id == user.effective_organization_id,
            Notification.user_id == user.id,
        )
    ).scalar_one_or_none()
    if notification is None:
        raise not_found("Notification")
    if notification.read_at is None:
        from datetime import UTC, datetime

        notification.read_at = datetime.now(UTC)
        db.commit()
    return _to_read(notification)


@router.patch(
    "/read-all",
    response_model=UnreadCount,
    summary="Mark all notifications as read",
)
def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("notifications.read")),
) -> UnreadCount:
    from datetime import UTC, datetime

    result = db.execute(
        select(Notification).where(
            Notification.organization_id == user.effective_organization_id,
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
    ).scalars()
    count = 0
    now = datetime.now(UTC)
    for n in result:
        n.read_at = now
        count += 1
    db.commit()
    return UnreadCount(count=count)


def _prefs_to_read(pref) -> NotificationPreferenceRead:
    return NotificationPreferenceRead(
        in_app_enabled=pref.in_app_enabled,
        email_enabled=pref.email_enabled,
        new_order_alerts=pref.new_order_alerts,
        low_stock_alerts=pref.low_stock_alerts,
        marketing_emails=pref.marketing_emails,
    )


@router.get(
    "/preferences",
    response_model=NotificationPreferenceRead,
    summary="Get notification preferences",
    description="Reads the caller's notification preferences, creating defaults on first access.",
)
def get_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("notifications.read")),
) -> NotificationPreferenceRead:
    from app.services.notification_service import get_preferences as svc

    return _prefs_to_read(svc(db, user))


@router.put(
    "/preferences",
    response_model=NotificationPreferenceRead,
    summary="Update notification preferences",
    description="Partially updates the caller's notification preferences.",
)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("notifications.read")),
) -> NotificationPreferenceRead:
    from app.services.notification_service import update_preferences as svc

    pref = svc(db, user, payload.model_dump(exclude_unset=True))
    return _prefs_to_read(pref)
