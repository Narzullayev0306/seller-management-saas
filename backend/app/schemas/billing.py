from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    price: Decimal
    description: str
    features: list[str]
    limits: dict


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    plan: str
    amount: Decimal
    currency: str
    status: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    created_at: datetime


class BillingSummary(BaseModel):
    plan: str
    plan_name: str
    price: Decimal
    features: list[str]
    limits: dict
    usage: dict
    subscription_status: str
    period_end: datetime | None = None


class ChangePlanRequest(BaseModel):
    plan: Literal["free", "pro", "enterprise"]
