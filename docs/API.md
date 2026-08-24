# API Endpoint Plan

Base URL: `/api/v1` — all endpoints require `Authorization: Bearer <access_token>`
except the public auth endpoints (register, login, refresh, logout, forgot/reset
password, verify email, accept invite) and the public storefront endpoints.
OpenAPI docs at `/docs` (backend root).

## Routers (24 + public)

auth · users · roles · sellers · suppliers · products · categories · customers ·
orders · inventory · analytics · audit-logs · storefront (+ legacy alias) ·
uploads · notifications · organizations · coupons · shipping-methods ·
refunds/returns · purchase-orders · webhooks · api-keys · billing · domains ·
public (API-key).

## Conventions

- **List endpoints** support common query params:
  `page` (1-based, default 1), `page_size` (default 20, max 100),
  `search`, `sort_by`, `sort_order` (`asc|desc`), plus entity-specific filters.
- **List response envelope**:

```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 57,
  "total_pages": 3
}
```

- **Error envelope** (all 4xx/5xx):

```json
{ "success": false, "error": { "code": "PRODUCT_NOT_FOUND", "message": "Product not found", "details": {} } }
```

- Sort fields are whitelisted per resource; unknown columns → 422.

## Auth

All public except `/me`, `/sessions*` and `/change-password` (token required).

| Method | Path                       | Summary                                              |
| ------ | -------------------------- | ---------------------------------------------------- |
| POST   | /auth/register             | Create org + owner user, returns tokens              |
| POST   | /auth/login                | Login with email/password, returns tokens            |
| POST   | /auth/refresh              | Rotate refresh token                                 |
| POST   | /auth/logout               | Revoke current refresh token                         |
| GET    | /auth/me                   | Current user + roles + permissions + verification status |
| POST   | /auth/switch-org           | Re-issue tokens scoped to another member organization |
| GET    | /auth/memberships          | Organizations the caller belongs to (org switcher)   |
| GET    | /auth/sessions             | List active sessions (devices) for the current user  |
| DELETE | /auth/sessions/{id}        | Revoke a specific session                            |
| POST   | /auth/sessions/revoke-others | Revoke all sessions except the current one         |
| POST   | /auth/forgot-password      | Request password reset email (public)                |
| POST   | /auth/reset-password       | Set new password with one-time token (public)        |
| POST   | /auth/change-password      | Change password for the authenticated user           |
| POST   | /auth/verify-email         | Verify email with one-time token (public)            |
| POST   | /auth/resend-verification  | Resend verification email (public)                   |

## Users

| Method | Path                     | Permissions      | Summary                     |
| ------ | ------------------------ | ---------------- | --------------------------- |
| GET    | /users                   | users.read       | List (search/sort/page, status filter) |
| POST   | /users                   | users.create     | Create user + roles         |
| POST   | /users/invite            | users.create     | Invite by email (one-time accept link) |
| POST   | /users/invites/accept    | public           | Accept invite, set name + password |
| POST   | /users/invites/resend    | users.create     | Re-send invite email (invited status only) |
| GET    | /users/{id}              | users.read       | Get user                    |
| PATCH  | /users/{id}              | users.update     | Update profile/active/status |
| PUT    | /users/{id}/roles        | users.update     | Replace role assignments (owner role changeable by owner only — `OWNER_ROLES_RESTRICTED`) |
| DELETE | /users/{id}              | users.delete     | Hard-delete invited users, otherwise suspend (owner accounts cannot be deleted) |

## Roles

| Method | Path        | Permissions | Summary                          |
| ------ | ----------- | ----------- | -------------------------------- |
| GET    | /roles/matrix | users.read | Role → permission matrix for the org |

## Sellers

| Method | Path                | Permissions    | Summary                              |
| ------ | ------------------- | -------------- | ------------------------------------ |
| GET    | /sellers            | sellers.read   | List (status filter, search)         |
| POST   | /sellers            | sellers.create | Create                               |
| GET    | /sellers/{id}       | sellers.read   | Detail                               |
| GET    | /sellers/{id}/stats | sellers.read   | Stats + recent orders + performance  |
| PATCH  | /sellers/{id}       | sellers.update | Update                               |
| DELETE | /sellers/{id}       | sellers.delete | Deactivate                           |

## Products

Product variants are managed through the create/update payloads.

| Method | Path                 | Permissions     | Summary                                     |
| ------ | -------------------- | --------------- | ------------------------------------------- |
| GET    | /products            | products.read   | List (category/status/stock filters)        |
| GET    | /products/categories | products.read   | Distinct category list for filters          |
| POST   | /products            | products.create | Create (stock via initial movement)         |
| GET    | /products/{id}       | products.read   | Detail                                      |
| PATCH  | /products/{id}       | products.update | Update (stock via adjustment movement)      |
| DELETE | /products/{id}       | products.delete | Deactivate                                  |

## Categories

| Method | Path                | Permissions     | Summary                        |
| ------ | ------------------- | --------------- | ------------------------------ |
| GET    | /categories/tree    | products.read   | Nested category tree           |
| GET    | /categories         | products.read   | Flat list (active only)        |
| POST   | /categories         | products.create | Create                         |
| GET    | /categories/{id}    | products.read   | Get                            |
| PATCH  | /categories/{id}    | products.update | Update                         |
| DELETE | /categories/{id}    | products.delete | Delete (must have no children or products) |

## Customers

| Method | Path                | Permissions      | Summary                      |
| ------ | ------------------- | ---------------- | ---------------------------- |
| GET    | /customers          | customers.read   | List (search)                |
| POST   | /customers          | customers.create | Create                       |
| GET    | /customers/{id}     | customers.read   | Detail + order history       |
| PATCH  | /customers/{id}     | customers.update | Update                       |
| DELETE | /customers/{id}     | customers.delete | Delete                       |

## Suppliers

| Method | Path               | Permissions      | Summary                        |
| ------ | ------------------ | ---------------- | ------------------------------ |
| GET    | /suppliers         | suppliers.read   | List (status filter, search)   |
| POST   | /suppliers         | suppliers.create | Create                         |
| GET    | /suppliers/{id}    | suppliers.read   | Detail                         |
| PATCH  | /suppliers/{id}    | suppliers.update | Update                         |
| DELETE | /suppliers/{id}    | suppliers.delete | Delete                         |

## Orders

| Method | Path                    | Permissions   | Summary                                   |
| ------ | ----------------------- | ------------- | ----------------------------------------- |
| GET    | /orders                 | orders.read   | List (status/payment/seller/customer/date filters) |
| POST   | /orders                 | orders.create | Create order (transactional, stock check, coupon, shipping fee, payment status) |
| GET    | /orders/{id}            | orders.read   | Detail + items + payments + creator       |
| PATCH  | /orders/{id}            | orders.update | Update status (delivered/cancel hooks)    |
| DELETE | /orders/{id}            | orders.delete | Cancel + restore stock                    |
| PATCH  | /orders/{id}/payment    | orders.update | Update payment status                     |
| GET    | /orders/{id}/payments   | orders.read   | Payment records for the order             |
| GET    | /orders/{id}/history    | orders.read   | Chronological order timeline              |

Business rules:
- Items must reference valid products of the same organization.
- Stock must be sufficient (otherwise 409 `INSUFFICIENT_STOCK`);
  inventory rows are locked with `SELECT … FOR UPDATE`.
- Subtotal = Σ qty × unit_price; total = subtotal − discount + tax + shipping_fee;
  discount must be ≤ subtotal; coupons are validated and applied server-side.
- Payment status flow: `pending` → `paid` / `partially_paid` → `refunded`.
- Status transitions follow the state machine
  (`pending → confirmed → processing → shipped → delivered / cancelled`);
  `delivered` finalizes the sale + commission, `cancelled` restores stock
  and reverses the sale.
- Every order creation/status/payment change is recorded in `audit_logs`
  and shown in `/orders/{id}/history`.

## Inventory

| Method | Path                   | Permissions      | Summary                             |
| ------ | ---------------------- | ---------------- | ----------------------------------- |
| GET    | /inventory             | inventory.read   | Stock overview (filters, low/out)   |
| GET    | /inventory/movements   | inventory.read   | Movement history (product filter)   |
| POST   | /inventory/adjustments | inventory.update | Manual adjust (purchase/adjustment) |

Movement types: `purchase` (+, from suppliers), `adjustment` (±, manual),
`return` (+, order cancelled), `sale` (−, internal only).

## Purchase Orders

| Method | Path                  | Permissions      | Summary                                    |
| ------ | --------------------- | ---------------- | ------------------------------------------ |
| GET    | /purchase-orders      | inventory.read   | List                                       |
| POST   | /purchase-orders      | inventory.update | Create draft                               |
| GET    | /purchase-orders/{id} | inventory.read   | Detail                                     |
| PATCH  | /purchase-orders/{id} | inventory.update | Order / receive / cancel (receive adds stock movements) |
| DELETE | /purchase-orders/{id} | inventory.update | Delete draft or ordered PO                 |

## Returns & Refunds

| Method | Path                      | Permissions    | Summary                                        |
| ------ | ------------------------- | -------------- | ---------------------------------------------- |
| GET    | /returns                  | orders.read    | List return requests                           |
| PATCH  | /returns/{id}             | orders.update  | Approve / reject / receive / complete a return |
| GET    | /refunds                  | orders.read    | List refunds                                   |
| POST   | /refunds                  | orders.update  | Create manual refund for an order              |
| PATCH  | /refunds/{id}             | orders.update  | Mark refund processed / failed                 |

## Coupons

| Method | Path               | Permissions    | Summary                    |
| ------ | ------------------ | -------------- | -------------------------- |
| GET    | /coupons           | coupons.read   | List                       |
| POST   | /coupons           | coupons.create | Create                     |
| GET    | /coupons/validate  | coupons.read   | Validate against a cart    |
| GET    | /coupons/{id}      | coupons.read   | Get                        |
| PATCH  | /coupons/{id}      | coupons.update | Update                     |
| DELETE | /coupons/{id}      | coupons.delete | Delete                     |

## Shipping Methods

Settings-scoped (`settings.read` / `settings.update`).

| Method | Path                    | Permissions     | Summary        |
| ------ | ----------------------- | --------------- | -------------- |
| GET    | /shipping-methods       | settings.read   | List           |
| POST   | /shipping-methods       | settings.update | Create         |
| GET    | /shipping-methods/{id}  | settings.read   | Get            |
| PATCH  | /shipping-methods/{id}  | settings.update | Update         |
| DELETE | /shipping-methods/{id}  | settings.update | Delete         |

## Analytics

Permission: `analytics.read`. Common param `range=today|7d|30d|90d|year|custom`
(+ `start`, `end` when `custom`).

| Method | Path                 | Summary                          |
| ------ | -------------------- | -------------------------------- |
| GET    | /analytics/dashboard | Full dashboard payload: summary metrics, revenue/orders series, top products/sellers, recent orders, low stock, status distribution, period comparison |

All analytics exclude cancelled orders; revenue = sum of non-cancelled order
totals (or `sales.amount` for finalized ones — see ERD rule; summary uses
non-cancelled orders for "revenue" and `sales` for commissions).

## Notifications

| Method | Path                          | Permissions        | Summary                        |
| ------ | ----------------------------- | ------------------ | ------------------------------ |
| GET    | /notifications                | notifications.read | List (unread_only filter)      |
| GET    | /notifications/unread-count   | notifications.read | Unread count (bell badge)      |
| PATCH  | /notifications/{id}/read      | notifications.read | Mark one as read               |
| PATCH  | /notifications/read-all       | notifications.read | Mark all as read               |
| GET    | /notifications/preferences    | notifications.read | Get notification preferences   |
| PUT    | /notifications/preferences    | notifications.read | Update notification preferences|

Notification types: `low_stock`, `order.created`, `order.cancelled`,
`team.invited`, `ownership_transferred`. Only one unread `low_stock` per product.

## Organizations

| Method | Path                                 | Permissions     | Summary                                  |
| ------ | ------------------------------------ | --------------- | ---------------------------------------- |
| GET    | /organizations/me                    | settings.read   | Company settings (logo, currency, tz...) |
| PATCH  | /organizations/me                    | settings.update | Update company settings                  |
| PATCH  | /organizations/me/plan               | owner only      | Change plan (free/pro/enterprise)        |
| POST   | /organizations/me/transfer-ownership | owner only      | Give owner role to another active member |
| POST   | /organizations/me/close              | owner only      | Soft-delete company; locks all members out |

## Audit Logs

| Method | Path         | Permissions | Summary                  |
| ------ | ------------ | ----------- | ------------------------ |
| GET    | /audit-logs  | audit.read  | List (user/action filters) |

## Uploads

| Method | Path                 | Permissions     | Summary                                          |
| ------ | -------------------- | --------------- | ------------------------------------------------ |
| POST   | /uploads/signed-url  | products.update | Signed upload URL for Supabase Storage (images)  |

## Webhooks

Outbound webhooks with HMAC signatures; settings-scoped.

| Method | Path                            | Permissions     | Summary                              |
| ------ | ------------------------------- | --------------- | ------------------------------------ |
| GET    | /webhooks                       | settings.read   | List webhook endpoints               |
| POST   | /webhooks                       | settings.update | Create webhook endpoint              |
| GET    | /webhooks/{id}                  | settings.read   | Get endpoint                         |
| PATCH  | /webhooks/{id}                  | settings.update | Update endpoint                      |
| DELETE | /webhooks/{id}                  | settings.update | Delete endpoint                      |
| POST   | /webhooks/{id}/test             | settings.update | Send a signed test ping              |
| GET    | /webhooks/{id}/deliveries       | settings.read   | Delivery history (status, response)  |

## API Keys

Machine-to-machine access; keys are hashed, scoped to permission subsets and
can expire. Settings-scoped management.

| Method | Path                | Permissions     | Summary                                            |
| ------ | ------------------- | --------------- | -------------------------------------------------- |
| GET    | /api-keys           | settings.read   | List API keys                                      |
| POST   | /api-keys           | settings.update | Create key (returns the raw secret exactly once)   |
| PATCH  | /api-keys/{id}      | settings.update | Rename, change scopes, activate/revoke, set expiry |
| DELETE | /api-keys/{id}      | settings.update | Delete key                                         |

## Billing

| Method | Path                  | Permissions    | Summary                                |
| ------ | --------------------- | -------------- | -------------------------------------- |
| GET    | /billing/plans        | billing.read   | List available plans                   |
| GET    | /billing/summary      | billing.read   | Current plan, usage and limits         |
| POST   | /billing/change-plan  | owner only     | Change the organization plan           |
| GET    | /billing/invoices     | billing.read   | List invoices                          |

## Domains

Custom storefront domains; settings-scoped.

| Method | Path                      | Permissions     | Summary            |
| ------ | ------------------------- | --------------- | ------------------ |
| GET    | /domains                  | settings.read   | List custom domains|
| POST   | /domains                  | settings.update | Add a domain       |
| POST   | /domains/{id}/verify      | settings.update | Verify ownership   |
| DELETE | /domains/{id}             | settings.update | Remove domain      |

## Storefront (public)

Two aliases: current `/api/v1/stores/{slug}/…` and deprecated
`/api/v1/storefront/…` (default store). No dashboard token required;
customer-account routes use storefront customer tokens issued by the store.

Catalog & content:

| Method | Path                                  | Summary                                |
| ------ | ------------------------------------- | -------------------------------------- |
| GET    | /stores/{slug}/info                   | Storefront metadata                    |
| GET    | /stores/{slug}/catalog                | Public product catalog (search/filter) |
| GET    | /stores/{slug}/products/{id}          | Public product detail                  |
| GET    | /stores/{slug}/brands                 | Brands with product counts             |
| GET    | /stores/{slug}/categories             | Categories with product counts         |
| GET    | /stores/{slug}/shipping-methods       | Active shipping methods                |

Checkout & customer:

| Method | Path                                  | Summary                                |
| ------ | ------------------------------------- | -------------------------------------- |
| POST   | /stores/{slug}/checkout               | Guest/customer checkout (idempotent via `Idempotency-Key`) |
| POST   | /stores/{slug}/auth/register          | Register a customer account            |
| POST   | /stores/{slug}/auth/login             | Customer login                         |
| POST   | /stores/{slug}/auth/refresh           | Rotate customer refresh token          |
| POST   | /stores/{slug}/auth/logout            | Customer logout                        |
| GET/PATCH | /stores/{slug}/auth/me             | Customer profile read/update           |
| GET    | /stores/{slug}/auth/orders            | Orders placed by this customer account |

Cart, wishlist & after-sales:

| Method | Path                                       | Summary                        |
| ------ | ------------------------------------------ | ------------------------------ |
| GET    | /stores/{slug}/cart                        | Read cart                      |
| POST   | /stores/{slug}/cart/items                  | Add item                       |
| PATCH  | /stores/{slug}/cart/items/{item_id}        | Update quantity                |
| DELETE | /stores/{slug}/cart/items/{item_id}        | Remove item                    |
| DELETE | /stores/{slug}/cart                        | Clear cart                     |
| GET    | /stores/{slug}/wishlist                    | Read wishlist                  |
| POST   | /stores/{slug}/wishlist/items              | Add item                       |
| DELETE | /stores/{slug}/wishlist/items/{item_id}    | Remove item                    |
| DELETE | /stores/{slug}/wishlist                    | Clear wishlist                 |
| GET/POST | /stores/{slug}/returns                   | List / request returns         |
| POST   | /stores/{slug}/products/{id}/reviews       | Submit a product review        |
| POST   | /stores/{slug}/products/{id}/back-in-stock | Back-in-stock notification opt-in |

## Public API (API key)

Authenticated with an API key (see API Keys above), not a user token.

| Method | Path                        | Summary                    |
| ------ | --------------------------- | -------------------------- |
| GET    | /public/products            | List products              |
| GET    | /public/products/{id}       | Product detail             |
| GET    | /public/inventory           | Stock overview             |

## System health

Outside `/api/v1`: `GET /api/health` (liveness+name),
`GET /api/health/live`, `GET /api/health/ready` (database + Redis checks,
returns 503 when degraded). Every response carries an `X-Request-Id` header.

## HTTP status codes used

`200` OK · `201` Created · `204` No Content · `400` Bad Request ·
`401` Unauthorized · `403` Forbidden · `404` Not Found · `409` Conflict ·
`422` Validation Error · `500` Internal Server Error
