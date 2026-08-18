from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product


class InventoryMovement(TimestampMixin, Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        Index(
            "ix_inventory_movements_org_product_created",
            "organization_id",
            "product_id",
            "created_at",
        ),
        CheckConstraint("quantity != 0", name="ck_inventory_movements_quantity_non_zero"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_id: Mapped[UUID | None] = mapped_column(nullable=True)

    product: Mapped[Product] = relationship(back_populates="movements")
