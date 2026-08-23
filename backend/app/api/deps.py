from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ApiError, forbidden, unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.api_key import ApiKey
from app.models.customer_account import CustomerAccount
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role, user_roles
from app.models.user import User
from app.services.api_key_service import verify_api_key

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_customer(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CustomerAccount:
    """Resolve the storefront customer account from a customer-kind JWT."""
    if credentials is None:
        raise unauthorized()
    payload = decode_access_token(credentials.credentials)
    if payload.get("kind") != "customer":
        raise unauthorized("INVALID_TOKEN", "Invalid access token")
    account = db.execute(
        select(CustomerAccount).where(
            CustomerAccount.id == payload["sub"],
        )
    ).scalar_one_or_none()
    if account is None or not account.is_active:
        raise unauthorized("INVALID_TOKEN", "Invalid access token")
    org = db.get(Organization, account.organization_id)
    if org is None or not org.is_active:
        raise unauthorized("ORG_INACTIVE", "This company is no longer active")
    return account


def optional_current_customer(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CustomerAccount | None:
    """Like get_current_customer, but returns None for missing/invalid tokens."""
    if credentials is None:
        return None
    try:
        return get_current_customer(db, credentials)
    except ApiError:
        return None


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise unauthorized()
    payload = decode_access_token(credentials.credentials)
    if payload.get("kind", "user") != "user":
        raise unauthorized("INVALID_TOKEN", "Invalid access token")
    user = db.execute(
        select(User).where(User.id == payload["sub"])
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

    # Scope roles (and their permissions) to the effective organization only:
    # a user switching orgs must never inherit roles from another organization.
    # NOTE: stored on a separate attribute (not user.roles) so the ORM never
    # rewrites the user_roles association table on flush.
    roles = db.execute(
        select(Role)
        .join(user_roles, user_roles.c.role_id == Role.id)
        .options(selectinload(Role.permissions))
        .where(
            user_roles.c.user_id == user.id,
            Role.organization_id == effective_org,
        )
    ).scalars().all()
    user.effective_roles = list(roles)
    user.effective_organization_id = effective_org
    return user


def _scoped_roles(user: User) -> list[Role]:
    roles = getattr(user, "effective_roles", None)
    return roles if roles is not None else list(user.roles)


def require_owner(user: User = Depends(get_current_user)) -> User:
    if "owner" not in {r.code for r in _scoped_roles(user)}:
        raise forbidden("OWNER_ONLY", "Only the company owner can perform this action")
    return user


def require_permissions(*required: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        granted = {
            p.code for role in _scoped_roles(user) for p in role.permissions
        }
        missing = set(required) - granted
        if missing:
            raise forbidden(
                "PERMISSION_DENIED",
                f"Missing permission(s): {', '.join(sorted(missing))}",
            )
        return user

    return dependency


def require_api_key_scopes(*required: str):
    """Authenticate via `Authorization: Bearer smk_...` and enforce scopes.

    The returned ApiKey carries `effective_organization_id` so endpoints can
    scope queries exactly like user-based endpoints.
    """

    def dependency(
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> ApiKey:
        if credentials is None or not credentials.credentials.startswith("smk_"):
            raise unauthorized("API_KEY_REQUIRED", "An API key is required")
        key = verify_api_key(db, credentials.credentials)
        if key is None:
            raise unauthorized("INVALID_API_KEY", "Invalid or expired API key")
        granted = set(key.scopes)
        missing = set(required) - granted
        if missing:
            raise forbidden(
                "API_KEY_SCOPE_DENIED",
                f"API key is missing scope(s): {', '.join(sorted(missing))}",
            )
        key.effective_organization_id = key.organization_id
        return key

    return dependency
