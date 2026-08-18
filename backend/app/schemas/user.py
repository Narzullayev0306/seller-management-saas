from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import PageParams


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    status: str = "active"
    roles: list[str] = []
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role_codes: list[str] = Field(min_length=1)


class UserInvite(BaseModel):
    email: EmailStr
    full_name: str = Field(default="", min_length=0, max_length=150)
    role_codes: list[str] = Field(min_length=1)


class AcceptInvite(BaseModel):
    token: str = Field(min_length=1)
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class ResendInvite(BaseModel):
    user_id: UUID


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    is_active: bool | None = None
    status: str | None = Field(
        default=None, pattern="^(active|invited|suspended)$"
    )


class UserRolesUpdate(BaseModel):
    role_codes: list[str] = Field(min_length=1)


class UserListParams(PageParams):
    search: str | None = Field(default=None, max_length=100)
    status: str | None = Field(
        default=None, pattern="^(active|invited|suspended)$"
    )
