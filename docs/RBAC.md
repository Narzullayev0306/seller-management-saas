# RBAC Permission Matrix

## Permission catalog

| Code                | Description                          |
| ------------------- | ------------------------------------ |
| dashboard.read      | View dashboard                       |
| users.read/create/update/delete   | Manage users            |
| sellers.read/create/update/delete | Manage sellers          |
| products.read/create/update/delete | Manage products        |
| customers.read/create/update/delete | Manage customers      |
| orders.read/create/update/delete | Manage orders           |
| inventory.read/update          | View/adjust inventory     |
| analytics.read     | View analytics                     |
| audit.read         | View audit logs                    |

## System roles (seeded per organization)

| Permission            | Owner | Admin | Manager | Seller | Viewer |
| --------------------- | :---: | :---: | :-----: | :----: | :----: |
| dashboard.read        |  ✓    |  ✓    |   ✓     |   ✓    |   ✓    |
| users.read            |  ✓    |  ✓    |   –     |   –    |   –    |
| users.create          |  ✓    |  ✓    |   –     |   –    |   –    |
| users.update          |  ✓    |  ✓    |   –     |   –    |   –    |
| users.delete          |  ✓    |  –    |   –     |   –    |   –    |
| sellers.read          |  ✓    |  ✓    |   ✓     |   ✓*   |   ✓    |
| sellers.create        |  ✓    |  ✓    |   ✓     |   –    |   –    |
| sellers.update        |  ✓    |  ✓    |   ✓     |   –    |   –    |
| sellers.delete        |  ✓    |  ✓    |   –     |   –    |   –    |
| products.read         |  ✓    |  ✓    |   ✓     |   ✓    |   ✓    |
| products.create       |  ✓    |  ✓    |   ✓     |   –    |   –    |
| products.update       |  ✓    |  ✓    |   ✓     |   –    |   –    |
| products.delete       |  ✓    |  ✓    |   ✓     |   –    |   –    |
| customers.read        |  ✓    |  ✓    |   ✓     |   ✓    |   ✓    |
| customers.create      |  ✓    |  ✓    |   ✓     |   –    |   –    |
| customers.update      |  ✓    |  ✓    |   ✓     |   –    |   –    |
| customers.delete      |  ✓    |  ✓    |   –     |   –    |   –    |
| orders.read           |  ✓    |  ✓    |   ✓     |   ✓**  |   ✓    |
| orders.create         |  ✓    |  ✓    |   ✓     |   ✓**  |   –    |
| orders.update         |  ✓    |  ✓    |   ✓     |   ✓**  |   –    |
| orders.delete         |  ✓    |  ✓    |   –     |   –    |   –    |
| inventory.read        |  ✓    |  ✓    |   ✓     |   –    |   ✓    |
| inventory.update      |  ✓    |  ✓    |   ✓     |   –    |   –    |
| analytics.read        |  ✓    |  ✓    |   ✓     |   –    |   ✓    |
| audit.read            |  ✓    |  ✓    |   –     |   –    |   –    |

\* Seller sees only own profile data (row-level scoping to `seller.user_id == current_user.id`).
\*\* Seller sees/creates/updates only orders where `orders.seller_id == own seller id`.

## Enforcement rules

1. **Backend is the only source of truth.** The `require_permissions(...)`
   FastAPI dependency checks the caller's role permissions on every protected
   endpoint. Missing permission → `403 FORBIDDEN` with code `PERMISSION_DENIED`.
2. **Frontend** hides buttons/routes based on `auth.me` permissions — UX only.
3. **Owner** is granted the superset at registration and cannot be deleted.
4. Admin cannot delete users (only Owner can) and cannot delete sellers —
   separation of destructive powers.
5. Row-level scoping for Sellers is enforced in the repository layer
   (org filter + optional user filter), never by the client.

## Permission → endpoint mapping

See `docs/API.md` — every endpoint table lists the required permission.