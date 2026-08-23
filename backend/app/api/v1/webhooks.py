from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.webhook import (
    WebhookCreate,
    WebhookDeliveryRead,
    WebhookRead,
    WebhookTestResult,
    WebhookUpdate,
)
from app.services import webhook_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "****"
    return secret[:4] + "****" + secret[-4:]


def _to_read(webhook) -> WebhookRead:
    read = WebhookRead.model_validate(webhook)
    read.secret = _mask_secret(read.secret)
    return read


@router.get(
    "",
    response_model=list[WebhookRead],
    summary="List webhook endpoints",
)
def list_webhooks(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> list[WebhookRead]:
    return [
        _to_read(w)
        for w in webhook_service.list_webhooks(db, user.effective_organization_id)
    ]


@router.post(
    "",
    response_model=WebhookRead,
    status_code=201,
    summary="Create a webhook endpoint",
    description="A signing secret is generated automatically; it is shown once "
    "in full only in the response to this call (masked afterwards).",
)
def create_webhook(
    payload: WebhookCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> WebhookRead:
    webhook = webhook_service.create_webhook(
        db, actor.effective_organization_id, payload
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="webhook.created", entity_type="webhook", entity_id=webhook.id,
        meta={"name": webhook.name, "url": webhook.url},
    )
    db.commit()
    return WebhookRead.model_validate(webhook)


@router.get(
    "/{webhook_id}",
    response_model=WebhookRead,
    summary="Get a webhook endpoint",
)
def get_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> WebhookRead:
    return _to_read(
        webhook_service._get_webhook(db, user.effective_organization_id, webhook_id)
    )


@router.patch(
    "/{webhook_id}",
    response_model=WebhookRead,
    summary="Update a webhook endpoint",
)
def update_webhook(
    webhook_id: UUID,
    payload: WebhookUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> WebhookRead:
    webhook = webhook_service.update_webhook(
        db, actor.effective_organization_id, webhook_id, payload
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="webhook.updated", entity_type="webhook", entity_id=webhook_id,
        meta={"name": webhook.name},
    )
    db.commit()
    return _to_read(webhook)


@router.delete(
    "/{webhook_id}",
    status_code=204,
    summary="Delete a webhook endpoint",
)
def delete_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> None:
    webhook_service.delete_webhook(db, actor.effective_organization_id, webhook_id)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="webhook.deleted", entity_type="webhook", entity_id=webhook_id,
        meta={"id": str(webhook_id)},
    )
    db.commit()


@router.post(
    "/{webhook_id}/test",
    response_model=WebhookTestResult,
    summary="Send a test ping to the endpoint",
)
def test_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> WebhookTestResult:
    delivery = webhook_service.test_webhook(
        db, actor.effective_organization_id, webhook_id
    )
    return WebhookTestResult(
        ok=delivery.error is None and (delivery.response_status or 0) < 400,
        response_status=delivery.response_status,
        response_body=delivery.response_body,
        error=delivery.error,
    )


@router.get(
    "/{webhook_id}/deliveries",
    response_model=list[WebhookDeliveryRead],
    summary="Delivery history for a webhook endpoint",
)
def webhook_deliveries(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> list[WebhookDeliveryRead]:
    return [
        WebhookDeliveryRead.model_validate(d)
        for d in webhook_service.list_deliveries(
            db, user.effective_organization_id, webhook_id
        )
    ]
