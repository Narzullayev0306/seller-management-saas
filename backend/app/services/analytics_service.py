from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.sale import Sale
from app.models.seller import Seller
from app.schemas.analytics import (
    AnalyticsSummary,
    CategorySales,
    LowStockProduct,
    RecentOrder,
    RevenueComparison,
    SeriesPoint,
    StatusCount,
    SummaryResponse,
    TopItem,
)

RANGES = {
    "today": 1,
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "year": 365,
}


def resolve_range(
    range_key: str, start: date | None = None, end: date | None = None
) -> tuple[datetime, datetime]:
    if range_key == "custom":
        if start is None or end is None:
            raise bad_request(
                "INVALID_RANGE", "Custom range requires both start and end dates"
            )
        if end < start:
            raise bad_request("INVALID_RANGE", "end must be after start")
        return (
            datetime.combine(start, datetime.min.time(), tzinfo=UTC),
            datetime.combine(end, datetime.max.time(), tzinfo=UTC),
        )
    if range_key not in RANGES:
        raise bad_request(
            "INVALID_RANGE", "range must be one of: today, 7d, 30d, 90d, year, custom"
        )
    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=RANGES[range_key])
    return start_dt, end_dt


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        seller_id: UUID | None = None,
    ) -> SummaryResponse:
        order_scope = (
            Order.seller_id == seller_id if seller_id else None
        )

        revenue = self.db.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.organization_id == organization_id,
                Order.status != "cancelled",
                Order.created_at.between(start, end),
                *((order_scope,) if order_scope is not None else ()),
            )
        ).scalar_one()

        orders_count = self.db.execute(
            select(func.count()).select_from(Order).where(
                Order.organization_id == organization_id,
                Order.status != "cancelled",
                Order.created_at.between(start, end),
                *((order_scope,) if order_scope is not None else ()),
            )
        ).scalar_one()

        commission = self.db.execute(
            select(func.coalesce(func.sum(Sale.commission_amount), 0)).where(
                Sale.organization_id == organization_id,
                Sale.created_at.between(start, end),
                *((Sale.seller_id == seller_id,) if seller_id else ()),
            )
        ).scalar_one()

        if seller_id is None:
            products_count = self.db.execute(
                select(func.count()).select_from(Product).where(
                    Product.organization_id == organization_id
                )
            ).scalar_one()
            customers_count = self.db.execute(
                select(func.count()).select_from(Customer).where(
                    Customer.organization_id == organization_id
                )
            ).scalar_one()
            low_stock = self.db.execute(
                select(func.count()).select_from(Product).where(
                    Product.organization_id == organization_id,
                    Product.stock_quantity > 0,
                    Product.stock_quantity <= Product.low_stock_threshold,
                )
            ).scalar_one()
            out_of_stock = self.db.execute(
                select(func.count()).select_from(Product).where(
                    Product.organization_id == organization_id,
                    Product.stock_quantity <= 0,
                )
            ).scalar_one()
        else:
            sold_products = (
                select(OrderItem.product_id)
                .join(Order, Order.id == OrderItem.order_id)
                .where(
                    Order.organization_id == organization_id,
                    Order.seller_id == seller_id,
                    Order.status != "cancelled",
                )
            )
            products_count = self.db.execute(
                select(func.count()).select_from(sold_products.subquery())
            ).scalar_one()
            customers_count = self.db.execute(
                select(func.count(func.distinct(Order.customer_id)))
                .select_from(Order)
                .where(
                    Order.organization_id == organization_id,
                    Order.seller_id == seller_id,
                    Order.status != "cancelled",
                )
            ).scalar_one()
            low_stock = self.db.execute(
                select(func.count()).select_from(Product).where(
                    Product.organization_id == organization_id,
                    Product.id.in_(sold_products),
                    Product.stock_quantity > 0,
                    Product.stock_quantity <= Product.low_stock_threshold,
                )
            ).scalar_one()
            out_of_stock = self.db.execute(
                select(func.count()).select_from(Product).where(
                    Product.organization_id == organization_id,
                    Product.id.in_(sold_products),
                    Product.stock_quantity <= 0,
                )
            ).scalar_one()

        active_sellers = self.db.execute(
            select(func.count()).select_from(Seller).where(
                Seller.organization_id == organization_id,
                Seller.status == "active",
            )
        ).scalar_one()

        avg_order_value = (
            Decimal(revenue) / Decimal(orders_count) if orders_count else Decimal("0")
        )

        return SummaryResponse(
            revenue=Decimal(revenue).quantize(Decimal("0.01")),
            orders_count=int(orders_count),
            products_count=int(products_count),
            customers_count=int(customers_count),
            active_sellers=int(active_sellers),
            low_stock_products=int(low_stock),
            out_of_stock_products=int(out_of_stock),
            avg_order_value=avg_order_value.quantize(Decimal("0.01")),
            total_commission=Decimal(commission).quantize(Decimal("0.01")),
        )

    def daily_series(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        expression,
        seller_id: UUID | None = None,
    ) -> list[SeriesPoint]:
        rows = self.db.execute(
            select(
                func.date_trunc("day", Order.created_at).label("day"),
                expression.label("value"),
            )
            .where(
                Order.organization_id == organization_id,
                Order.status != "cancelled",
                Order.created_at.between(start, end),
                *((Order.seller_id == seller_id,) if seller_id else ()),
            )
            .group_by("day")
            .order_by("day")
        ).all()
        return [SeriesPoint(date=row.day.strftime("%Y-%m-%d"), value=Decimal(row.value)) for row in rows]

    def revenue_over_time(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        seller_id: UUID | None = None,
    ) -> list[SeriesPoint]:
        return self.daily_series(
            organization_id, start, end, func.coalesce(func.sum(Order.total), 0), seller_id
        )

    def orders_over_time(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        seller_id: UUID | None = None,
    ) -> list[SeriesPoint]:
        return self.daily_series(organization_id, start, end, func.count(), seller_id)

    def top_products(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        limit: int = 5,
        seller_id: UUID | None = None,
    ) -> list[TopItem]:
        rows = self.db.execute(
            select(
                Product.id,
                Product.name,
                func.coalesce(func.sum(OrderItem.subtotal), 0),
                func.count(func.distinct(Order.id)),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Product.organization_id == organization_id,
                Order.organization_id == organization_id,
                Order.status != "cancelled",
                Order.created_at.between(start, end),
                *((Order.seller_id == seller_id,) if seller_id else ()),
            )
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderItem.subtotal).desc())
            .limit(limit)
        ).all()
        return [
            TopItem(id=str(r.id), name=r.name, value=Decimal(r[2]), orders=int(r[3]))
            for r in rows
        ]

    def top_sellers(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        limit: int = 5,
        seller_id: UUID | None = None,
    ) -> list[TopItem]:
        rows = self.db.execute(
            select(
                Seller.id,
                func.concat(Seller.first_name, " ", Seller.last_name),
                func.coalesce(func.sum(Order.total), 0),
                func.count(func.distinct(Order.id)),
            )
            .join(Order, Order.seller_id == Seller.id)
            .where(
                Seller.organization_id == organization_id,
                Order.organization_id == organization_id,
                Order.status != "cancelled",
                Order.created_at.between(start, end),
                *((Order.seller_id == seller_id,) if seller_id else ()),
            )
            .group_by(Seller.id, Seller.first_name, Seller.last_name)
            .order_by(func.sum(Order.total).desc())
            .limit(limit)
        ).all()
        return [
            TopItem(id=str(r.id), name=str(r[1]), value=Decimal(r[2]), orders=int(r[3]))
            for r in rows
        ]

    def sales_by_category(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        seller_id: UUID | None = None,
    ) -> list[CategorySales]:
        rows = self.db.execute(
            select(
                Product.category,
                func.coalesce(func.sum(OrderItem.subtotal), 0),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Product.organization_id == organization_id,
                Order.organization_id == organization_id,
                Order.status != "cancelled",
                Order.created_at.between(start, end),
                *((Order.seller_id == seller_id,) if seller_id else ()),
            )
            .group_by(Product.category)
            .order_by(func.sum(OrderItem.subtotal).desc())
        ).all()
        return [
            CategorySales(category=r.category, value=Decimal(r[1])) for r in rows
        ]

    def recent_orders(
        self,
        organization_id: UUID,
        seller_id: UUID | None = None,
        limit: int = 6,
    ) -> list[RecentOrder]:
        rows = self.db.execute(
            select(
                Order.id,
                Order.order_number,
                func.concat(Customer.first_name, " ", Customer.last_name),
                Order.total,
                Order.status,
                Order.created_at,
            )
            .join(Customer, Customer.id == Order.customer_id)
            .where(
                Order.organization_id == organization_id,
                Order.status != "cancelled",
                *((Order.seller_id == seller_id,) if seller_id else ()),
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        ).all()
        return [
            RecentOrder(
                id=str(r.id),
                order_number=r.order_number,
                customer_name=str(r[2]),
                total=Decimal(r.total).quantize(Decimal("0.01")),
                status=r.status,
                created_at=r.created_at,
            )
            for r in rows
        ]

    def low_stock_products(
        self,
        organization_id: UUID,
        seller_id: UUID | None = None,
        limit: int = 6,
    ) -> list[LowStockProduct]:
        stmt = (
            select(
                Product.id,
                Product.name,
                Product.sku,
                Product.stock_quantity,
                Product.low_stock_threshold,
            )
            .where(
                Product.organization_id == organization_id,
                Product.stock_quantity > 0,
                Product.stock_quantity <= Product.low_stock_threshold,
            )
            .order_by(Product.stock_quantity.asc())
            .limit(limit)
        )
        if seller_id is not None:
            sold = select(OrderItem.product_id).join(Order, Order.id == OrderItem.order_id).where(
                Order.organization_id == organization_id,
                Order.seller_id == seller_id,
                Order.status != "cancelled",
            )
            stmt = stmt.where(Product.id.in_(sold))
        rows = self.db.execute(stmt).all()
        return [
            LowStockProduct(
                id=str(r.id),
                name=r.name,
                sku=r.sku,
                stock_quantity=int(r.stock_quantity),
                low_stock_threshold=int(r.low_stock_threshold),
            )
            for r in rows
        ]

    def status_distribution(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        seller_id: UUID | None = None,
    ) -> list[StatusCount]:
        rows = self.db.execute(
            select(Order.status, func.count())
            .where(
                Order.organization_id == organization_id,
                Order.created_at.between(start, end),
                *((Order.seller_id == seller_id,) if seller_id else ()),
            )
            .group_by(Order.status)
            .order_by(func.count().desc())
        ).all()
        return [StatusCount(status=r.status, count=int(r[1])) for r in rows]

    def revenue_comparison(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        seller_id: UUID | None = None,
    ) -> RevenueComparison:
        span = end - start
        prev_start = start - span
        scope = (Order.seller_id == seller_id) if seller_id else None

        def _revenue(from_dt: datetime, to_dt: datetime) -> Decimal:
            return Decimal(
                self.db.execute(
                    select(func.coalesce(func.sum(Order.total), 0)).where(
                        Order.organization_id == organization_id,
                        Order.status != "cancelled",
                        Order.created_at.between(from_dt, to_dt),
                        *((scope,) if scope is not None else ()),
                    )
                ).scalar_one()
            ).quantize(Decimal("0.01"))

        current = _revenue(start, end)
        previous = _revenue(prev_start, start)
        if previous > 0:
            change = ((current - previous) / previous * 100).quantize(Decimal("0.1"))
        else:
            change = Decimal("100") if current > 0 else Decimal("0")
        return RevenueComparison(
            current=current, previous=previous, change_percent=change
        )

    def empty_dashboard(self) -> AnalyticsSummary:
        return AnalyticsSummary(
            summary=SummaryResponse(
                revenue=Decimal("0").quantize(Decimal("0.01")),
                orders_count=0,
                products_count=0,
                customers_count=0,
                active_sellers=0,
                low_stock_products=0,
                out_of_stock_products=0,
                avg_order_value=Decimal("0").quantize(Decimal("0.01")),
                total_commission=Decimal("0").quantize(Decimal("0.01")),
            ),
            revenue_over_time=[],
            orders_over_time=[],
            top_products=[],
            top_sellers=[],
            sales_by_category=[],
            recent_orders=[],
            low_stock_products=[],
            status_distribution=[],
            revenue_comparison=RevenueComparison(
                current=Decimal("0"), previous=Decimal("0"), change_percent=Decimal("0")
            ),
        )

    def full_dashboard(
        self,
        organization_id: UUID,
        range_key: str,
        start: date | None,
        end: date | None,
        seller_id: UUID | None = None,
    ) -> AnalyticsSummary:
        start_dt, end_dt = resolve_range(range_key, start, end)
        return AnalyticsSummary(
            summary=self.get_summary(organization_id, start_dt, end_dt, seller_id),
            revenue_over_time=self.revenue_over_time(organization_id, start_dt, end_dt, seller_id),
            orders_over_time=self.orders_over_time(organization_id, start_dt, end_dt, seller_id),
            top_products=self.top_products(organization_id, start_dt, end_dt, seller_id=seller_id),
            top_sellers=self.top_sellers(organization_id, start_dt, end_dt, seller_id=seller_id),
            sales_by_category=self.sales_by_category(organization_id, start_dt, end_dt, seller_id),
            recent_orders=self.recent_orders(organization_id, seller_id),
            low_stock_products=self.low_stock_products(organization_id, seller_id),
            status_distribution=self.status_distribution(organization_id, start_dt, end_dt, seller_id),
            revenue_comparison=self.revenue_comparison(organization_id, start_dt, end_dt, seller_id),
        )
