from __future__ import annotations

from app.models.customer import Customer
from app.repositories.base import OrgRepository, parse_sort_params

CUSTOMER_SORTS = {
    "first_name": Customer.first_name,
    "last_name": Customer.last_name,
    "email": Customer.email,
    "phone": Customer.phone,
    "total_orders": Customer.total_orders,
    "total_spent": Customer.total_spent,
    "created_at": Customer.created_at,
}


class CustomerRepository(OrgRepository[Customer]):
    model = Customer

    def list_page(
        self,
        organization_id,
        *,
        page,
        page_size,
        search=None,
        sort_by=None,
        sort_order=None,
    ):
        sort_by, sort_order = parse_sort_params(sort_by, sort_order, CUSTOMER_SORTS)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sorts=CUSTOMER_SORTS,
            search=search,
            search_fields=[Customer.first_name, Customer.last_name, Customer.email],
        )
