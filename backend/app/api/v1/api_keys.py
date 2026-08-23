from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyRead, ApiKeyUpdate, ApiKeyWithSecret
from app.services import api_key_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _to_read(key) -> ApiKeyRead:
    return ApiKeyRead(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        scopes=key.scopes,
        is_active=key.is_active,
        expires_at=key.expires_at,
        last_used_at=key.last_used_at,
        created_at=key.created_at,
    )


@router.get(
    "",
    response_model=list[ApiKeyRead],
    summary="List API keys",
)
def list_api_keys(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("settings.read")),
) -> list[ApiKeyRead]:
    return [
        _to_read(k) for k in api_key_service.list_api_keys(db, user.effective_organization_id)
    ]


@router.post(
    "",
    response_model=ApiKeyWithSecret,
    status_code=201,
    summary="Create an API key",
    description="The raw key is returned exactly once; only its hash is stored.",
)
def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> ApiKeyWithSecret:
    key, secret = api_key_service.create_api_key(
        db, actor.effective_organization_id, payload, actor.id
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="api_key.created", entity_type="api_key", entity_id=key.id,
        meta={"name": key.name, "scopes": key.scopes},
    )
    db.commit()
    return ApiKeyWithSecret(**_to_read(key).model_dump(), key=secret)


@router.patch(
    "/{key_id}",
    response_model=ApiKeyRead,
    summary="Update an API key (rename, scopes, activate/revoke, expiry)",
)
def update_api_key(
    key_id: UUID,
    payload: ApiKeyUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> ApiKeyRead:
    key = api_key_service.update_api_key(
        db, actor.effective_organization_id, key_id, payload, actor.id
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="api_key.updated", entity_type="api_key", entity_id=key_id,
        meta={"name": key.name, "is_active": key.is_active},
    )
    db.commit()
    return _to_read(key)


@router.delete(
    "/{key_id}",
    status_code=204,
    summary="Delete an API key",
)
def delete_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.update")),
) -> None:
    api_key_service.delete_api_key(db, actor.effective_organization_id, key_id, actor.id)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="api_key.deleted", entity_type="api_key", entity_id=key_id,
    )
    db.commit()
