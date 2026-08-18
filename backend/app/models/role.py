from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    Column(
        "permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    ),
    UniqueConstraint("role_id", "permission_id"),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    UniqueConstraint("user_id", "role_id"),
)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=False, default="")

    roles: Mapped[list[Role]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    is_system: Mapped[bool] = mapped_column(default=True, nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="roles")
    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions, back_populates="roles", lazy="selectin"
    )
    users: Mapped[list[User]] = relationship(
        secondary=user_roles, back_populates="roles"
    )
