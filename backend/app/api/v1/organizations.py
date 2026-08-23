from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_owner, require_permissions
from app.core.exceptions import bad_request, conflict
from app.db.session import get_db
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.organization import OrganizationRead, OrganizationUpdate
from app.services.audit_service import log_action
from app.services.notification_service import notify_team_owner_transferred

router = APIRouter(prefix="/organizations", tags=["organizations"])


class PlanUpdate(BaseModel):
    plan: Literal["free", "pro", "enterprise"]


class OwnershipTransfer(BaseModel):
    user_id: UUID = Field(description="Member who will become the new owner")


@router.get(
    "/me",
    response_model=OrganizationRead,
    summary="Get the caller's company settings",
)
def get_my_organization(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> Organization:
    return db.get(Organization, user.effective_organization_id)


@router.patch(
    "/me",
    response_model=OrganizationRead,
    summary="Update the caller's company settings",
    description="Updates name, logo, favicon, brand colors, description, social "
    "links, currency, timezone, address, phone and email.",
)
def update_my_organization(
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> Organization:
    org = db.get(Organization, actor.effective_organization_id)
    data = payload.model_dump(exclude_none=True)
    if "name" in data and data["name"].lower() != org.name.lower():
        existing = db.execute(
            select(Organization).where(Organization.name == data["name"])
        ).scalar_one_or_none()
        if existing is not None:
            raise conflict("NAME_TAKEN", "This company name is already taken")
    for field, value in data.items():
        setattr(org, field, value)
    log_action(
        db,
        organization_id=actor.effective_organization_id,
        user_id=actor.id,
        action="organization.updated",
        entity_type="organization",
        entity_id=org.id,
        meta=data,
    )
    db.commit()
    db.refresh(org)
    return org


@router.patch(
    "/me/plan",
    response_model=OrganizationRead,
    summary="Change the company plan",
    description="Owner only. Selects a billing plan for the workspace.",
)
def update_plan(
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_owner),
) -> Organization:
    org = db.get(Organization, actor.effective_organization_id)
    old = org.plan
    org.plan = payload.plan
    log_action(
        db,
        organization_id=actor.effective_organization_id,
        user_id=actor.id,
        action="organization.plan_changed",
        entity_type="organization",
        entity_id=org.id,
        meta={"from": old, "to": payload.plan},
    )
    db.commit()
    db.refresh(org)
    return org


@router.post(
    "/me/transfer-ownership",
    response_model=OrganizationRead,
    summary="Transfer company ownership",
    description="Owner only. Makes another active member the new owner; the "
    "current owner keeps their account but loses the owner role.",
    responses={
        400: {"description": "Target is the current owner, not active, or owner role not found"},
        404: {"description": "Target user not found in this company"},
    },
)
def transfer_ownership(
    payload: OwnershipTransfer,
    db: Session = Depends(get_db),
    actor: User = Depends(require_owner),
) -> Organization:
    if payload.user_id == actor.id:
        raise bad_request("SELF_TRANSFER", "You are already the owner")
    repo = UserRepository(db)
    target = repo.get_with_roles(actor.effective_organization_id, payload.user_id)
    if target is None:
        from app.core.exceptions import not_found

        raise not_found("User")
    if not target.is_active or target.status != "active":
        raise bad_request("TARGET_INACTIVE", "The new owner must be an active member")
    if "owner" in [r.code for r in target.roles]:
        raise bad_request("ALREADY_OWNER", "This member is already the owner")

    owner_role = db.execute(
        select(Role).where(
            Role.organization_id == actor.effective_organization_id,
            Role.code == "owner",
        )
    ).scalar_one_or_none()
    if owner_role is None:
        raise bad_request("OWNER_ROLE_MISSING", "The owner role does not exist")
    target.roles.append(owner_role)
    actor.roles = [r for r in actor.roles if r.code != "owner"]

    log_action(
        db,
        organization_id=actor.effective_organization_id,
        user_id=actor.id,
        action="organization.ownership_transferred",
        entity_type="user",
        entity_id=target.id,
    )
    notify_team_owner_transferred(
        db, actor.effective_organization_id, actor.id, target.email
    )
    db.commit()
    db.refresh(actor.organization)
    return actor.organization


@router.post(
    "/me/close",
    status_code=200,
    summary="Close the company",
    description="Owner only. Soft-deletes the workspace: every member loses "
    "access immediately and the data is kept for recovery.",
    responses={400: {"description": "Only the owner can close the company"}},
)
def close_company(
    db: Session = Depends(get_db),
    actor: User = Depends(require_owner),
) -> dict:
    org = db.get(Organization, actor.effective_organization_id)
    org.is_active = False
    log_action(
        db,
        organization_id=actor.effective_organization_id,
        user_id=actor.id,
        action="organization.closed",
        entity_type="organization",
        entity_id=org.id,
    )
    db.commit()
    return {"message": "Company closed. You can no longer sign in."}
