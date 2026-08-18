
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditListParams, AuditLogRead
from app.schemas.common import Page, build_page

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get(
    "",
    response_model=Page[AuditLogRead],
    summary="List audit logs",
    description="Paginated audit trail, filterable by user, action, entity type and date range.",
)
def list_audit_logs(
    params: AuditListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("audit.read")),
) -> Page[AuditLogRead]:
    base_filter = [AuditLog.organization_id == user.effective_organization_id]
    if params.user_id:
        base_filter.append(AuditLog.user_id == params.user_id)
    if params.action:
        base_filter.append(AuditLog.action == params.action)
    if params.entity_type:
        base_filter.append(AuditLog.entity_type == params.entity_type)
    if params.start_date:
        base_filter.append(AuditLog.created_at >= params.start_date)
    if params.end_date:
        base_filter.append(AuditLog.created_at <= params.end_date)

    count_stmt = select(func.count(AuditLog.id)).where(*base_filter)
    total = int(db.execute(count_stmt).scalar_one())

    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(*base_filter)
        .order_by(AuditLog.created_at.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )

    rows = list(db.execute(stmt).scalars())
    items = [
        AuditLogRead(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.full_name if log.user else None,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            meta=log.meta,
            created_at=log.created_at,
        )
        for log in rows
    ]
    return build_page(items, params.page, params.page_size, total)
