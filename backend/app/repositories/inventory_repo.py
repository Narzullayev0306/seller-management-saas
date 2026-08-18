from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.inventory import InventoryMovement
from app.models.product import Product
from app.repositories.base import OrgRepository, parse_sort_params

MOVEMENT_SORTS = {
    "type": InventoryMovement.type,
    "quantity": InventoryMovement.quantity,
    "created_at": InventoryMovement.created_at,
}


class InventoryRepository(OrgRepository[InventoryMovement]):
    model = InventoryMovement

    def list_movements(
        self,
        organization_id,
        *,
        page,
        page_size,
        product_id=None,
        movement_type=None,
        sort_by=None,
        sort_order=None,
    ):
        sort_by, sort_order = parse_sort_params(sort_by, sort_order, MOVEMENT_SORTS)
        filters = []
        if product_id:
            filters.append(InventoryMovement.product_id == product_id)
        if movement_type:
            filters.append(InventoryMovement.type == movement_type)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sorts=MOVEMENT_SORTS,
            filters=filters,
        )

    def stock_overview(
        self,
        organization_id,
        *,
        page,
        page_size,
        search=None,
        stock_status=None,
        category=None,
        sort_by=None,
        sort_order=None,
    ):
        sort_by, sort_order = parse_sort_params(sort_by, sort_order, {
            "name": Product.name,
            "sku": Product.sku,
            "stock_quantity": Product.stock_quantity,
            "category": Product.category,
        })
        filters = []
        if stock_status == "low_stock":
            filters.append(
                (Product.stock_quantity > 0)
                & (Product.stock_quantity <= Product.low_stock_threshold)
            )
        elif stock_status == "out_of_stock":
            filters.append(Product.stock_quantity <= 0)
        if category:
            filters.append(Product.category == category)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sorts={
                "name": Product.name,
                "sku": Product.sku,
                "stock_quantity": Product.stock_quantity,
                "category": Product.category,
            },
            search=search,
            search_fields=[Product.name, Product.sku],
            filters=filters,
            model=Product,
        )


def get_product_stock(db, organization_id: UUID, product_id: UUID) -> Product | None:
    return db.execute(
        select(Product).where(
            Product.organization_id == organization_id, Product.id == product_id
        )
    ).scalar_one_or_none()
