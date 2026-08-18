from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    audit_logs,
    auth,
    coupons,
    customers,
    inventory,
    notifications,
    orders,
    organizations,
    products,
    roles,
    sellers,
    storefront,
    suppliers,
    uploads,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(sellers.router)
api_router.include_router(products.router)
api_router.include_router(customers.router)
api_router.include_router(orders.router)
api_router.include_router(inventory.router)
api_router.include_router(analytics.router)
api_router.include_router(audit_logs.router)
api_router.include_router(storefront.router)
api_router.include_router(storefront.legacy_router)
api_router.include_router(uploads.router)
api_router.include_router(notifications.router)
api_router.include_router(organizations.router)
api_router.include_router(suppliers.router)
api_router.include_router(coupons.router)
