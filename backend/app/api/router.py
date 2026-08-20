from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    api_keys,
    audit_logs,
    auth,
    billing,
    categories,
    coupons,
    customers,
    domains,
    inventory,
    notifications,
    orders,
    organizations,
    products,
    public_api,
    purchase_orders,
    refunds,
    roles,
    sellers,
    shipping_methods,
    storefront,
    suppliers,
    uploads,
    users,
    webhooks,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(sellers.router)
api_router.include_router(products.router)
api_router.include_router(categories.router)
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
api_router.include_router(shipping_methods.router)
api_router.include_router(refunds.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(webhooks.router)
api_router.include_router(api_keys.router)
api_router.include_router(billing.router)
api_router.include_router(domains.router)
api_router.include_router(public_api.router)
