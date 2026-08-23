from __future__ import annotations

import secrets
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import bad_request, conflict, forbidden, not_found, unauthorized
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenPair
from app.services import email_service
from app.services.audit_service import log_action
from app.services.auth_token_service import (
    consume_auth_token,
    create_auth_token,
    invalidate_user_tokens,
)
from app.services.permissions import RoleCode
from app.services.rbac_service import seed_organization_roles, user_permissions

MISSING_CREDENTIALS = unauthorized(
    "INVALID_CREDENTIALS", "Incorrect email or password"
)


def _enqueue_email(
    background_tasks: BackgroundTasks | None, task: Callable[[], bool]
) -> None:
    if background_tasks is not None:
        background_tasks.add_task(task)
    else:
        task()


def _issue_tokens(
    db: Session, user: User, organization_id: UUID | None = None
) -> TokenPair:
    access_token = create_access_token(
        user.id, organization_id or user.organization_id
    )
    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=refresh_token_expiry(),
        )
    )
    db.flush()
    return TokenPair(access_token=access_token, refresh_token=raw_refresh)


def register(
    db: Session,
    payload: RegisterRequest,
    background_tasks: BackgroundTasks | None = None,
) -> tuple[User, TokenPair]:
    existing = db.execute(
        select(User).where(User.email == payload.email.lower())
    ).scalar_one_or_none()
    if existing:
        raise conflict("EMAIL_TAKEN", "An account with this email already exists")

    org_name, org_slug = _unique_org_name_and_slug(
        db, payload.organization_name, payload.email
    )
    org = Organization(
        name=org_name,
        slug=org_slug,
    )
    db.add(org)
    db.flush()

    seed_organization_roles(db, org.id)

    user = User(
        organization_id=org.id,
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    owner_role = db.execute(
        select(Role).where(
            Role.organization_id == org.id, Role.code == RoleCode.OWNER
        )
    ).scalar_one()
    user.roles.append(owner_role)
    db.add(OrganizationMember(organization_id=org.id, user_id=user.id))
    db.flush()

    verification_token = create_auth_token(db, user.id, "verify_email")
    _enqueue_email(
        background_tasks,
        lambda: email_service.send_verification_email(user.email, verification_token),
    )

    tokens = _issue_tokens(db, user)
    log_action(
        db,
        organization_id=org.id,
        user_id=user.id,
        action="auth.register",
        meta={"email": user.email},
    )
    db.commit()
    db.refresh(user)
    return user, tokens


def login(db: Session, email: str, password: str) -> tuple[User, TokenPair]:
    user = db.execute(
        select(User).options(selectinload(User.roles)).where(User.email == email.lower())
    ).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise MISSING_CREDENTIALS
    if not user.is_active:
        raise forbidden("ACCOUNT_DISABLED", "This account has been disabled")
    if not user.organization.is_active:
        raise forbidden("ORGANIZATION_DISABLED", "Your organization is disabled")

    tokens = _issue_tokens(db, user)
    log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="auth.login",
        meta={"email": user.email},
    )
    db.commit()
    return user, tokens


def refresh(db: Session, raw_refresh: str) -> TokenPair:
    token_hash = hash_refresh_token(raw_refresh)
    token = db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user).selectinload(User.roles))
        .where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if token is None:
        raise unauthorized("INVALID_REFRESH_TOKEN", "Invalid refresh token")

    now = datetime.now(UTC)
    if token.revoked_at is not None:
        raise unauthorized("REFRESH_TOKEN_REVOKED", "Refresh token has been revoked")
    if token.expires_at < now:
        raise unauthorized("REFRESH_TOKEN_EXPIRED", "Refresh token has expired")
    if not token.user.is_active:
        raise forbidden("ACCOUNT_DISABLED", "This account has been disabled")

    token.revoked_at = now
    db.flush()
    new_tokens = _issue_tokens(db, token.user)
    db.commit()
    return new_tokens


def logout(db: Session, raw_refresh: str) -> None:
    token_hash = hash_refresh_token(raw_refresh)
    token = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if token is not None:
        token.revoked_at = datetime.now(UTC)
        log_action(
            db,
            organization_id=token.user.organization_id,
            user_id=token.user_id,
            action="auth.logout",
        )
        db.commit()


def current_user_payload(db: Session, user: User) -> dict:
    effective_org_id = (
        getattr(user, "effective_organization_id", None) or user.organization_id
    )
    roles = getattr(user, "effective_roles", None)
    if roles is None:
        roles = list(user.roles)
    org = db.get(Organization, effective_org_id)
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "organization_id": str(effective_org_id),
        "organization_name": org.name if org else user.organization.name,
        "organization_slug": org.slug if org else None,
        "email_verified": user.email_verified,
        "status": user.status,
        "roles": [
            {"code": r.code, "name": r.name} for r in roles
        ],
        "permissions": user_permissions(db, user),
    }


def switch_org(db: Session, user: User, target_org_id: UUID) -> TokenPair:
    """Re-issue tokens scoped to another organization the user belongs to."""
    member = db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == target_org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == "active",
        )
    ).scalar_one_or_none()
    if member is None:
        raise forbidden(
            "NOT_A_MEMBER", "You are not a member of that organization"
        )
    org = db.get(Organization, target_org_id)
    if org is None or not org.is_active:
        raise forbidden("ORG_INACTIVE", "This company is no longer active")

    tokens = _issue_tokens(db, user, target_org_id)
    log_action(
        db,
        organization_id=target_org_id,
        user_id=user.id,
        action="auth.org_switched",
        meta={"to": org.name},
    )
    db.commit()
    return tokens


def list_memberships(db: Session, user: User) -> list[dict]:
    rows = db.execute(
        select(Organization, OrganizationMember.status)
        .join(
            OrganizationMember,
            OrganizationMember.organization_id == Organization.id,
        )
        .where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == "active",
        )
        .order_by(Organization.created_at)
    ).all()
    return [
        {
            "organization_id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "plan": org.plan,
            "is_active": org.is_active,
            "status": status,
        }
        for org, status in rows
    ]


def forgot_password(
    db: Session, email: str, background_tasks: BackgroundTasks | None = None
) -> None:
    """Issue a reset token. Always succeeds to avoid user enumeration."""
    user = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()
    if user is None:
        db.commit()
        return
    if not user.is_active:
        db.commit()
        return
    invalidate_user_tokens(db, user.id, "reset_password")
    token = create_auth_token(db, user.id, "reset_password")
    _enqueue_email(
        background_tasks,
        lambda: email_service.send_reset_password_email(user.email, token),
    )
    log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="auth.password_reset_requested",
    )
    db.commit()


def reset_password(db: Session, token: str, new_password: str) -> None:
    user = consume_auth_token(db, token, "reset_password")
    user.password_hash = hash_password(new_password)
    invalidate_user_tokens(db, user.id, "reset_password")
    for rt in db.scalars(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    ):
        rt.revoked_at = datetime.now(UTC)
    log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="auth.password_reset",
    )
    db.commit()


def change_password(
    db: Session, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise bad_request("INVALID_PASSWORD", "Current password is incorrect")
    if current_password == new_password:
        raise bad_request(
            "SAME_PASSWORD", "New password must be different from current password"
        )
    user.password_hash = hash_password(new_password)
    log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="auth.password_changed",
    )
    db.commit()


def verify_email(db: Session, token: str) -> None:
    user = consume_auth_token(db, token, "verify_email")
    user.email_verified = True
    log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="auth.email_verified",
    )
    db.commit()


def resend_verification(
    db: Session, email: str, background_tasks: BackgroundTasks | None = None
) -> None:
    """Re-issue the verification token for a registered, unverified account."""
    user = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()
    if user is None or user.email_verified or not user.is_active:
        db.commit()
        return
    token = create_auth_token(db, user.id, "verify_email")
    _enqueue_email(
        background_tasks,
        lambda: email_service.send_verification_email(user.email, token),
    )
    db.commit()


def invite_user(
    db: Session,
    organization_id: UUID,
    *,
    email: str,
    full_name: str,
    role_codes: list[str],
    actor_user_id: UUID,
    background_tasks: BackgroundTasks | None = None,
) -> User:
    """Create a user in 'invited' state and email them an accept link."""
    from app.models.role import Role

    existing = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()
    if existing:
        raise conflict(
            "EMAIL_TAKEN", "A user with this email already exists"
        )

    role_codes_set = set(role_codes)
    roles = list(
        db.execute(
            select(Role).where(
                Role.organization_id == organization_id,
                Role.code.in_(role_codes_set),
            )
        ).scalars()
    )
    if len(roles) != len(role_codes_set):
        raise bad_request("INVALID_ROLE", "One or more roles do not exist")

    user = User(
        organization_id=organization_id,
        email=email.lower(),
        full_name=full_name or email.split("@")[0],
        password_hash=hash_password(secrets.token_urlsafe(24)),
        status="invited",
    )
    user.roles = roles
    db.add(user)
    db.flush()
    db.add(OrganizationMember(organization_id=organization_id, user_id=user.id))

    token = create_auth_token(db, user.id, "invite")
    role_names = [r.name for r in roles]
    org = db.get(Organization, organization_id)
    _enqueue_email(
        background_tasks,
        lambda: email_service.send_invite_email(user.email, token, org.name, role_names),
    )
    log_action(
        db,
        organization_id=organization_id,
        user_id=actor_user_id,
        action="user.invited",
        entity_type="user",
        entity_id=user.id,
        meta={"email": user.email, "roles": role_codes},
    )
    db.commit()
    return user


def accept_invite(db: Session, token: str, full_name: str, password: str) -> None:
    user = consume_auth_token(db, token, "invite")
    user.full_name = full_name
    user.password_hash = hash_password(password)
    user.status = "active"
    user.email_verified = True
    user.is_active = True
    log_action(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        action="user.invite_accepted",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()


def resend_invite(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    background_tasks: BackgroundTasks | None = None,
) -> User:
    """Re-issue an invite link for a user still in 'invited' status."""
    user = db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id, User.organization_id == organization_id)
    ).scalar_one_or_none()
    if user is None:
        raise not_found("User")
    if user.status != "invited":
        raise bad_request("NOT_INVITED", "This user is not in invited status")

    token = create_auth_token(db, user.id, "invite")
    org = db.get(Organization, organization_id)
    _enqueue_email(
        background_tasks,
        lambda: email_service.send_invite_email(
            user.email, token, org.name, [r.name for r in user.roles]
        ),
    )
    log_action(
        db,
        organization_id=organization_id,
        user_id=None,
        action="user.invite_resent",
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    return user


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    ).scalar_one_or_none()


def _slugify(name: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return (base or "org")[:100]


def _unique_org_name_and_slug(
    db: Session, base_name: str, email: str
) -> tuple[str, str]:
    clean_name = (base_name or "").strip()
    if not clean_name:
        clean_name = "Workspace"
    elif clean_name == "Customer Account":
        username = email.split("@")[0]
        clean_name = f"{username.capitalize()}'s Account"

    base_slug = "".join(c if c.isalnum() else "-" for c in clean_name.lower()).strip("-") or "org"
    base_slug = base_slug[:80]

    candidate_name = clean_name
    candidate_slug = base_slug
    counter = 1
    while True:
        exists = db.execute(
            select(Organization.id).where(
                (Organization.name == candidate_name) | (Organization.slug == candidate_slug)
            )
        ).scalar_one_or_none()
        if not exists:
            return candidate_name, candidate_slug
        counter += 1
        candidate_name = f"{clean_name} ({counter})"
        candidate_slug = f"{base_slug}-{counter}"
