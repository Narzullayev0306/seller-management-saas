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
    favicon_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    description: str | None = None
    social_links: dict | None = None
    currency: str
    timezone: str
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    created_at: datetime


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    logo_url: str | None = Field(default=None, max_length=500)
    favicon_url: str | None = Field(default=None, max_length=500)
    primary_color: str | None = Field(
        default=None, pattern=r"^#[0-9a-fA-F]{6}$|^#[0-9a-fA-F]{8}$|^$"
    )
    secondary_color: str | None = Field(
        default=None, pattern=r"^#[0-9a-fA-F]{6}$|^#[0-9a-fA-F]{8}$|^$"
    )
    description: str | None = Field(default=None, max_length=2000)
    social_links: dict | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    address: str | None = Field(default=None, max_length=300)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
