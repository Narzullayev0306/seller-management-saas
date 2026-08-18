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
├── name          varchar(200)
├── sku           varchar(50)
├── description   text (nullable)
├── category      varchar(100)
├── price         numeric(14,2)  CHECK (price >= 0)
├── cost_price    numeric(14,2)  CHECK (cost_price >= 0)
├── stock_quantity integer      CHECK (stock_quantity >= 0)
├── low_stock_threshold integer default 10
├── status        varchar(20)   [active | inactive]
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
├── status        varchar(20)  [pending | confirmed | processing | shipped | delivered | cancelled]
├── subtotal      numeric(14,2)
├── discount      numeric(14,2) default 0
├── tax           numeric(14,2) default 0
├── total         numeric(14,2)
├── created_at / updated_at
├── UNIQUE (organization_id, order_number)

order_items
├── id            UUID PK
├── order_id      UUID FK → orders (ON DELETE CASCADE)
├── product_id    UUID FK → products
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
├── metadata      JSONB (nullable)
├── created_at
├── INDEX (organization_id, created_at DESC)
```

## Relationships

- Organization 1─N Users, Sellers, Products, Customers, Orders, Movements, Sales, AuditLogs, Roles
- User 1─N RefreshTokens; User N─M Roles (via user_roles)
- Role N─M Permission (via role_permissions)
- Seller N─1 User (optional); Order N─1 Seller (optional)
- Order 1─N OrderItems; Order 1─1 Sale; OrderItem N─1 Product
- Product 1─N InventoryMovements

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