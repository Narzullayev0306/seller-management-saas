"""Supabase Storage integration (REST API via httpx).

The Storage API mirrors S3: presigned upload URLs, public object URLs.
Fails loudly (503) when the project URL / service key are not configured.
"""

from __future__ import annotations

import re
from uuid import uuid4

import httpx

from app.core.config import settings
from app.core.exceptions import ApiError

ALLOWED_BUCKETS = {"products", "brands", "reviews"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/avif": "avif",
    "image/gif": "gif",
}
UPLOAD_EXPIRES_IN = 3600
MAX_SIZE_MB = 5


def _ensure_configured() -> None:
    if not settings.supabase_url or not settings.supabase_service_key:
        raise ApiError(
            503,
            "STORAGE_NOT_CONFIGURED",
            "Supabase Storage is not configured. Add SUPABASE_URL and "
            "SUPABASE_SERVICE_KEY to the environment.",
        )


def _headers() -> dict:
    return {
        "apikey": settings.supabase_anon_key or settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
    }


def _safe_path(bucket: str, filename: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", filename.rsplit("/", 1)[-1])[:80]
    stem = stem or "image"
    return f"{uuid4()}/{stem}"


def public_url(bucket: str, path: str) -> str:
    return f"{settings.supabase_url}/storage/v1/object/public/{bucket}/{path}"


async def create_signed_upload_url(bucket: str, content_type: str, filename: str) -> dict:
    _ensure_configured()
    if bucket not in ALLOWED_BUCKETS:
        raise ApiError(400, "INVALID_BUCKET", f"Bucket must be one of {sorted(ALLOWED_BUCKETS)}")
    ext = ALLOWED_CONTENT_TYPES.get(content_type)
    if ext is None:
        raise ApiError(400, "INVALID_CONTENT_TYPE", "Only JPEG, PNG, WebP, AVIF and GIF images are allowed")
    path = _safe_path(bucket, filename or f"image.{ext}")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{settings.supabase_url}/storage/v1/object/upload/sign/{bucket}/{path}",
            headers=_headers(),
            json={"contentType": content_type, "expiresIn": UPLOAD_EXPIRES_IN},
        )
    if resp.status_code not in (200, 201):
        raise ApiError(502, "STORAGE_UPLOAD_SIGN_FAILED", f"Supabase Storage error: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    return {
        "url": data["signedUrl"],
        "token": data["token"],
        "path": data["path"],
        "public_url": public_url(bucket, data["path"]),
        "expires_in": UPLOAD_EXPIRES_IN,
        "max_size_mb": MAX_SIZE_MB,
    }


async def delete_object(bucket: str, path: str) -> None:
    _ensure_configured()
    async with httpx.AsyncClient(timeout=10) as client:
        await client.delete(
            f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}",
            headers=_headers(),
        )
