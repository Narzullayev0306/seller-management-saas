from __future__ import annotations

from app.models.seller import Seller
from app.repositories.base import OrgRepository, parse_sort_params

SELLER_SORTS = {
    "first_name": Seller.first_name,
    "last_name": Seller.last_name,
    "email": Seller.email,
    "status": Seller.status,
    "commission_rate": Seller.commission_rate,
    "total_sales": Seller.total_sales,
    "total_orders": Seller.total_orders,
    "created_at": Seller.created_at,
}


class SellerRepository(OrgRepository[Seller]):
    model = Seller

    def list_page(
        self,
        organization_id,
        *,
        page,
        page_size,
        search=None,
        status=None,
        sort_by=None,
        sort_order=None,
    ):
        sort_by, sort_order = parse_sort_params(sort_by, sort_order, SELLER_SORTS)
        filters = []
        if status:
            filters.append(Seller.status == status)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sorts=SELLER_SORTS,
            search=search,
            search_fields=[Seller.first_name, Seller.last_name, Seller.email],
            filters=filters,
        )
