from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.seller import Seller
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary
from app.services.analytics_service import AnalyticsService
from app.services.rbac_service import user_role_codes

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _linked_seller(db: Session, user: User) -> Seller | None:
    if "seller" not in user_role_codes(user):
        return None
    return db.execute(
        select(Seller).where(
            Seller.organization_id == user.effective_organization_id,
            Seller.user_id == user.id,
        )
    ).scalar_one_or_none()


@router.get(
    "/dashboard",
    response_model=AnalyticsSummary,
    summary="Full dashboard analytics",
    description=(
        "Summary metrics plus revenue/orders series, top products, top sellers "
        "and sales by category for the requested date range. "
        "Cancelled orders are excluded. Users with the 'seller' role only see "
        "their own sales."
    ),
)
def dashboard_analytics(
    range: str = Query(
        default="30d",
        pattern="^(today|7d|30d|90d|year|custom)$",
        description="Date range preset",
    ),
    start: date | None = Query(default=None, description="Required when range=custom"),
    end: date | None = Query(default=None, description="Required when range=custom"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("analytics.read")),
) -> AnalyticsSummary:
    service = AnalyticsService(db)
    if "seller" in user_role_codes(user):
        seller = _linked_seller(db, user)
        if seller is None:
            return service.empty_dashboard()
        return service.full_dashboard(
            user.effective_organization_id, range, start, end, seller_id=seller.id
        )
    return service.full_dashboard(user.effective_organization_id, range, start, end)
