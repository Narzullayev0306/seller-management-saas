"""Payment provider abstraction.

Providers are pluggable and payment-provider agnostic: checkout code only
depends on the PaymentProvider interface, so Stripe / Payme / Click / Uzum
can be added as new implementations without touching order flow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel


class PaymentResult(BaseModel):
    success: bool
    provider_payment_id: str | None = None
    message: str = ""


class PaymentProvider(ABC):
    name: str = "base"

    @abstractmethod
    def process(
        self, *, amount: Decimal, currency: str, order_number: str
    ) -> PaymentResult:
        """Charge the given amount. Returns success/failure synchronously;
        real providers wrap async callbacks/webhooks behind the same result."""


class MockPaymentProvider(PaymentProvider):
    """Auto-approving provider used in dev/tests and as the default."""

    name = "mock"

    def process(
        self, *, amount: Decimal, currency: str, order_number: str
    ) -> PaymentResult:
        return PaymentResult(
            success=True,
            provider_payment_id=f"mock_{uuid4().hex[:12]}",
            message="approved",
        )


class DeclinedPaymentProvider(PaymentProvider):
    """Provider that always declines — used to exercise failure paths."""

    name = "decline"

    def process(
        self, *, amount: Decimal, currency: str, order_number: str
    ) -> PaymentResult:
        return PaymentResult(
            success=False,
            provider_payment_id=f"declined_{uuid4().hex[:12]}",
            message="payment declined",
        )


PROVIDERS: dict[str, type[PaymentProvider]] = {
    "mock": MockPaymentProvider,
    "decline": DeclinedPaymentProvider,
}


def get_payment_provider(name: str) -> PaymentProvider:
    provider_cls = PROVIDERS.get(name)
    if provider_cls is None:
        raise ValueError(f"Unknown payment provider: {name}")
    return provider_cls()
