"""Category tree management: create/update/delete/list with nested children."""

from __future__ import annotations

import re
import unicodedata
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryRead, CategoryTreeNode, CategoryUpdate

_SLUG_UNSAFE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    value = unicodedata.normalize("NFKD", name)
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = _SLUG_UNSAFE.sub("-", value).strip("-")
    return value or "category"


def unique_slug(db: Session, org_id: UUID, base: str, exclude_id: UUID | None = None) -> str:
    candidate = base
    n = 2
    while True:
        stmt = select(Category.id).where(
            Category.organization_id == org_id, Category.slug == candidate
        )
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        if db.execute(stmt).scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def _get_category(db: Session, org_id: UUID, category_id: UUID) -> Category:
    category = db.execute(
        select(Category).where(
            Category.organization_id == org_id, Category.id == category_id
        )
    ).scalar_one_or_none()
    if category is None:
        raise not_found("Category")
    return category


def _ensure_parent(db: Session, org_id: UUID, parent_id: UUID | None) -> None:
    if parent_id is None:
        return
    _get_category(db, org_id, parent_id)


def _sync_product_names(db: Session, org_id: UUID, category_id: UUID, name: str) -> None:
    db.execute(
        Product.__table__.update()
        .where(Product.organization_id == org_id, Product.category_id == category_id)
        .values(category=name)
    )


def create_category(db: Session, org_id: UUID, payload: CategoryCreate) -> Category:
    _ensure_parent(db, org_id, payload.parent_id)
    slug = unique_slug(db, org_id, payload.slug or slugify(payload.name))
    category = Category(
        organization_id=org_id,
        name=payload.name.strip(),
        slug=slug,
        parent_id=payload.parent_id,
        description=payload.description,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(category)
    db.commit()
    return category


def update_category(
    db: Session, org_id: UUID, category_id: UUID, payload: CategoryUpdate
) -> Category:
    category = _get_category(db, org_id, category_id)
    if payload.parent_id is not None and payload.parent_id != category.parent_id:
        if payload.parent_id == category.id:
            raise bad_request("CATEGORY_SELF_PARENT", "A category cannot be its own parent")
        parent = _get_category(db, org_id, payload.parent_id)
        node = parent
        while node is not None:
            if node.id == category.id:
                raise bad_request(
                    "CATEGORY_CYCLE", "Cannot move a category under one of its descendants"
                )
            node = node.parent
        category.parent_id = payload.parent_id
    if payload.name is not None and payload.name.strip() != category.name:
        category.name = payload.name.strip()
        _sync_product_names(db, org_id, category.id, category.name)
    if payload.slug is not None and payload.slug != category.slug:
        category.slug = unique_slug(db, org_id, payload.slug, exclude_id=category.id)
    if payload.description is not None:
        category.description = payload.description
    if payload.sort_order is not None:
        category.sort_order = payload.sort_order
    if payload.is_active is not None:
        category.is_active = payload.is_active
    db.commit()
    return category


def delete_category(db: Session, org_id: UUID, category_id: UUID) -> None:
    category = _get_category(db, org_id, category_id)
    child_count = db.execute(
        select(func.count(Category.id)).where(Category.parent_id == category.id)
    ).scalar_one()
    if child_count:
        raise bad_request(
            "CATEGORY_HAS_CHILDREN", "Move or delete child categories first"
        )
    product_count = db.execute(
        select(func.count(Product.id)).where(
            Product.organization_id == org_id, Product.category_id == category.id
        )
    ).scalar_one()
    if product_count:
        raise bad_request(
            "CATEGORY_HAS_PRODUCTS", "Reassign products out of this category first"
        )
    db.delete(category)
    db.commit()


def _counts(db: Session, org_id: UUID) -> dict[UUID, int]:
    rows = db.execute(
        select(Product.category_id, func.count(Product.id))
        .where(Product.organization_id == org_id, Product.category_id.is_not(None))
        .group_by(Product.category_id)
    ).all()
    return {cid: int(count) for cid, count in rows}


def _to_read(category: Category, counts: dict[UUID, int]) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        description=category.description,
        sort_order=category.sort_order,
        is_active=category.is_active,
        product_count=counts.get(category.id, 0),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def list_categories(db: Session, org_id: UUID, include_inactive: bool = False) -> list[Category]:
    stmt = select(Category).where(Category.organization_id == org_id)
    if not include_inactive:
        stmt = stmt.where(Category.is_active.is_(True))
    return list(db.execute(stmt.order_by(Category.sort_order, Category.name)).scalars())


def build_tree(
    db: Session, org_id: UUID, include_inactive: bool = False
) -> list[CategoryTreeNode]:
    categories = list_categories(db, org_id, include_inactive=include_inactive)
    counts = _counts(db, org_id)
    by_id: dict[UUID, CategoryTreeNode] = {}
    for c in categories:
        by_id[c.id] = CategoryTreeNode(
            **_to_read(c, counts).model_dump(), children=[]
        )
    roots: list[CategoryTreeNode] = []
    for c in categories:
        node = by_id[c.id]
        if c.parent_id is not None and c.parent_id in by_id:
            by_id[c.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


def get_tree(db: Session, org_id: UUID) -> list[CategoryTreeNode]:
    return build_tree(db, org_id, include_inactive=False)
