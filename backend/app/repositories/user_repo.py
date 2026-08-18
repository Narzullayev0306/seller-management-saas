from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import not_found
from app.models.user import User
from app.repositories.base import OrgRepository


class UserRepository(OrgRepository[User]):
    model = User

    def get_with_roles(self, organization_id, entity_id: str) -> User:
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(
                User.organization_id == organization_id, User.id == entity_id
            )
        )
        user = self.db.execute(stmt).scalar_one_or_none()
        if user is None:
            raise not_found("User")
        return user

    def list_page(self, organization_id, *, page, page_size, search=None, status=None):
        search_fields = [User.full_name, User.email]
        filters = []
        if status:
            filters.append(User.status == status)
        return super().list_page(
            organization_id,
            page=page,
            page_size=page_size,
            sort_by="created_at",
            sort_order="desc",
            search=search,
            search_fields=search_fields,
            filters=filters,
        )
