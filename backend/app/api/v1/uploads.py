from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_permissions
from app.core.exceptions import ApiError
from app.models.user import User
from app.services import storage_service

router = APIRouter(prefix="/uploads", tags=["uploads"])


class SignedUploadRequest(BaseModel):
    bucket: Literal["products", "brands", "reviews"]
    content_type: str = Field(pattern=r"^image/(jpeg|png|webp|avif|gif)$")
    filename: str = Field(default="", max_length=200)


@router.post("/signed-url", status_code=201, summary="Get a signed upload URL for Supabase Storage")
async def signed_upload_url(
    payload: SignedUploadRequest,
    actor: User = Depends(require_permissions("products.update")),
) -> dict:
    try:
        return await storage_service.create_signed_upload_url(
            payload.bucket, payload.content_type, payload.filename
        )
    except ApiError:
        raise
