from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageParams


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    user_name: str | None = None
    action: str
    entity_type: str | None
    entity_id: UUID | None
    meta: dict | None
    created_at: datetime


class AuditListParams(PageParams):
    user_id: UUID | None = None
    action: str | None = Field(default=None, max_length=50)
    entity_type: str | None = Field(default=None, max_length=50)
    start_date: datetime | None = None
    end_date: datetime | None = None
