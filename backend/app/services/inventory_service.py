from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApiError, not_found
from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.schemas.inventory import AdjustmentCreate
from app.services.audit_service import log_action


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def apply_adjustment(
        self,
        organization_id: UUID,
        payload: AdjustmentCreate,
        actor_user_id: UUID,
    ) -> Product:
        product = self.db.get(Product, payload.product_id)
        if product is None or product.organization_id != organization_id:
            raise not_found("Product")

        delta = payload.quantity if payload.type in ("purchase", "return") else -payload.quantity
        new_stock = product.stock_quantity + delta
        if new_stock < 0:
            raise ApiError(
                409,
                "INSUFFICIENT_STOCK",
                f"Cannot decrease stock below zero (current: {product.stock_quantity})",
            )
        if delta == 0:
            raise ApiError(422, "VALIDATION_ERROR", "Quantity must be non-zero")

        product.stock_quantity = new_stock
        self.db.add(
            InventoryMovement(
                organization_id=organization_id,
                product_id=product.id,
                type=payload.type,
                quantity=delta,
                reason=payload.reason,
            )
        )
        log_action(
            self.db,
            organization_id=organization_id,
            user_id=actor_user_id,
            action="inventory.adjusted",
            entity_type="product",
            entity_id=product.id,
            meta={"type": payload.type, "quantity": str(delta), "reason": payload.reason},
        )
        self.db.commit()
        self.db.refresh(product)
        return product
