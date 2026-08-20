from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.core.exceptions import bad_request, not_found
from app.core.security import hash_password
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.common import Page
from app.schemas.user import (
    AcceptInvite,
    ResendInvite,
    UserCreate,
    UserInvite,
    UserListParams,
    UserRead,
    UserRolesUpdate,
    UserUpdate,
)
from app.services.audit_service import log_action
from app.services.auth_service import (
    accept_invite as auth_accept_invite,
)
from app.services.auth_service import get_user_by_id, invite_user, resend_invite
from app.services.notification_service import notify_team_invited
from app.services.rbac_service import user_role_codes

router = APIRouter(prefix="/users", tags=["users"])


def _to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        status=user.status,
        roles=[r.code for r in user.roles],
        created_at=user.created_at,
    )


@router.post(
    "/invite",
    response_model=UserRead,
    status_code=201,
    summary="Invite a team member by email",
    description="Creates a user in 'invited' status and emails an accept link. "
    "The invitee sets their own password when accepting.",
)
def invite_member(
    payload: UserInvite,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.create")),
) -> UserRead:
    user = invite_user(
        db,
        actor.effective_organization_id,
        email=payload.email,
        full_name=payload.full_name,
        role_codes=payload.role_codes,
        actor_user_id=actor.id,
        background_tasks=background_tasks,
    )
    notify_team_invited(
        db,
        actor.effective_organization_id,
        actor.id,
        user.email,
        [r.name for r in user.roles],
    )
    db.commit()
    return _to_read(get_user_by_id(db, user.id))


@router.post(
    "/invites/accept",
    status_code=200,
    summary="Accept a team invitation",
    description="Public endpoint: sets the invitee's name and password and "
    "activates the account.",
    responses={
        400: {"description": "Invalid, expired or already-used invite link"},
        422: {"description": "Weak password"},
    },
)
def accept_invitation(payload: AcceptInvite, db: Session = Depends(get_db)) -> dict:
    auth_accept_invite(db, payload.token, payload.full_name, payload.password)
    return {"message": "Welcome! You can now sign in."}


@router.post(
    "/invites/resend",
    response_model=UserRead,
    status_code=200,
    summary="Resend a team invitation",
    description="Re-issues the invite email for a user still in 'invited' status.",
    responses={400: {"description": "User is not in invited status"}},
)
def resend_invitation(
    payload: ResendInvite,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.create")),
) -> UserRead:
    user = resend_invite(
        db, actor.effective_organization_id, payload.user_id, background_tasks
    )
    notify_team_invited(
        db,
        actor.effective_organization_id,
        actor.id,
        user.email,
        [r.name for r in user.roles],
    )
    db.commit()
    return _to_read(user)


@router.get(
    "",
    response_model=Page[UserRead],
    summary="List users",
    description="Paginated, searchable list of organization users.",
)
def list_users(
    params: UserListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("users.read")),
) -> Page[UserRead]:
    repo = UserRepository(db)
    page = repo.list_page(
        user.effective_organization_id, page=params.page, page_size=params.page_size,
        search=params.search, status=params.status,
    )
    return Page[UserRead](
        items=[_to_read(u) for u in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.post(
    "",
    response_model=UserRead,
    status_code=201,
    summary="Create a user",
    description="Creates a user within the caller's organization and assigns roles.",
    responses={409: {"description": "Email already exists"}},
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.create")),
) -> UserRead:
    from app.services.billing_service import check_usage_limit

    check_usage_limit(db, actor.effective_organization_id, "users")
    existing = db.execute(
        select(User).where(User.email == payload.email.lower())
    ).scalar_one_or_none()
    if existing:
        raise bad_request("EMAIL_TAKEN", "A user with this email already exists")

    role_codes = set(payload.role_codes)
    roles = db.execute(
        select(Role).where(
            Role.organization_id == actor.effective_organization_id,
            Role.code.in_(role_codes),
        )
    ).scalars()
    roles = list(roles)
    if len(roles) != len(role_codes):
        raise bad_request("INVALID_ROLE", "One or more roles do not exist")

    user = User(
        organization_id=actor.effective_organization_id,
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    user.roles = roles
    db.add(user)
    db.flush()
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="user.created", entity_type="user", entity_id=user.id,
        meta={"email": user.email, "roles": payload.role_codes},
    )
    db.commit()
    return _to_read(get_user_by_id(db, user.id))


@router.get("/{user_id}", response_model=UserRead, summary="Get a user")
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("users.read")),
) -> UserRead:
    target = db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(user.effective_organization_id == user.effective_organization_id, User.id == user_id)
    ).scalar_one_or_none()
    if target is None:
        raise not_found("User")
    return _to_read(target)


@router.patch("/{user_id}", response_model=UserRead, summary="Update a user")
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.update")),
) -> UserRead:
    repo = UserRepository(db)
    target = repo.get_with_roles(actor.effective_organization_id, user_id)
    if payload.full_name is not None:
        target.full_name = payload.full_name
    if payload.is_active is not None:
        if target.id == actor.id and payload.is_active is False:
            raise bad_request("CANNOT_DEACTIVATE_SELF", "You cannot deactivate yourself")
        target.is_active = payload.is_active
        if payload.is_active:
            if target.status == "suspended":
                target.status = "active"
        elif target.status == "active":
            target.status = "suspended"
    if payload.status is not None:
        if target.id == actor.id and payload.status != "active":
            raise bad_request("CANNOT_DEACTIVATE_SELF", "You cannot change your own status")
        target.status = payload.status
        target.is_active = payload.status != "suspended"
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="user.updated", entity_type="user", entity_id=target.id,
        meta=payload.model_dump(exclude_none=True),
    )
    db.commit()
    return _to_read(repo.get_with_roles(actor.effective_organization_id, user_id))


@router.put("/{user_id}/roles", response_model=UserRead, summary="Replace user roles")
def update_user_roles(
    user_id: UUID,
    payload: UserRolesUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.update")),
) -> UserRead:
    repo = UserRepository(db)
    target = repo.get_with_roles(actor.effective_organization_id, user_id)
    if target.id == actor.id and "owner" not in payload.role_codes:
        raise bad_request("CANNOT_REMOVE_OWN_OWNER", "You cannot remove your own owner role")

    actor_is_owner = "owner" in user_role_codes(actor)
    target_is_owner = "owner" in [r.code for r in target.roles]
    if (target_is_owner or "owner" in payload.role_codes) and not actor_is_owner:
        raise bad_request(
            "OWNER_ROLES_RESTRICTED", "Only the owner can change the owner role"
        )

    role_codes = set(payload.role_codes)
    roles = db.execute(
        select(Role).where(
            Role.organization_id == actor.effective_organization_id,
            Role.code.in_(role_codes),
        )
    ).scalars()
    roles = list(roles)
    if len(roles) != len(role_codes):
        raise bad_request("INVALID_ROLE", "One or more roles do not exist")

    target.roles = roles
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="user.roles_changed", entity_type="user", entity_id=target.id,
        meta={"roles": payload.role_codes},
    )
    db.commit()
    return _to_read(repo.get_with_roles(actor.effective_organization_id, user_id))


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Remove a user",
    description="Hard-deletes an invited user; otherwise suspends the account so "
    "the user can no longer log in.",
)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.delete")),
) -> None:
    repo = UserRepository(db)
    target = repo.get_with_roles(actor.effective_organization_id, user_id)
    if target.id == actor.id:
        raise bad_request("CANNOT_DEACTIVATE_SELF", "You cannot deactivate yourself")
    if "owner" in [r.code for r in target.roles]:
        raise bad_request("CANNOT_DELETE_OWNER", "The owner role cannot be deactivated")
    if target.status == "invited":
        db.delete(target)
        log_action(
            db, organization_id=actor.effective_organization_id, user_id=actor.id,
            action="user.invite_revoked", entity_type="user", entity_id=target.id,
        )
    else:
        target.is_active = False
        target.status = "suspended"
        log_action(
            db, organization_id=actor.effective_organization_id, user_id=actor.id,
            action="user.deactivated", entity_type="user", entity_id=target.id,
        )
    db.commit()
