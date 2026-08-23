from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer


class CustomerAccount(TimestampMixin, Base):
    """A storefront customer's login credentials, scoped to one organization.

    Every account is linked to a `customers` row so guest and registered
    shoppers share the same customer record for order history and totals.
    """

    __tablename__ = "customer_accounts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "email", name="uq_customer_accounts_org_email"
        ),
        UniqueConstraint("customer_id", name="uq_customer_accounts_customer"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="account")
    refresh_tokens: Mapped[list[CustomerRefreshToken]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class CustomerRefreshToken(Base):
    __tablename__ = "customer_refresh_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("customer_accounts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    account: Mapped[CustomerAccount] = relationship(back_populates="refresh_tokens")
