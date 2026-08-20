from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryTreeNode, CategoryUpdate
from app.services import category_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "/tree",
    response_model=list[CategoryTreeNode],
    summary="Get the category tree (nested)",
)
def get_tree(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("products.read")),
) -> list[CategoryTreeNode]:
    return category_service.get_tree(db, user.effective_organization_id)


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="List categories (flat, active only)",
)
def list_categories(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("products.read")),
) -> list[CategoryRead]:
    categories = category_service.list_categories(
        db, user.effective_organization_id, include_inactive=include_inactive
    )
    counts = category_service._counts(db, user.effective_organization_id)
    return [category_service._to_read(c, counts) for c in categories]


@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    summary="Create a category",
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.create")),
) -> CategoryRead:
    category = category_service.create_category(
        db, actor.effective_organization_id, payload
    )
    counts = category_service._counts(db, actor.effective_organization_id)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="category.created", entity_type="category", entity_id=category.id,
        meta={"name": category.name, "slug": category.slug},
    )
    db.commit()
    return category_service._to_read(category, counts)


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Get a category",
)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("products.read")),
) -> CategoryRead:
    category = category_service._get_category(
        db, user.effective_organization_id, category_id
    )
    counts = category_service._counts(db, user.effective_organization_id)
    return category_service._to_read(category, counts)


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update a category",
    description="Renaming a category also updates the denormalized category "
    "name on its products.",
)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.update")),
) -> CategoryRead:
    category = category_service.update_category(
        db, actor.effective_organization_id, category_id, payload
    )
    counts = category_service._counts(db, actor.effective_organization_id)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="category.updated", entity_type="category", entity_id=category.id,
        meta={"name": category.name, "slug": category.slug},
    )
    db.commit()
    return category_service._to_read(category, counts)


@router.delete(
    "/{category_id}",
    status_code=204,
    summary="Delete a category",
    description="Rejected while the category has children or products.",
)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.delete")),
) -> None:
    category_service.delete_category(db, actor.effective_organization_id, category_id)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="category.deleted", entity_type="category", entity_id=category_id,
        meta={"id": str(category_id)},
    )
    db.commit()
