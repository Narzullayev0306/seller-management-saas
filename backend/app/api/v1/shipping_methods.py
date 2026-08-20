from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import bad_request, not_found
from app.db.session import get_db
from app.models.shipping_method import ShippingMethod
from app.models.user import User
from app.schemas.shipping_method import (
    ShippingMethodCreate,
    ShippingMethodRead,
    ShippingMethodUpdate,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/shipping-methods", tags=["shipping-methods"])


def _ensure_unique_name(
    db: Session, org_id: UUID, name: str, exclude_id: UUID | None = None
) -> None:
    stmt = select(ShippingMethod.id).where(
        ShippingMethod.organization_id == org_id, ShippingMethod.name == name
    )
    if exclude_id is not None:
        stmt = stmt.where(ShippingMethod.id != exclude_id)
    if db.execute(stmt).scalar_one_or_none() is not None:
        raise bad_request(
            "SHIPPING_METHOD_NAME_TAKEN", "A shipping method with this name already exists"
        )


@router.get(
    "",
    response_model=list[ShippingMethodRead],
    summary="List shipping methods",
)
def list_shipping_methods(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> list[ShippingMethodRead]:
    stmt = select(ShippingMethod).where(
        ShippingMethod.organization_id == user.effective_organization_id
    )
    if not include_inactive:
        stmt = stmt.where(ShippingMethod.is_active.is_(True))
    return list(
        db.execute(stmt.order_by(ShippingMethod.sort_order, ShippingMethod.name)).scalars()
    )


@router.post(
    "",
    response_model=ShippingMethodRead,
    status_code=201,
    summary="Create a shipping method",
)
def create_shipping_method(
    payload: ShippingMethodCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> ShippingMethodRead:
    _ensure_unique_name(db, actor.effective_organization_id, payload.name)
    method = ShippingMethod(
        organization_id=actor.effective_organization_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        min_order_amount=payload.min_order_amount,
        max_order_amount=payload.max_order_amount,
        estimated_delivery_days=payload.estimated_delivery_days,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )
    db.add(method)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="shipping_method.created", entity_type="shipping_method",
        entity_id=method.id, meta={"name": method.name, "price": str(method.price)},
    )
    db.commit()
    return ShippingMethodRead.model_validate(method)


@router.get(
    "/{method_id}",
    response_model=ShippingMethodRead,
    summary="Get a shipping method",
)
def get_shipping_method(
    method_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> ShippingMethodRead:
    method = db.execute(
        select(ShippingMethod).where(
            ShippingMethod.organization_id == user.effective_organization_id,
            ShippingMethod.id == method_id,
        )
    ).scalar_one_or_none()
    if method is None:
        raise not_found("ShippingMethod")
    return ShippingMethodRead.model_validate(method)


@router.patch(
    "/{method_id}",
    response_model=ShippingMethodRead,
    summary="Update a shipping method",
)
def update_shipping_method(
    method_id: UUID,
    payload: ShippingMethodUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> ShippingMethodRead:
    method = db.execute(
        select(ShippingMethod).where(
            ShippingMethod.organization_id == actor.effective_organization_id,
            ShippingMethod.id == method_id,
        )
    ).scalar_one_or_none()
    if method is None:
        raise not_found("ShippingMethod")
    data = payload.model_dump(exclude_none=True)
    if "name" in data:
        _ensure_unique_name(
            db, actor.effective_organization_id, data["name"], exclude_id=method.id
        )
    for field, value in data.items():
        setattr(method, field, value)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="shipping_method.updated", entity_type="shipping_method",
        entity_id=method.id, meta=data,
    )
    db.commit()
    return ShippingMethodRead.model_validate(method)


@router.delete(
    "/{method_id}",
    status_code=204,
    summary="Delete a shipping method",
)
def delete_shipping_method(
    method_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> None:
    method = db.execute(
        select(ShippingMethod).where(
            ShippingMethod.organization_id == actor.effective_organization_id,
            ShippingMethod.id == method_id,
        )
    ).scalar_one_or_none()
    if method is None:
        raise not_found("ShippingMethod")
    db.delete(method)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="shipping_method.deleted", entity_type="shipping_method",
        entity_id=method_id, meta={"id": str(method_id)},
    )
    db.commit()
