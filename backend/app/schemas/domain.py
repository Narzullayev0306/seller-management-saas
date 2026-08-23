from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DomainRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    domain: str
    status: str
    verification_token: str
    verified_at: datetime | None = None
    is_primary: bool
    created_at: datetime


class DomainCreate(BaseModel):
    domain: str = Field(
        min_length=4,
        max_length=253,
        pattern=r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$",
    )


class DomainVerify(BaseModel):
    token: str = Field(min_length=1, max_length=64)
