from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationPreference(Base):
    """Per-user notification preferences.

    Global across organizations for the user (kept simple on purpose); the
    notification fan-out consults these before creating in-app rows.
    """

    __tablename__ = "notification_preferences"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    in_app_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    email_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    new_order_alerts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    low_stock_alerts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    marketing_emails: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="notification_preference")
