from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    revenue: Decimal
    orders_count: int
    products_count: int
    customers_count: int
    active_sellers: int
    low_stock_products: int
    out_of_stock_products: int
    avg_order_value: Decimal
    total_commission: Decimal


class SeriesPoint(BaseModel):
    date: str
    value: Decimal


class TopItem(BaseModel):
    id: str
    name: str
    value: Decimal
    orders: int = 0


class CategorySales(BaseModel):
    category: str
    value: Decimal


class RecentOrder(BaseModel):
    id: str
    order_number: str
    customer_name: str
    total: Decimal
    status: str
    created_at: datetime


class LowStockProduct(BaseModel):
    id: str
    name: str
    sku: str
    stock_quantity: int
    low_stock_threshold: int


class StatusCount(BaseModel):
    status: str
    count: int


class RevenueComparison(BaseModel):
    current: Decimal
    previous: Decimal
    change_percent: Decimal


class AnalyticsSummary(BaseModel):
    summary: SummaryResponse
    revenue_over_time: list[SeriesPoint]
    orders_over_time: list[SeriesPoint]
    top_products: list[TopItem]
    top_sellers: list[TopItem]
    sales_by_category: list[CategorySales]
    recent_orders: list[RecentOrder]
    low_stock_products: list[LowStockProduct]
    status_distribution: list[StatusCount]
    revenue_comparison: RevenueComparison
