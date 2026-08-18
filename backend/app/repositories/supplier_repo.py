from __future__ import annotations

from app.models.supplier import Supplier
from app.repositories.base import OrgRepository, parse_sort_params

SUPPLIER_SORTS = {
    "name": Supplier.name,
    "email": Supplier.email,
    "status": Supplier.status,
    "created_at": Supplier.created_at,
}


class SupplierRepository(OrgRepository[Supplier]):
    model = Supplier

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
        sort_by, sort_order = parse_sort_params(sort_by, sort_order, SUPPLIER_SORTS)
        filters = []
        if status:
            filters.append(Supplier.status == status)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sorts=SUPPLIER_SORTS,
            search=search,
            search_fields=[Supplier.name, Supplier.email, Supplier.phone],
            filters=filters,
        )
