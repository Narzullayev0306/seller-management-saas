# API Endpoint Plan

Base URL: `/api/v1` — all endpoints require `Authorization: Bearer <access_token>`
except the public auth endpoints (register, login, refresh, logout, forgot/reset
password, verify email, accept invite). OpenAPI docs at `/docs` (backend root).

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

## Auth (public)

| Method | Path              | Summary                                             |
| ------ | ----------------- | --------------------------------------------------- |
| POST   | /auth/register    | Create org + owner user, returns tokens             |
| POST   | /auth/login       | Login with email/password, returns tokens           |
| POST   | /auth/refresh     | Rotate refresh token                                |
| POST   | /auth/logout      | Revoke current refresh token                        |
| GET    | /auth/me          | Current user + roles + permissions + verification status |
| POST   | /auth/forgot-password | Request password reset email (public)               |
| POST   | /auth/reset-password  | Set new password with one-time token (public)       |
| POST   | /auth/verify-email    | Verify email with one-time token (public)           |
| POST   | /auth/resend-verification | Resend verification email (public)              |
| GET    | /auth/memberships     | Organizations the caller belongs to (org switcher)  |
| POST   | /auth/switch-org      | Re-issue tokens scoped to another member organization |

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
| PUT    | /users/{id}/roles        | users.update     | Replace role assignments (owner role only changeable by owner) |
| DELETE | /users/{id}              | users.delete     | Hard-delete invited users, otherwise suspend |

## Sellers

| Method | Path              | Permissions    | Summary                              |
| ------ | ----------------- | -------------- | ------------------------------------ |
| GET    | /sellers          | sellers.read   | List (status filter, search)         |
| POST   | /sellers          | sellers.create | Create                               |
| GET    | /sellers/{id}     | sellers.read   | Detail                               |
| GET    | /sellers/{id}/stats | sellers.read | Stats + recent orders + performance |
| PATCH  | /sellers/{id}     | sellers.update | Update                               |
| DELETE | /sellers/{id}     | sellers.delete | Deactivate                           |

## Products

| Method | Path              | Permissions     | Summary                                     |
| ------ | ----------------- | --------------- | ------------------------------------------- |
| GET    | /products         | products.read   | List (category/status/stock filters)        |
| POST   | /products         | products.create | Create (stock via initial movement)         |
| GET    | /products/{id}    | products.read   | Detail                                      |
| PATCH  | /products/{id}    | products.update | Update (stock via adjustment movement)      |
| DELETE | /products/{id}    | products.delete | Deactivate                                  |

## Customers

| Method | Path               | Permissions     | Summary                      |
| ------ | ------------------ | --------------- | ---------------------------- |
| GET    | /customers         | customers.read  | List (search)                |
| POST   | /customers         | customers.create| Create                       |
| GET    | /customers/{id}    | customers.read  | Detail + order history       |
| PATCH  | /customers/{id}    | customers.update| Update                       |
| DELETE | /customers/{id}    | customers.delete| Delete                       |

## Suppliers

| Method | Path              | Permissions      | Summary                        |
| ------ | ----------------- | ---------------- | ------------------------------ |
| GET    | /suppliers        | suppliers.read   | List (status filter, search)   |
| POST   | /suppliers        | suppliers.create | Create                         |
| GET    | /suppliers/{id}   | suppliers.read   | Detail                         |
| PATCH  | /suppliers/{id}   | suppliers.update | Update                         |
| DELETE | /suppliers/{id}   | suppliers.delete | Delete                         |

## Orders

| Method | Path                   | Permissions    | Summary                                   |
| ------ | ---------------------- | -------------- | ----------------------------------------- |
| GET    | /orders                | orders.read    | List (status/payment/seller/customer/date filters) |
| POST   | /orders                | orders.create  | Create order (transactional, stock check, shipping fee, payment status) |
| GET    | /orders/{id}           | orders.read    | Detail + items + creator                  |
| PATCH  | /orders/{id}           | orders.update  | Update status (delivered/cancel hooks)    |
| PATCH  | /orders/{id}/payment   | orders.update  | Update payment status                     |
| GET    | /orders/{id}/history   | orders.read    | Chronological order timeline              |
| DELETE | /orders/{id}           | orders.delete  | Cancel + restore stock                    |

Business rules:
- Items must reference valid products of the same organization.
- Stock must be sufficient (except when `allow_backorder` false → 409 `INSUFFICIENT_STOCK`).
- Subtotal = Σ qty × unit_price; total = subtotal − discount + tax + shipping_fee;
  discount must be ≤ subtotal; tax can be a percent or amount (client sends amount).
- Payment status flow: `pending` → `paid` / `partially_paid` → `refunded`.
- Status transitions: any → any, but `delivered` finalizes the sale,
  `cancelled` restores stock and reverses the sale.
- Every order creation/status/payment change is recorded in `audit_logs` and shown
  in `/orders/{id}/history`.

## Inventory

| Method | Path                           | Permissions      | Summary                             |
| ------ | ------------------------------ | ---------------- | ----------------------------------- |
| GET    | /inventory                     | inventory.read   | Stock overview (filters, low/out)   |
| GET    | /inventory/movements           | inventory.read   | Movement history (product filter)   |
| POST   | /inventory/adjustments         | inventory.update | Manual adjust (purchase/adjustment) |

Movement types: `purchase` (+, from suppliers), `adjustment` (±, manual),
`return` (+, order cancelled), `sale` (−, internal only).

## Analytics

All under `analytics.read`, common param `range=today|7d|30d|90d|year|custom`
(+ `start`, `end` when `custom`).

| Method | Path                               | Summary                          |
| ------ | ---------------------------------- | -------------------------------- |
| GET    | /analytics/summary                 | Revenue, orders, products, customers, active sellers, low stock |
| GET    | /analytics/revenue-over-time       | Daily revenue series             |
| GET    | /analytics/orders-over-time        | Daily orders series              |
| GET    | /analytics/top-products            | Top N by revenue (default 5)     |
| GET    | /analytics/top-sellers             | Top N sellers by revenue         |
| GET    | /analytics/sales-by-category       | Revenue per category             |
| GET    | /analytics/dashboard               | All of the above plus widgets: `recent_orders` (6), `low_stock_products` (6), `status_distribution`, `revenue_comparison` (current vs previous period + change %) |

All analytics exclude cancelled orders; revenue = sum of non-cancelled order
totals (or `sales.amount` for finalized ones — see ERD rule; summary uses
non-cancelled orders for "revenue" and `sales` for commissions).

## Notifications

| Method | Path                            | Permissions       | Summary                        |
| ------ | ------------------------------- | ----------------- | ------------------------------ |
| GET    | /notifications                  | notifications.read| List (unread_only filter)      |
| GET    | /notifications/unread-count     | notifications.read| Unread count (bell badge)      |
| PATCH  | /notifications/{id}/read        | notifications.read| Mark one as read               |
| PATCH  | /notifications/read-all         | notifications.read| Mark all as read               |

Notification types: `low_stock`, `order.created`, `order.cancelled`,
`team.invited`, `ownership_transferred`. Only one unread `low_stock` per product.

## Organizations

| Method | Path                            | Permissions     | Summary                                  |
| ------ | ------------------------------- | --------------- | ---------------------------------------- |
| GET    | /organizations/me               | settings.read   | Company settings (logo, currency, tz...) |
| PATCH  | /organizations/me               | settings.update | Update company settings                  |
| PATCH  | /organizations/me/plan          | owner only      | Change plan (free/pro/enterprise)        |
| POST   | /organizations/me/transfer-ownership | owner only | Give owner role to another active member |
| POST   | /organizations/me/close         | owner only      | Soft-delete company; locks all members out |

## Audit Logs

| Method | Path         | Permissions | Summary                  |
| ------ | ------------ | ----------- | ------------------------ |
| GET    | /audit-logs  | audit.read  | List (user/action filters) |

## HTTP status codes used

`200` OK · `201` Created · `204` No Content · `400` Bad Request ·
`401` Unauthorized · `403` Forbidden · `404` Not Found · `409` Conflict ·
`422` Validation Error · `500` Internal Server Error