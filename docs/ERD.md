# Database Design (ERD)

PostgreSQL. Every table uses `UUID` primary keys (`uuid_generate_v4` via
`gen_random_uuid()`), plus `created_at` / `updated_at` timestamps
(`timestamptz`).

## Entities

```
organizations
├── id            UUID PK
├── name          varchar(100) UNIQUE
├── slug          varchar(100) UNIQUE
├── plan          varchar(20) default 'free'   [free | pro | enterprise]
├── is_active     boolean default true
├── created_at / updated_at

users
├── id            UUID PK
├── organization_id  UUID FK → organizations (NOT NULL, indexed)
├── email         varchar(255) UNIQUE (global unique — email identifies account)
├── full_name     varchar(150)
├── password_hash varchar(255)
├── is_active     boolean default true
├── email_verified boolean default false
├── status        varchar(20)  [active | invited | suspended]
├── created_at / updated_at

roles                              (system roles, seeded per organization)
├── id            UUID PK
├── organization_id  UUID FK → organizations (NOT NULL)
├── name          varchar(50)
├── code          varchar(50)      [owner | admin | manager | seller | viewer]
├── is_system     boolean default true
├── UNIQUE (organization_id, code)

permissions                        (global catalog)
├── id            UUID PK
├── code          varchar(100) UNIQUE   e.g. products.create
├── description   varchar(255)

role_permissions
├── id            UUID PK
├── role_id       UUID FK → roles (ON DELETE CASCADE)
├── permission_id UUID FK → permissions (ON DELETE CASCADE)
├── UNIQUE (role_id, permission_id)

user_roles
├── id            UUID PK
├── user_id       UUID FK → users (ON DELETE CASCADE)
├── role_id       UUID FK → roles (ON DELETE CASCADE)
├── UNIQUE (user_id, role_id)

sellers
├── id            UUID PK
├── organization_id  UUID FK (NOT NULL, indexed)
├── user_id       UUID FK → users (nullable — links a seller to a user account)
├── first_name    varchar(100)
├── last_name     varchar(100)
├── email         varchar(255) (nullable)
├── phone         varchar(30)  (nullable)
├── status        varchar(20)  [active | inactive | suspended]
├── commission_rate numeric(5,2) default 0   (percent, 0–100)
├── total_sales   numeric(14,2) default 0    (denormalized, maintained by service)
├── total_orders  integer default 0          (denormalized)
├── created_at / updated_at
├── UNIQUE (organization_id, email)  (when email not null)

products
├── id            UUID PK
├── organization_id  UUID FK (NOT NULL, indexed)
├── category_id   UUID FK → categories (nullable)
├── brand_id      UUID FK → brands (nullable)
├── name          varchar(200)
├── sku           varchar(50)
├── description   text (nullable)
├── category      varchar(100)  (legacy free-text label kept for filters)
├── price         numeric(14,2)  CHECK (price >= 0)
├── cost_price    numeric(14,2)  CHECK (cost_price >= 0)
├── stock_quantity integer      CHECK (stock_quantity >= 0)
├── low_stock_threshold integer default 10
├── status        varchar(20)   [active | inactive]
├── image_url     varchar (nullable)
├── featured      boolean default false
├── created_at / updated_at
├── UNIQUE (organization_id, sku)

customers
├── id            UUID PK
├── organization_id  UUID FK (NOT NULL, indexed)
├── first_name / last_name  varchar(100)
├── email         varchar(255) (nullable)
├── phone         varchar(30)  (nullable)
├── address       text         (nullable)
├── total_orders  integer default 0
├── total_spent   numeric(14,2) default 0
├── created_at / updated_at
├── UNIQUE (organization_id, email)  (when email not null)

orders
├── id            UUID PK
├── organization_id  UUID FK (NOT NULL, indexed)
├── order_number  varchar(30)
├── seller_id     UUID FK → sellers (nullable)
├── customer_id   UUID FK → customers (NOT NULL)
├── created_by    UUID FK → users (nullable)
├── status        varchar(20)  [pending | confirmed | processing | shipped | delivered | cancelled]
├── payment_status varchar(20) [pending | paid | partially_paid | refunded]
├── subtotal      numeric(14,2)
├── discount      numeric(14,2) default 0
├── tax           numeric(14,2) default 0
├── shipping_fee  numeric(14,2) default 0
├── total         numeric(14,2)
├── created_at / updated_at
├── UNIQUE (organization_id, order_number)

order_items
├── id            UUID PK
├── order_id      UUID FK → orders (ON DELETE CASCADE)
├── product_id    UUID FK → products
├── product_variant_id UUID FK → product_variants (nullable)
├── quantity      integer CHECK (quantity > 0)
├── unit_price    numeric(14,2)
├── subtotal      numeric(14,2)  (quantity * unit_price)
├── created_at

inventory_movements
├── id            UUID PK
├── organization_id  UUID FK (NOT NULL, indexed)
├── product_id    UUID FK → products
├── type          varchar(20)  [purchase | sale | adjustment | return]
├── quantity      integer      (positive for in, negative for out — stored signed)
├── reason        varchar(255) (nullable)
├── reference_id  UUID         (nullable — links to order/adjustment doc)
├── created_at
├── INDEX (organization_id, product_id, created_at)

sales
├── id            UUID PK
├── organization_id  UUID FK (NOT NULL, indexed)
├── order_id      UUID FK → orders (UNIQUE — one sale per order)
├── seller_id     UUID FK → sellers (nullable)
├── customer_id   UUID FK → customers
├── amount        numeric(14,2)
├── commission_amount numeric(14,2) default 0
├── created_at

refresh_tokens
├── id            UUID PK
├── user_id       UUID FK → users (ON DELETE CASCADE)
├── token_hash    varchar(64) UNIQUE   (SHA-256 of the raw token)
├── family_id     UUID          (rotation family — reuse detection)
├── replaced_by   UUID (nullable — next token in the family)
├── created_ip / user_agent (session metadata)
├── expires_at    timestamptz
├── revoked_at    timestamptz (nullable)
├── created_at

audit_logs
├── id            UUID PK
├── organization_id  UUID FK (NOT NULL, indexed)
├── user_id       UUID FK → users
├── action        varchar(50)   e.g. login, order.created
├── entity_type   varchar(50)   e.g. product, order, user
├── entity_id     UUID (nullable)
├── meta          JSONB (nullable)
├── created_at
├── INDEX (organization_id, created_at DESC)

## Additional tables (grouped)

### Multi-tenant membership & settings

organization_members — user ↔ organization N:M with role_code + status;
powers the org switcher (`/auth/memberships`, `/auth/switch-org`).

categories — org-scoped tree: name, slug, parent_id (self-FK), position,
is_active.

brands, product_images, reviews, price_history, back_in_stock_requests —
storefront merchandising around products.

product_variants — org+product scoped SKU variants: attributes JSONB, price,
cost_price, stock_quantity, active.

shipping_methods — org-scoped delivery options (name, fee, zone, active).

coupons — code, discount_type/percent|fixed, discount_value, min_subtotal,
max_redemptions, max_per_customer, starts/expires, redemptions counter.
coupon_redemptions — coupon × order/customer with discount_amount.

suppliers — org-scoped vendors feeding purchase orders.

purchase_orders (+ purchase_order_items) — supplier POs with status machine
draft → ordered → received/cancelled; receiving writes inventory movements.

payments — per-order payment records: provider, provider_payment_id, amount,
currency, status, paid_at, failure_message.

return_requests — storefront return flow per order item
(requested → approved/rejected → received → completed).
refunds — manual/provider refunds per order (amount, status, processed_at).

### Platform & reliability

outbox_events — transactional outbox: event_type, aggregate, payload JSONB,
attempts, last_error, processed_at. Dispatched by `app/worker.py`.

idempotency_keys — Idempotency-Key guard for checkout: key, request_hash,
status, response snapshot, expires_at.

notifications — in-app alerts (low_stock, order.created/cancelled,
team.invited, ownership_transferred) with read tracking.
notification_preferences — per-user channel/type toggles.

webhook_endpoints + webhook_deliveries — outbound webhooks (URL, secret,
events, active) and signed delivery attempts with response codes.

api_keys — hashed machine tokens with permission-scope list, expiry,
last_used_at.

subscriptions + invoices — billing plans (free/pro/enterprise), usage limits
and invoice rows.

organization_domains — custom storefront domains with verification state.

auth_tokens — one-time email action tokens (verify, reset, invite), hashed.

customer_refresh_tokens + customer_accounts — storefront customer accounts
(separate from staff users) with their own rotating refresh-token sessions.

carts + cart_items, wishlists + wishlist_items — server-side carts/wishlists
keyed by customer account or guest session_token.
```

## Relationships

- Organization 1─N Users, Members, Sellers, Products, Categories, Customers,
  Orders, Movements, Sales, AuditLogs, Roles, Suppliers, Coupons,
  ShippingMethods, Webhooks, ApiKeys, Domains, Notifications
- User 1─N RefreshTokens / AuthTokens; User N─M Roles (via user_roles);
  User N─M Organizations (via organization_members)
- Role N─M Permission (via role_permissions)
- Seller N─1 User (optional); Order N─1 Seller (optional)
- Order 1─N OrderItems · Order 1─N Payments/Refunds/ReturnRequests ·
  Order 1─1 Sale; OrderItem N─1 Product (or ProductVariant)
- Product 1─N InventoryMovements · Variants · Images · Reviews;
  Category self-referencing tree; Brand 1─N Products
- CustomerAccount 1─N Carts/Wishlists/CustomerRefreshTokens

## Denormalization strategy

`sellers.total_sales / total_orders` and `customers.total_orders / total_spent`
are maintained inside the same transaction that creates/updates orders, so they
never drift. `products.stock_quantity` is maintained by inventory movements in
the same transaction.

## Sales lifecycle rule

- Order created → stock decremented (movement `sale`), no sale record yet.
- Order status → `delivered` → `sales` row created (amount = order total,
  commission = total × seller commission_rate); seller/customer counters updated.
- Order status → `cancelled` → stock restored (movement `return`), sale row
  deleted, counters rolled back.

All of this runs in a single transaction per order-status change.