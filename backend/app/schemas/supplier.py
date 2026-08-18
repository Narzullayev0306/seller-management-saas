from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import PageParams


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=300)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=300)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")


class SupplierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str | None
    phone: str | None
    address: str | None
    status: str
    created_at: datetime


class SupplierListParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")
    sort_by: str | None = None
    sort_order: str | None = Field(default=None, pattern="^(asc|desc)$")
