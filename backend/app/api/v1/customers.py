from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import bad_request
from app.db.session import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.models.user import User
from app.repositories.customer_repo import CustomerRepository
from app.schemas.common import Page
from app.schemas.customer import (
    CustomerCreate,
    CustomerListParams,
    CustomerRead,
    CustomerUpdate,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/customers", tags=["customers"])


def _to_read(customer: Customer) -> CustomerRead:
    return CustomerRead(
        id=customer.id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        total_orders=customer.total_orders,
        total_spent=customer.total_spent,
        created_at=customer.created_at,
    )


@router.get(
    "",
    response_model=Page[CustomerRead],
    summary="List customers",
    description="Paginated, searchable list with sorting.",
)
def list_customers(
    params: CustomerListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("customers.read")),
) -> Page[CustomerRead]:
    repo = CustomerRepository(db)
    page = repo.list_page(
        user.effective_organization_id,
        page=params.page, page_size=params.page_size,
        search=params.search, sort_by=params.sort_by, sort_order=params.sort_order,
    )
    return Page[CustomerRead](
        items=[_to_read(c) for c in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.post(
    "", response_model=CustomerRead, status_code=201, summary="Create a customer"
)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("customers.create")),
) -> CustomerRead:
    repo = CustomerRepository(db)
    if payload.email:
        existing = db.execute(
            select(Customer).where(
                Customer.organization_id == actor.effective_organization_id,
                Customer.email == payload.email.lower(),
            )
        ).scalar_one_or_none()
        if existing:
            raise bad_request("EMAIL_TAKEN", "A customer with this email already exists")
    customer = repo.create(
        actor.effective_organization_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower() if payload.email else None,
        phone=payload.phone,
        address=payload.address,
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="customer.created", entity_type="customer", entity_id=customer.id,
        meta={"email": customer.email},
    )
    db.commit()
    return _to_read(customer)


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Get a customer",
    description="Customer profile. Use /orders?customer_id= for order history.",
)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("customers.read")),
) -> CustomerRead:
    customer = CustomerRepository(db).get(user.effective_organization_id, customer_id)
    return _to_read(customer)


@router.patch("/{customer_id}", response_model=CustomerRead, summary="Update a customer")
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("customers.update")),
) -> CustomerRead:
    repo = CustomerRepository(db)
    customer = repo.get(actor.effective_organization_id, customer_id)
    data = payload.model_dump(exclude_none=True)
    if "email" in data:
        data["email"] = data["email"].lower()
    for field, value in data.items():
        setattr(customer, field, value)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="customer.updated", entity_type="customer", entity_id=customer.id,
        meta=data,
    )
    db.commit()
    return _to_read(customer)


@router.delete(
    "/{customer_id}",
    status_code=204,
    summary="Delete a customer",
    description="Hard delete. Fails with 409 if the customer has orders.",
)
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("customers.delete")),
) -> None:
    repo = CustomerRepository(db)
    customer = repo.get(actor.effective_organization_id, customer_id)
    has_orders = db.execute(
        select(Order.id).where(
            Order.organization_id == actor.effective_organization_id,
            Order.customer_id == customer.id,
        ).limit(1)
    ).scalar_one_or_none()
    if has_orders:
        raise bad_request(
            "CUSTOMER_HAS_ORDERS", "This customer has orders and cannot be deleted"
        )
    db.delete(customer)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="customer.deleted", entity_type="customer", entity_id=customer.id,
    )
    db.commit()
