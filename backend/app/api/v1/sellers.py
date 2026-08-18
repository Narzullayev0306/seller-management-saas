from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.core.exceptions import bad_request
from app.db.session import get_db
from app.models.order import Order
from app.models.sale import Sale
from app.models.seller import Seller
from app.models.user import User
from app.repositories.seller_repo import SellerRepository
from app.schemas.common import Page
from app.schemas.seller import (
    SellerCreate,
    SellerListParams,
    SellerRead,
    SellerStats,
    SellerUpdate,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/sellers", tags=["sellers"])


def _to_read(seller: Seller) -> SellerRead:
    return SellerRead(
        id=seller.id,
        first_name=seller.first_name,
        last_name=seller.last_name,
        email=seller.email,
        phone=seller.phone,
        status=seller.status,
        commission_rate=seller.commission_rate,
        total_sales=seller.total_sales,
        total_orders=seller.total_orders,
        created_at=seller.created_at,
    )


@router.get(
    "",
    response_model=Page[SellerRead],
    summary="List sellers",
    description="Paginated, searchable list with status filter and sorting.",
)
def list_sellers(
    params: SellerListParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("sellers.read")),
) -> Page[SellerRead]:
    repo = SellerRepository(db)
    page = repo.list_page(
        user.effective_organization_id,
        page=params.page, page_size=params.page_size,
        search=params.search, status=params.status,
        sort_by=params.sort_by, sort_order=params.sort_order,
    )
    return Page[SellerRead](
        items=[_to_read(s) for s in page.items],
        page=page.page, page_size=page.page_size, total=page.total,
        total_pages=page.total_pages,
    )


@router.post(
    "", response_model=SellerRead, status_code=201, summary="Create a seller"
)
def create_seller(
    payload: SellerCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("sellers.create")),
) -> SellerRead:
    repo = SellerRepository(db)
    if payload.email:
        existing = db.execute(
            select(Seller).where(
                Seller.organization_id == actor.effective_organization_id,
                Seller.email == payload.email.lower(),
            )
        ).scalar_one_or_none()
        if existing:
            raise bad_request("EMAIL_TAKEN", "A seller with this email already exists")
    seller = repo.create(
        actor.effective_organization_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower() if payload.email else None,
        phone=payload.phone,
        status=payload.status,
        commission_rate=payload.commission_rate,
        user_id=payload.user_id,
    )
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="seller.created", entity_type="seller", entity_id=seller.id,
        meta={"email": seller.email},
    )
    db.commit()
    return _to_read(seller)


@router.get("/{seller_id}", response_model=SellerRead, summary="Get a seller")
def get_seller(
    seller_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("sellers.read")),
) -> SellerRead:
    repo = SellerRepository(db)
    seller = repo.get(user.effective_organization_id, seller_id)
    return _to_read(seller)


@router.get(
    "/{seller_id}/stats",
    response_model=SellerStats,
    summary="Seller statistics",
    description="Sales totals, commission, recent orders and monthly performance.",
)
def seller_stats(
    seller_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("sellers.read")),
) -> SellerStats:
    repo = SellerRepository(db)
    seller = repo.get(user.effective_organization_id, seller_id)
    orders = db.execute(
        select(Order)
        .options(selectinload(Order.customer), selectinload(Order.items))
        .where(
            Order.organization_id == user.effective_organization_id,
            Order.seller_id == seller.id,
            Order.status != "cancelled",
        )
        .order_by(Order.created_at.desc())
        .limit(10)
    ).scalars()
    recent = [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "status": o.status,
            "total": str(o.total),
            "customer": o.customer.full_name if o.customer else None,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]

    commission = db.execute(
        select(Sale).where(
            Sale.organization_id == user.effective_organization_id,
            Sale.seller_id == seller.id,
        )
    ).scalars()
    total_commission = sum((s.commission_amount for s in commission), Decimal("0"))

    perf = db.execute(
        select(
            func.date_trunc("month", Order.created_at).label("month"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .where(
            Order.organization_id == user.effective_organization_id,
            Order.seller_id == seller.id,
            Order.status != "cancelled",
        )
        .group_by("month")
        .order_by("month")
    ).all()

    return SellerStats(
        total_sales=seller.total_sales,
        total_orders=seller.total_orders,
        total_commission=total_commission,
        avg_order_value=(
            seller.total_sales / Decimal(seller.total_orders)
            if seller.total_orders
            else Decimal("0")
        ),
        recent_orders=recent,
        performance=[
            {
                "month": r.month.strftime("%Y-%m"),
                "revenue": str(r.revenue),
            }
            for r in perf
        ],
    )


@router.patch("/{seller_id}", response_model=SellerRead, summary="Update a seller")
def update_seller(
    seller_id: UUID,
    payload: SellerUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("sellers.update")),
) -> SellerRead:
    repo = SellerRepository(db)
    seller = repo.get(actor.effective_organization_id, seller_id)
    data = payload.model_dump(exclude_none=True)
    if "email" in data:
        data["email"] = data["email"].lower()
    for field, value in data.items():
        setattr(seller, field, value)
    log_action(
        db, organization_id=actor.effective_organization_id, user_id=actor.id,
        action="seller.updated", entity_type="seller", entity_id=seller.id,
        meta=data,
    )
    db.commit()
    return _to_read(seller)


@router.delete(
    "/{seller_id}",
    status_code=204,
    summary="Deactivate a seller",
    description="Sets the seller status to 'inactive'.",
)
def delete_seller(
    seller_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("sellers.delete")),
) -> None:
    repo = SellerRepository(db)
    seller = repo.get(actor.effective_organization_id, seller_id)
    if seller.status != "inactive":
        seller.status = "inactive"
        log_action(
            db, organization_id=actor.effective_organization_id, user_id=actor.id,
            action="seller.deactivated", entity_type="seller", entity_id=seller.id,
        )
        db.commit()
