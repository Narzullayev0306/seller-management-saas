from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.services.permissions import PERMISSIONS

router = APIRouter(prefix="/roles", tags=["roles"])


class MatrixRole(BaseModel):
    id: str
    name: str
    code: str
    is_system: bool
    permissions: list[str]


class PermissionInfo(BaseModel):
    code: str
    description: str


class RoleMatrix(BaseModel):
    roles: list[MatrixRole]
    permissions: list[PermissionInfo]


@router.get(
    "/matrix",
    response_model=RoleMatrix,
    summary="Role permission matrix",
    description=(
        "Organization roles with their granted permission codes, plus the full "
        "permission catalog with descriptions. Used to render the permission matrix."
    ),
)
def role_matrix(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("users.read")),
) -> RoleMatrix:
    roles = db.execute(
        select(Role)
        .where(Role.organization_id == user.effective_organization_id)
        .order_by(Role.is_system.desc(), Role.name)
    ).scalars().all()
    return RoleMatrix(
        roles=[
            MatrixRole(
                id=str(r.id),
                name=r.name,
                code=r.code,
                is_system=r.is_system,
                permissions=sorted(p.code for p in r.permissions),
            )
            for r in roles
        ],
        permissions=[
            PermissionInfo(code=code, description=desc)
            for code, desc in PERMISSIONS.items()
        ],
    )
