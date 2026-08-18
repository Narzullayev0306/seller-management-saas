from __future__ import annotations

from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError, not_found
from app.schemas.common import Page, build_page

T = TypeVar("T")


class OrgRepository[T]:
    """Organization-scoped data access.

    Every query is forced to filter by organization_id, which makes
    cross-tenant access structurally impossible.
    """

    model: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---- core -----------------------------------------------------------

    def base_query(self, organization_id: UUID) -> Select[tuple[T]]:
        return select(self.model).where(
            self.model.organization_id == organization_id
        )

    def get(self, organization_id: UUID, entity_id: UUID, raise_if_missing: bool = True) -> T | None:
        stmt = self.base_query(organization_id).where(self.model.id == entity_id)
        obj = self.db.execute(stmt).scalar_one_or_none()
        if obj is None and raise_if_missing:
            raise not_found(self.model.__name__)
        return obj

    def count(self, organization_id: UUID) -> int:
        stmt = select(func.count()).select_from(self.model).where(
            self.model.organization_id == organization_id
        )
        return int(self.db.execute(stmt).scalar_one())

    def create(self, organization_id: UUID, **values: Any) -> T:
        obj = self.model(organization_id=organization_id, **values)
        self.db.add(obj)
        self.db.flush()
        return obj

    # ---- list helpers ---------------------------------------------------

    def list_page(
        self,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        sort_by: str | None = None,
        sort_order: str = "desc",
        allowed_sorts: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[Any] | None = None,
        filters: list[Any] | None = None,
        model: type | None = None,
    ) -> Page[T]:
        target = model or self.model
        stmt = select(target).where(target.organization_id == organization_id)
        if search and search_fields:
            stmt = stmt.where(
                or_(
                    *[field.ilike(f"%{search}%") for field in search_fields]
                )
            )
        for cond in filters or []:
            stmt = stmt.where(cond)
        total = int(self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one())

        if sort_by and allowed_sorts and sort_by in allowed_sorts:
            column = allowed_sorts[sort_by]
            stmt = stmt.order_by(
                column.desc() if sort_order == "desc" else column.asc()
            )
        items = list(self.db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars())
        return build_page(items, page, page_size, total)


def parse_sort_params(
    sort_by: str | None, sort_order: str | None, allowed: dict[str, Any]
) -> tuple[str | None, str]:
    order = sort_order or "desc"
    if order not in ("asc", "desc"):
        raise ApiError(422, "VALIDATION_ERROR", "sort_order must be 'asc' or 'desc'")
    if sort_by is not None and sort_by not in allowed:
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            f"sort_by must be one of: {', '.join(allowed)}",
        )
    return sort_by, order
