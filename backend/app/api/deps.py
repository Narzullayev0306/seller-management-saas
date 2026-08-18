from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import forbidden, unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise unauthorized()
    payload = decode_access_token(credentials.credentials)
    user = db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == payload["sub"])
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise unauthorized("INVALID_TOKEN", "Invalid access token")

    claimed_org = payload.get("org")
    effective_org: UUID = user.organization_id
    if claimed_org is not None and UUID(str(claimed_org)) != user.organization_id:
        member = db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == UUID(str(claimed_org)),
                OrganizationMember.user_id == user.id,
                OrganizationMember.status == "active",
            )
        ).scalar_one_or_none()
        org = db.get(Organization, UUID(str(claimed_org)))
        if member is None or org is None or not org.is_active:
            raise unauthorized(
                "ORG_NOT_MEMBER",
                "You are not a member of the organization in this session",
            )
        effective_org = UUID(str(claimed_org))

    org = db.get(Organization, effective_org)
    if org is None or not org.is_active:
        raise unauthorized("ORG_INACTIVE", "This company is no longer active")

    user.effective_organization_id = effective_org
    return user


def require_owner(user: User = Depends(get_current_user)) -> User:
    if "owner" not in {r.code for r in user.roles}:
        raise forbidden("OWNER_ONLY", "Only the company owner can perform this action")
    return user


def require_permissions(*required: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        granted = {
            p.code for role in user.roles for p in role.permissions
        }
        missing = set(required) - granted
        if missing:
            raise forbidden(
                "PERMISSION_DENIED",
                f"Missing permission(s): {', '.join(sorted(missing))}",
            )
        return user

    return dependency
