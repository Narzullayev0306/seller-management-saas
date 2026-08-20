"""Custom domain management with TXT-record verification."""

from __future__ import annotations

import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import conflict
from app.models.domain import OrganizationDomain
from app.services.billing_service import require_feature


def require_domain_feature(db: Session, org_id: UUID) -> None:
    require_feature(db, org_id, "custom_domain")


def list_domains(db: Session, org_id: UUID) -> list[OrganizationDomain]:
    return (
        db.execute(
            select(OrganizationDomain)
            .where(OrganizationDomain.organization_id == org_id)
            .order_by(OrganizationDomain.created_at)
        )
        .scalars()
        .all()
    )


def add_domain(db: Session, org_id: UUID, domain: str) -> OrganizationDomain:
    domain = domain.strip().lower().rstrip(".")
    existing = db.execute(
        select(OrganizationDomain).where(OrganizationDomain.domain == domain)
    ).scalar_one_or_none()
    if existing is not None:
        raise conflict("DOMAIN_TAKEN", "This domain is already in use")
    row = OrganizationDomain(
        organization_id=org_id,
        domain=domain,
        verification_token=secrets.token_urlsafe(24),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def mark_verified(db: Session, domain: OrganizationDomain) -> OrganizationDomain:
    from datetime import UTC, datetime

    domain.status = "verified"
    domain.verified_at = datetime.now(UTC)
    db.commit()
    db.refresh(domain)
    return domain


def remove_domain(db: Session, domain: OrganizationDomain) -> None:
    db.delete(domain)
    db.commit()


def resolve_org_by_host(db: Session, host: str) -> UUID | None:
    """Map a verified custom domain back to an organization id (if any)."""
    host = (host or "").split(":")[0].strip().lower()
    if not host:
        return None
    row = db.execute(
        select(OrganizationDomain).where(
            OrganizationDomain.domain == host,
            OrganizationDomain.status == "verified",
        )
    ).scalar_one_or_none()
    return row.organization_id if row is not None else None
