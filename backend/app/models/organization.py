from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.billing import Invoice, Subscription
    from app.models.category import Category
    from app.models.domain import OrganizationDomain
    from app.models.notification import Notification
    from app.models.organization_member import OrganizationMember
    from app.models.role import Role
    from app.models.shipping_method import ShippingMethod
    from app.models.supplier import Supplier
    from app.models.user import User
    from app.models.webhook import WebhookEndpoint
    from app.models.wishlist import Wishlist


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    storefront_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    users: Mapped[list[User]] = relationship(back_populates="organization")
    members: Mapped[list[OrganizationMember]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    roles: Mapped[list[Role]] = relationship(back_populates="organization")
    suppliers: Mapped[list[Supplier]] = relationship(back_populates="organization")
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    wishlists: Mapped[list[Wishlist]] = relationship(back_populates="organization")
    categories: Mapped[list[Category]] = relationship(back_populates="organization")
    shipping_methods: Mapped[list[ShippingMethod]] = relationship(
        back_populates="organization"
    )
    webhook_endpoints: Mapped[list[WebhookEndpoint]] = relationship(
        back_populates="organization"
    )
    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="organization")
    subscription: Mapped[Subscription | None] = relationship(
        back_populates="organization", uselist=False
    )
    invoices: Mapped[list[Invoice]] = relationship(back_populates="organization")
    domains: Mapped[list[OrganizationDomain]] = relationship(
        back_populates="organization"
    )
