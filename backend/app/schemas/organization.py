from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    plan: str
    logo_url: str | None = None
    currency: str
    timezone: str
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    created_at: datetime


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    logo_url: str | None = Field(default=None, max_length=500)
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    address: str | None = Field(default=None, max_length=300)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
