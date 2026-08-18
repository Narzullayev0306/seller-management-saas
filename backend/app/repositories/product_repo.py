from __future__ import annotations

from app.models.product import Product
from app.repositories.base import OrgRepository, parse_sort_params

PRODUCT_SORTS = {
    "name": Product.name,
    "sku": Product.sku,
    "category": Product.category,
    "price": Product.price,
    "stock_quantity": Product.stock_quantity,
    "status": Product.status,
    "created_at": Product.created_at,
}


class ProductRepository(OrgRepository[Product]):
    model = Product

    def list_page(
        self,
        organization_id,
        *,
        page,
        page_size,
        search=None,
        category=None,
        status=None,
        stock_status=None,
        sort_by=None,
        sort_order=None,
    ):
        sort_by, sort_order = parse_sort_params(sort_by, sort_order, PRODUCT_SORTS)
        filters = []
        if category:
            filters.append(Product.category == category)
        if status:
            filters.append(Product.status == status)
        if stock_status == "low_stock":
            filters.append(
                (Product.stock_quantity > 0)
                & (Product.stock_quantity <= Product.low_stock_threshold)
            )
        elif stock_status == "out_of_stock":
            filters.append(Product.stock_quantity <= 0)
        elif stock_status == "in_stock":
            filters.append(Product.stock_quantity > Product.low_stock_threshold)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sorts=PRODUCT_SORTS,
            search=search,
            search_fields=[Product.name, Product.sku],
            filters=filters,
        )

    def categories(self, organization_id) -> list[str]:
        rows = self.db.execute(
            self.base_query(organization_id)
            .with_only_columns(Product.category)
            .distinct()
            .order_by(Product.category)
        ).all()
        return [row[0] for row in rows if row[0]]
