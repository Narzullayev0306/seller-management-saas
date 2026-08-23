from __future__ import annotations

from dataclasses import dataclass

PERMISSIONS: dict[str, str] = {
    "dashboard.read": "View the dashboard",
    "users.read": "List and view users",
    "users.create": "Create users",
    "users.update": "Update users and their roles",
    "users.delete": "Deactivate users",
    "sellers.read": "List and view sellers",
    "sellers.create": "Create sellers",
    "sellers.update": "Update sellers",
    "sellers.delete": "Deactivate sellers",
    "products.read": "List and view products",
    "products.create": "Create products",
    "products.update": "Update products",
    "products.delete": "Deactivate products",
    "customers.read": "List and view customers",
    "customers.create": "Create customers",
    "customers.update": "Update customers",
    "customers.delete": "Delete customers",
    "orders.read": "List and view orders",
    "orders.create": "Create orders",
    "orders.update": "Update order status",
    "orders.delete": "Cancel orders",
    "inventory.read": "View inventory",
    "inventory.update": "Adjust inventory",
    "analytics.read": "View analytics",
    "audit.read": "View audit logs",
    "notifications.read": "View notifications",
    "suppliers.read": "List and view suppliers",
    "suppliers.create": "Create suppliers",
    "suppliers.update": "Update suppliers",
    "suppliers.delete": "Delete suppliers",
    "coupons.read": "List and view coupons",
    "coupons.create": "Create coupons",
    "coupons.update": "Update coupons",
    "coupons.delete": "Delete coupons",
    "settings.read": "View company settings",
    "settings.update": "Update company settings",
    "billing.read": "View plan, usage and invoices",
    "billing.manage": "Change the billing plan",
}

SYSTEM_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "owner": list(PERMISSIONS.keys()),
    "admin": list(PERMISSIONS.keys()),
    "manager": [
        "dashboard.read",
        "sellers.read",
        "sellers.create",
        "sellers.update",
        "products.read",
        "products.create",
        "products.update",
        "products.delete",
        "customers.read",
        "customers.create",
        "customers.update",
        "orders.read",
        "orders.create",
        "orders.update",
        "inventory.read",
        "inventory.update",
        "analytics.read",
        "notifications.read",
        "suppliers.read",
        "suppliers.create",
        "suppliers.update",
        "coupons.read",
        "coupons.create",
        "coupons.update",
        "settings.read",
    ],
    "seller": [
        "dashboard.read",
        "sellers.read",
        "products.read",
        "customers.read",
        "orders.read",
        "orders.create",
        "orders.update",
        "analytics.read",
        "notifications.read",
    ],
    "viewer": [
        "dashboard.read",
        "sellers.read",
        "products.read",
        "customers.read",
        "orders.read",
        "inventory.read",
        "analytics.read",
        "notifications.read",
    ],
    "customer": [],
}

SYSTEM_ROLE_NAMES: dict[str, str] = {
    "owner": "Owner",
    "admin": "Admin",
    "manager": "Manager",
    "seller": "Seller",
    "viewer": "Viewer",
    "customer": "Customer",
}


@dataclass(frozen=True)
class RoleCode:
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    SELLER = "seller"
    VIEWER = "viewer"
    CUSTOMER = "customer"
