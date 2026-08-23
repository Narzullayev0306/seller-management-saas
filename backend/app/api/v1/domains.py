"""Custom domains for storefronts: management and TXT verification."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import bad_request, not_found
from app.db.session import get_db
from app.models.domain import OrganizationDomain
from app.models.user import User
from app.schemas.domain import DomainCreate, DomainRead, DomainVerify
from app.services import domain_service

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get(
    "",
    response_model=list[DomainRead],
    summary="List custom domains",
    description="Custom domains for the caller's storefront. Requires the Pro "
    "plan feature 'custom_domain'.",
)
def list_domains(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> list[DomainRead]:
    domain_service.require_domain_feature(db, user.effective_organization_id)
    return domain_service.list_domains(db, user.effective_organization_id)


@router.post(
    "",
    response_model=DomainRead,
    status_code=201,
    summary="Add a custom domain",
    description="Adds a domain in 'pending' status and returns the TXT "
    "verification token. Verify by adding a TXT record then calling verify.",
)
def add_domain(
    payload: DomainCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.update")),
) -> OrganizationDomain:
    domain_service.require_domain_feature(db, user.effective_organization_id)
    return domain_service.add_domain(db, user.effective_organization_id, payload.domain)


@router.post(
    "/{domain_id}/verify",
    response_model=DomainRead,
    summary="Verify a domain",
    description="Confirms the TXT verification token. For local/demo setups the "
    "token is returned in the response so verification can be simulated.",
)
def verify_domain(
    domain_id: UUID,
    payload: DomainVerify,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.update")),
) -> OrganizationDomain:
    domain = db.get(OrganizationDomain, domain_id)
    if domain is None or domain.organization_id != user.effective_organization_id:
        raise not_found("Domain")
    if payload.token != domain.verification_token:
        raise bad_request("DOMAIN_VERIFY_FAILED", "Verification token does not match")
    return domain_service.mark_verified(db, domain)


@router.delete(
    "/{domain_id}",
    status_code=204,
    summary="Remove a domain",
)
def remove_domain(
    domain_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.update")),
) -> None:
    domain = db.get(OrganizationDomain, domain_id)
    if domain is None or domain.organization_id != user.effective_organization_id:
        raise not_found("Domain")
    domain_service.remove_domain(db, domain)
