from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import bad_request
from app.db.session import get_db
from app.models.supplier import Supplier
from app.models.user import User
from app.repositories.supplier_repo import SupplierRepository
from app.schemas.common import Page
from app.schemas.supplier import (
    SupplierCreate,
    SupplierListParams,
    SupplierRead,
    SupplierUpdate,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _to_read(supplier: Supplier) -> SupplierRead:
    return SupplierRead(
        id=supplier.id,
        name=supplier.name,
        email=supplier.email,
        phone=supplier.phone,
        address=supplier.address,
        status=supplier.status,
        created_at=supplier.created_at,
    )


@router.get(
    "",
    response_model=Page[SupplierRead],
    summary="List suppliers",
    description="Paginated, searchable list with status filter and sorting.",
)
def list_suppliers(
    params: SupplierListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("suppliers.read")),
) -> Page[SupplierRead]:
    repo = SupplierRepository(db)
    page = repo.list_page(
        user.effective_organization_id,
        page=params.page, page_size=params.page_size,
        search=params.search, status=params.status,
        sort_by=params.sort_by, sort_order=params.sort_order,
    )
    return Page[SupplierRead](
        items=[_to_read(s) for s in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.post(
    "",
    response_model=SupplierRead,
    status_code=201,
    summary="Create a supplier",
)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("suppliers.create")),
) -> SupplierRead:
    if payload.email:
        existing = db.execute(
            select(Supplier).where(
                Supplier.organization_id == actor.effective_organization_id,
                Supplier.email == payload.email.lower(),
            )
        ).scalar_one_or_none()
        if existing:
            raise bad_request("EMAIL_TAKEN", "A supplier with this email already exists")
    supplier = SupplierRepository(db).create(
        actor.effective_organization_id,
        name=payload.name,
        email=payload.email.lower() if payload.email else None,
        phone=payload.phone,
        address=payload.address,
        status=payload.status,
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="supplier.created", entity_type="supplier", entity_id=supplier.id,
        meta={"name": supplier.name},
    )
    db.commit()
    return _to_read(supplier)


@router.get("/{supplier_id}", response_model=SupplierRead, summary="Get a supplier")
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("suppliers.read")),
) -> SupplierRead:
    return _to_read(SupplierRepository(db).get(user.effective_organization_id, supplier_id))


@router.patch(
    "/{supplier_id}", response_model=SupplierRead, summary="Update a supplier"
)
def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("suppliers.update")),
) -> SupplierRead:
    repo = SupplierRepository(db)
    supplier = repo.get(actor.effective_organization_id, supplier_id)
    data = payload.model_dump(exclude_none=True)
    if "email" in data:
        data["email"] = data["email"].lower()
    for field, value in data.items():
        setattr(supplier, field, value)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="supplier.updated", entity_type="supplier", entity_id=supplier.id,
        meta=data,
    )
    db.commit()
    return _to_read(supplier)


@router.delete(
    "/{supplier_id}",
    status_code=204,
    summary="Delete a supplier",
)
def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("suppliers.delete")),
) -> None:
    repo = SupplierRepository(db)
    supplier = repo.get(actor.effective_organization_id, supplier_id)
    db.delete(supplier)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="supplier.deleted", entity_type="supplier", entity_id=supplier.id,
    )
    db.commit()
