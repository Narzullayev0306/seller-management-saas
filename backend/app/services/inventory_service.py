from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError, not_found
from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.schemas.inventory import AdjustmentCreate
from app.services.audit_service import log_action
from app.services.outbox_service import emit


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def apply_adjustment(
        self,
        organization_id: UUID,
        payload: AdjustmentCreate,
        actor_user_id: UUID,
    ) -> Product:
        product = self.db.execute(
            select(Product)
            .where(
                Product.organization_id == organization_id,
                Product.id == payload.product_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if product is None:
            raise not_found("Product")

        delta = payload.quantity if payload.type in ("purchase", "return") else -payload.quantity
        old_stock = product.stock_quantity
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
        restocked = old_stock == 0 and new_stock > 0
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
        if restocked:
            emit(
                self.db,
                organization_id=organization_id,
                event_type="inventory.restocked",
                aggregate_type="product",
                aggregate_id=product.id,
            )
        if product.stock_quantity <= product.low_stock_threshold:
            emit(
                self.db,
                organization_id=organization_id,
                event_type="stock.low",
                aggregate_type="product",
                aggregate_id=product.id,
            )
        self.db.commit()
        self.db.refresh(product)
        return product
