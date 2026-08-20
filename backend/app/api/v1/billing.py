"""Billing: plan catalog, subscription, invoices and usage enforcement."""


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_owner, require_permissions
from app.core.exceptions import bad_request
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.billing import (
    BillingSummary,
    ChangePlanRequest,
    InvoiceRead,
    PlanRead,
)
from app.services import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get(
    "/plans",
    response_model=list[PlanRead],
    summary="List available plans",
    description="The full plan catalog with prices, limits and features.",
)
def list_plans(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("billing.read")),
) -> list[PlanRead]:
    return [PlanRead(**plan) for plan in billing_service.get_plan_catalog()]


@router.get(
    "/summary",
    response_model=BillingSummary,
    summary="Get the current plan, usage and limits",
    description="Shows the org's plan, feature set, limits and current usage "
    "counts (users, products, orders this month).",
)
def billing_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("billing.read")),
) -> BillingSummary:
    org_id = user.effective_organization_id
    org = db.get(Organization, org_id)
    subscription = billing_service.get_or_create_subscription(db, org_id)
    info = billing_service.plan_info(org.plan)
    db.commit()
    return BillingSummary(
        plan=org.plan,
        plan_name=info["name"],
        price=info["price"],
        features=info["features"],
        limits=info["limits"],
        usage=billing_service.count_usage(db, org_id),
        subscription_status=subscription.status,
        period_end=subscription.current_period_end,
    )


@router.post(
    "/change-plan",
    response_model=BillingSummary,
    summary="Change the organization plan",
    description="Owner only. Switches the plan, resets the billing period and "
    "records a paid invoice.",
    responses={400: {"description": "Unknown plan"}},
)
def change_plan(
    payload: ChangePlanRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_owner),
) -> BillingSummary:
    org_id = actor.effective_organization_id
    if payload.plan not in billing_service.PLAN_CATALOG:
        raise bad_request("UNKNOWN_PLAN", "Unknown plan code")
    org, subscription, _ = billing_service.change_plan(
        db, org_id, payload.plan, actor_user_id=actor.id
    )
    info = billing_service.plan_info(org.plan)
    return BillingSummary(
        plan=org.plan,
        plan_name=info["name"],
        price=info["price"],
        features=info["features"],
        limits=info["limits"],
        usage=billing_service.count_usage(db, org_id),
        subscription_status=subscription.status,
        period_end=subscription.current_period_end,
    )


@router.get(
    "/invoices",
    response_model=list[InvoiceRead],
    summary="List invoices",
    description="Invoices issued on plan changes, newest first.",
)
def list_invoices(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("billing.read")),
) -> list[InvoiceRead]:
    return [
        InvoiceRead.model_validate(inv)
        for inv in billing_service.list_invoices(db, user.effective_organization_id)
    ]
