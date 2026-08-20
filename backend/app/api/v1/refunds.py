from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.refund import (
    RefundAction,
    RefundCreate,
    RefundRead,
    ReturnDecision,
    ReturnRequestRead,
)
from app.services import refund_service
from app.services.audit_service import log_action

router = APIRouter(tags=["refunds-returns"])


@router.get(
    "/returns",
    response_model=list[ReturnRequestRead],
    summary="List return requests",
)
def list_returns(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("orders.read")),
) -> list[ReturnRequestRead]:
    return [
        refund_service.return_read(r)
        for r in refund_service.list_returns(db, user.effective_organization_id)
    ]


@router.patch(
    "/returns/{return_id}",
    response_model=ReturnRequestRead,
    summary="Approve, reject, receive or complete a return request",
    description="Approving a return automatically creates a refund for the "
    "returned items.",
)
def decide_return(
    return_id: UUID,
    payload: ReturnDecision,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("orders.update")),
) -> ReturnRequestRead:
    request = refund_service.decide_return(
        db, actor.effective_organization_id, return_id, payload.action, actor
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action=f"return.{payload.action}", entity_type="return_request",
        entity_id=return_id, meta={"action": payload.action},
    )
    db.commit()
    return refund_service.return_read(request)


@router.get(
    "/refunds",
    response_model=list[RefundRead],
    summary="List refunds",
)
def list_refunds(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("orders.read")),
) -> list[RefundRead]:
    return [
        refund_service.refund_read(r)
        for r in refund_service.list_refunds(db, user.effective_organization_id)
    ]


@router.post(
    "/refunds",
    response_model=RefundRead,
    status_code=201,
    summary="Create a manual refund for an order",
    description="The amount cannot exceed the order total minus already-issued "
    "refunds.",
)
def create_refund(
    payload: RefundCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("orders.update")),
) -> RefundRead:
    refund = refund_service.create_manual_refund(
        db,
        actor.effective_organization_id,
        payload.order_id,
        payload.amount,
        payload.reason,
        payload.payment_id,
        actor,
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="refund.created", entity_type="refund", entity_id=refund.id,
        meta={"order_id": str(payload.order_id), "amount": str(payload.amount)},
    )
    db.commit()
    return refund_service.refund_read(refund)


@router.patch(
    "/refunds/{refund_id}",
    response_model=RefundRead,
    summary="Mark a refund as processed or failed",
)
def act_on_refund(
    refund_id: UUID,
    payload: RefundAction,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("orders.update")),
) -> RefundRead:
    refund = refund_service.act_on_refund(
        db, actor.effective_organization_id, refund_id, payload.action, actor
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action=f"refund.{payload.action}", entity_type="refund", entity_id=refund_id,
        meta={"action": payload.action},
    )
    db.commit()
    return refund_service.refund_read(refund)
