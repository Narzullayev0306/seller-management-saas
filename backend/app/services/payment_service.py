from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import Order
from app.models.organization import Organization
from app.models.payment import Payment
from app.services.payment_providers import PaymentResult, get_payment_provider


def process_order_payment(
    db: Session,
    organization_id: UUID,
    order: Order,
    provider_name: str | None = None,
) -> Payment:
    """Create a payment for an order and run it through the configured
    provider. On success the order is marked paid in the same transaction."""
    provider_name = provider_name or settings.payment_provider
    provider = get_payment_provider(provider_name)

    org = db.get(Organization, organization_id)
    currency = (org.currency or "USD") if org is not None else "USD"

    payment = Payment(
        organization_id=organization_id,
        order_id=order.id,
        provider=provider_name,
        amount=order.total,
        currency=currency,
        status="pending",
    )
    db.add(payment)
    db.flush()

    result: PaymentResult = provider.process(
        amount=order.total,
        currency=currency,
        order_number=order.order_number,
    )
    payment.provider_payment_id = result.provider_payment_id
    payment.failure_message = result.message if not result.success else None
    if result.success:
        payment.status = "paid"
        payment.paid_at = datetime.now(UTC)
        order.payment_status = "paid"
    else:
        payment.status = "failed"
        order.payment_status = "failed"
    db.flush()
    return payment
