from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import bad_request
from app.db.session import get_db
from app.models.coupon import Coupon
from app.models.user import User
from app.schemas.common import Page
from app.schemas.coupon import (
    CouponCreate,
    CouponListParams,
    CouponRead,
    CouponUpdate,
    CouponValidateResult,
)
from app.services.audit_service import log_action
from app.services.coupon_service import get_coupon, validate_coupon

router = APIRouter(prefix="/coupons", tags=["coupons"])


def _to_read(coupon: Coupon) -> CouponRead:
    return CouponRead(
        id=coupon.id,
        code=coupon.code,
        description=coupon.description,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value,
        min_subtotal=coupon.min_subtotal,
        max_redemptions=coupon.max_redemptions,
        max_per_customer=coupon.max_per_customer,
        active=coupon.active,
        starts_at=coupon.starts_at,
        expires_at=coupon.expires_at,
        usage_count=coupon.usage_count,
        created_at=coupon.created_at,
    )


@router.get(
    "",
    response_model=Page[CouponRead],
    summary="List coupons",
    description="Paginated coupon list with search and active filter.",
)
def list_coupons(
    params: CouponListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("coupons.read")),
) -> Page[CouponRead]:
    org_id = user.effective_organization_id
    stmt = select(Coupon).where(Coupon.organization_id == org_id)
    if params.search:
        stmt = stmt.where(Coupon.code.ilike(f"%{params.search}%"))
    if params.active is not None:
        stmt = stmt.where(Coupon.active.is_(params.active))
    total = db.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()
    rows = db.execute(
        stmt.order_by(Coupon.created_at.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    ).scalars().all()
    return Page[CouponRead](
        items=[_to_read(c) for c in rows],
        page=params.page, page_size=params.page_size, total=total,
        total_pages=(total + params.page_size - 1) // params.page_size,
    )


@router.post(
    "", response_model=CouponRead, status_code=201, summary="Create a coupon",
    description="Codes are case-insensitive and unique per organization.",
)
def create_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("coupons.create")),
) -> CouponRead:
    org_id = actor.effective_organization_id
    code = payload.code.strip().upper()
    existing = db.execute(
        select(Coupon.id).where(
            Coupon.organization_id == org_id,
            func.upper(Coupon.code) == code,
        )
    ).scalar_one_or_none()
    if existing:
        raise bad_request("COUPON_EXISTS", "A coupon with this code already exists")
    if payload.expires_at is not None and payload.starts_at is not None and payload.expires_at <= payload.starts_at:
        raise bad_request("VALIDATION_ERROR", "expires_at must be after starts_at")
    coupon = Coupon(
        organization_id=org_id,
        code=code,
        description=payload.description,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        min_subtotal=payload.min_subtotal,
        max_redemptions=payload.max_redemptions,
        max_per_customer=payload.max_per_customer,
        active=payload.active,
        starts_at=payload.starts_at,
        expires_at=payload.expires_at,
    )
    db.add(coupon)
    log_action(
        db, organization_id=org_id, user_id=actor.id,
        action="coupon.created", entity_type="coupon", entity_id=coupon.id,
        meta={"code": coupon.code, "discount_type": coupon.discount_type},
    )
    db.commit()
    return _to_read(get_coupon(db, org_id, coupon.id))


@router.get("/validate", response_model=CouponValidateResult, summary="Validate a coupon")
def validate_coupon_endpoint(
    code: str,
    subtotal: Decimal | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("coupons.read")),
) -> CouponValidateResult:
    org_id = user.effective_organization_id
    try:
        coupon = validate_coupon(
            db, org_id, code, subtotal if subtotal is not None else Decimal("0")
        )
    except Exception as exc:
        code_out = getattr(exc, "code", None) or "COUPON_INVALID"
        return CouponValidateResult(
            valid=False,
            code=code.strip().upper(),
            discount_type="",
            discount_value=Decimal("0"),
            message=code_out,
        )
    return CouponValidateResult(
        valid=True,
        code=coupon.code,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value,
        min_subtotal=coupon.min_subtotal,
        message="valid",
    )


@router.get("/{coupon_id}", response_model=CouponRead, summary="Get a coupon")
def get_coupon_endpoint(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("coupons.read")),
) -> CouponRead:
    return _to_read(get_coupon(db, user.effective_organization_id, coupon_id))


@router.patch("/{coupon_id}", response_model=CouponRead, summary="Update a coupon")
def update_coupon(
    coupon_id: UUID,
    payload: CouponUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("coupons.update")),
) -> CouponRead:
    org_id = actor.effective_organization_id
    coupon = get_coupon(db, org_id, coupon_id)
    data = payload.model_dump(exclude_none=True)
    if "code" in data:
        new_code = data["code"].strip().upper()
        existing = db.execute(
            select(Coupon.id).where(
                Coupon.organization_id == org_id,
                func.upper(Coupon.code) == new_code,
                Coupon.id != coupon.id,
            )
        ).scalar_one_or_none()
        if existing:
            raise bad_request("COUPON_EXISTS", "A coupon with this code already exists")
        data["code"] = new_code
    if (
        payload.expires_at is not None
        and (payload.starts_at or coupon.starts_at) is not None
        and payload.expires_at <= (payload.starts_at or coupon.starts_at)
    ):
        raise bad_request("VALIDATION_ERROR", "expires_at must be after starts_at")
    for field, value in data.items():
        setattr(coupon, field, value)
    log_action(
        db, organization_id=org_id, user_id=actor.id,
        action="coupon.updated", entity_type="coupon", entity_id=coupon.id,
        meta=data,
    )
    db.commit()
    return _to_read(get_coupon(db, org_id, coupon_id))


@router.delete(
    "/{coupon_id}",
    status_code=204,
    summary="Delete a coupon",
    description="Deactivates the coupon; redemptions are kept.",
)
def delete_coupon(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("coupons.delete")),
) -> None:
    org_id = actor.effective_organization_id
    coupon = get_coupon(db, org_id, coupon_id)
    if coupon.active:
        coupon.active = False
        log_action(
            db, organization_id=org_id, user_id=actor.id,
            action="coupon.deactivated", entity_type="coupon", entity_id=coupon.id,
        )
        db.commit()
