# RBAC Permission Matrix

The catalog below mirrors `backend/app/services/permissions.py` — the single
source of truth. Permissions are synced into the database on application start
(`ensure_permission_catalog` + `sync_system_role_permissions`).

## Permission catalog (38)

| Code                | Description                              |
| ------------------- | ---------------------------------------- |
| dashboard.read      | View the dashboard                       |
| users.read          | List and view users                      |
| users.create        | Create users                             |
| users.update        | Update users and their roles             |
| users.delete        | Deactivate users                         |
| sellers.read        | List and view sellers                    |
| sellers.create      | Create sellers                           |
| sellers.update      | Update sellers                           |
| sellers.delete      | Deactivate sellers                       |
| products.read       | List and view products                   |
| products.create     | Create products                          |
| products.update     | Update products                          |
| products.delete     | Deactivate products                      |
| customers.read      | List and view customers                  |
| customers.create    | Create customers                         |
| customers.update    | Update customers                         |
| customers.delete    | Delete customers                         |
| orders.read         | List and view orders                     |
| orders.create       | Create orders                            |
| orders.update       | Update order status                      |
| orders.delete       | Cancel orders                            |
| inventory.read      | View inventory                           |
| inventory.update    | Adjust inventory                         |
| analytics.read      | View analytics                           |
| audit.read          | View audit logs                          |
| notifications.read  | View notifications                       |
| suppliers.read      | List and view suppliers                  |
| suppliers.create    | Create suppliers                         |
| suppliers.update    | Update suppliers                         |
| suppliers.delete    | Delete suppliers                         |
| coupons.read        | List and view coupons                    |
| coupons.create      | Create coupons                           |
| coupons.update      | Update coupons                           |
| coupons.delete      | Delete coupons                           |
| settings.read       | View company settings                    |
| settings.update     | Update company settings                  |
| billing.read        | View plan, usage and invoices            |
| billing.manage      | Change the billing plan                  |

## System roles (seeded per organization)

Six system role codes: `owner`, `admin`, `manager`, `seller`, `viewer`
(staff) and `customer` (storefront accounts — no dashboard permissions).

- **owner** and **admin** hold all 38 permissions.
- **manager**: dashboard, sellers (read/create/update), products (full CRUD),
  customers (read/create/update), orders (read/create/update), inventory
  (read/update), analytics, notifications, suppliers (read/create/update),
  coupons (read/create/update), settings.read.
- **seller**: dashboard, sellers.read, products.read, customers.read,
  orders (read/create/update), analytics.read, notifications.read — with
  row-level scoping to their own profile and own orders.
- **viewer**: read-only across dashboard, sellers, products, customers,
  orders, inventory, analytics, notifications.

### Row-level scoping for Sellers

\* Seller sees only their own seller profile (`seller.user_id == current_user.id`).
\*\* Seller lists/creates/updates only orders where `orders.seller_id == own seller id`.

## Enforcement rules

1. **Backend is the only source of truth.** The `require_permissions(...)`
   FastAPI dependency checks the caller's role permissions on every protected
   endpoint. Missing permission → `403 FORBIDDEN` with code `PERMISSION_DENIED`.
2. **Frontend** hides buttons/routes based on `auth.me` permissions — UX only.
3. **Owner** is granted the superset at registration and cannot be deleted
   (`CANNOT_DELETE_OWNER`); an owner account cannot be suspended by an admin.
4. **Owner-only operations**: granting/removing the `owner` role and modifying
   owner accounts (`OWNER_ROLES_RESTRICTED`), changing the company plan,
   transferring ownership and closing the company.
5. Row-level scoping for Sellers is enforced in the repository layer
   (org filter + optional user filter), never by the client.
6. API keys can be issued with any subset of the permission catalog as scopes
   (`ALL_SCOPES` in `app/schemas/api_key.py`) and are enforced the same way.

## Permission → endpoint mapping

See `docs/API.md` — every endpoint table lists the required permission.
