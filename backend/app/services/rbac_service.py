from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Permission, Role
from app.models.user import User
from app.services.permissions import (
    PERMISSIONS,
    SYSTEM_ROLE_NAMES,
    SYSTEM_ROLE_PERMISSIONS,
)


def ensure_permission_catalog(db: Session) -> None:
    """Idempotently create the global permission catalog."""
    existing = {
        code for (code,) in db.execute(select(Permission.code)).all()
    }
    missing = set(PERMISSIONS) - existing
    if missing:
        db.add_all(
            Permission(code=code, description=desc)
            for code, desc in PERMISSIONS.items()
            if code in missing
        )
        db.flush()


def seed_organization_roles(db: Session, organization_id: UUID) -> dict[str, Role]:
    """Create the system roles for an organization with their permission sets."""
    ensure_permission_catalog(db)

    permissions = {
        p.code: p for p in db.execute(select(Permission)).scalars().all()
    }
    roles: dict[str, Role] = {}
    for code, name in SYSTEM_ROLE_NAMES.items():
        role = Role(
            organization_id=organization_id,
            name=name,
            code=code,
            is_system=True,
        )
        codes = SYSTEM_ROLE_PERMISSIONS.get(code, [])
        role.permissions = [permissions[c] for c in codes if c in permissions]
        db.add(role)
        roles[code] = role
    db.flush()
    return roles


def sync_system_role_permissions(db: Session) -> None:
    """Bring existing orgs' system roles up to date.

    Creates any system roles that did not exist when the org was seeded
    (e.g. a newly introduced "customer" role) and grants any newly-added
    permissions to the existing system roles. Idempotent.
    """
    ensure_permission_catalog(db)
    permissions = {
        p.code: p for p in db.execute(select(Permission)).scalars().all()
    }
    orgs = db.execute(select(Organization)).scalars().all()
    for org in orgs:
        existing = {
            r.code: r
            for r in db.execute(
                select(Role).where(
                    Role.organization_id == org.id, Role.is_system.is_(True)
                )
            ).scalars()
        }
        for code, name in SYSTEM_ROLE_NAMES.items():
            role = existing.get(code)
            if role is None:
                role = Role(
                    organization_id=org.id,
                    name=name,
                    code=code,
                    is_system=True,
                )
                db.add(role)
                existing[code] = role
            codes = SYSTEM_ROLE_PERMISSIONS.get(code, [])
            role.permissions = [permissions[c] for c in codes if c in permissions]

    db.flush()


def _roles_of(user: User) -> list[Role]:
    roles = getattr(user, "effective_roles", None)
    return roles if roles is not None else list(user.roles)


def user_permissions(db: Session, user: User) -> list[str]:
    codes: set[str] = set()
    for role in _roles_of(user):
        codes.update(p.code for p in role.permissions)
    return sorted(codes)


def user_role_codes(user: User) -> list[str]:
    return [r.code for r in _roles_of(user)]
