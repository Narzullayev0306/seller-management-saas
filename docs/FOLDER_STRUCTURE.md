# Folder Structure

Monorepo with two applications (`backend/`, `frontend/`), an E2E suite
(`e2e/`) and infrastructure/config at the root.

```
seller-management-saas/
├── README.md · CHANGELOG.md · DEPLOYMENT.md · LICENSE
├── .env.example              # template — real secrets never committed
├── docker-compose.yml        # dev stack: postgres, redis, migrate, backend,
│                             # worker, frontend
├── docker-compose.prod.yml   # prod stack (+ caddy reverse proxy)
├── deploy/Caddyfile          # TLS termination / proxy rules
├── .github/workflows/        # ci.yml · e2e.yml · security.yml (CodeQL)
│
├── backend/
│   ├── Dockerfile · pyproject.toml · alembic.ini
│   ├── api/index.py          # Vercel serverless entrypoint
│   ├── alembic/versions/     # 20 revisions (schema → ... → categories)
│   ├── app/
│   │   ├── main.py           # app factory, CORS, middleware, error handlers,
│   │   │                     # health endpoints, Sentry (optional)
│   │   ├── api/
│   │   │   ├── router.py     # aggregates all v1 routers under /api/v1
│   │   │   ├── deps.py       # get_db, get_current_user, require_permissions,
│   │   │   │                 # require_owner, api-key auth
│   │   │   └── v1/           # 24 routers + public_api:
│   │   │       # auth, users, roles, sellers, products, categories, customers,
│   │   │       # orders, inventory, analytics, audit_logs, storefront,
│   │   │       # uploads, notifications, organizations, suppliers, coupons,
│   │   │       # shipping_methods, refunds, purchase_orders, webhooks,
│   │   │       # api_keys, billing, domains
│   │   ├── core/             # config, security (bcrypt/JWT), exceptions,
│   │   │                     # middleware (request-id, security headers),
│   │   │                     # ratelimit, redis client
│   │   ├── db/               # session, base, seed CLI (python -m app.db.seed)
│   │   ├── models/           # 33 SQLAlchemy models: organization, user, role,
│   │   │                     # seller, product, product_variant, category,
│   │   │                     # customer(_account), order, payment, refund,
│   │   │                     # inventory, purchase_order, supplier, sale,
│   │   │                     # coupon, shipping_method, cart, wishlist,
│   │   │                     # notification(_preference), webhook, api_key,
│   │   │                     # billing, domain, outbox, idempotency,
│   │   │                     # refresh_token, auth_token, audit_log, ...
│   │   ├── repositories/     # org-scoped data access; base.py forces the
│   │   │                     # organization_id filter on every query
│   │   ├── schemas/          # Pydantic v2 request/response models
│   │   └── services/         # business logic: order_service +
│   │                         # order_state_machine, inventory, payment(+_providers),
│   │                         # coupon, cart, wishlist, storefront,
│   │                         # customer_auth, category, purchase_order,
│   │                         # refund, shipping/domain/billing/webhook/api_key,
│   │                         # notification(+preferences), email, storage,
│   │                         # outbox, idempotency, permissions/rbac,
│   │                         # auth_token (sessions), audit
│   ├── app/worker.py         # python -m app.worker — outbox dispatcher
│   └── tests/                # pytest suite — 228 tests incl. isolation & RBAC
│
├── frontend/
│   ├── Dockerfile · Dockerfile.prod · next.config.ts · proxy.ts
│   ├── instrumentation*.ts · sentry.server.config.ts   # optional Sentry
│   ├── app/
│   │   ├── layout.tsx · globals.css · page.tsx
│   │   ├── (auth)/           # login, register, verify-email, accept-invite,
│   │   │                     # forgot/reset password
│   │   ├── dashboard/        # overview, products, categories, customers,
│   │   │                     # orders, inventory, reports, sellers, users,
│   │   │                     # marketing (coupons), shipping, refunds,
│   │   │                     # purchase-orders, webhooks, api-keys, billing,
│   │   │                     # settings, audit
│   │   ├── storefront/       # public per-org store: catalog, product, cart,
│   │   │                     # checkout, account (orders), auth pages
│   │   ├── contact/ · terms/ · privacy/
│   ├── components/ui|storefront   # shadcn/ui kit + storefront components
│   ├── lib/                  # api-client (fetch + token refresh), use-api,
│   │                         # use-list, types, format, storefront-slug
│   └── public/               # static assets
│
├── e2e/                      # Playwright: auth, products, orders, storefront
├── docker/postgres.init.sql  # uuid extension
└── docs/                     # ARCHITECTURE · API · ERD · RBAC ·
                              # FOLDER_STRUCTURE · PHASES (+ assets)
```

## Rationale

- **api → services → repositories → models**: dependency direction is strictly
  inward; HTTP concerns never leak into data access.
- **Repositories own tenancy**: the org filter is applied in `repositories/base.py`,
  so services cannot accidentally issue cross-tenant queries.
- **Services own transactions**: multi-table invariants (order + stock + sale +
  outbox) are committed or rolled back as one unit.
- **Frontend `lib/api-client`** is the single fetch wrapper: token injection,
  one automatic refresh+retry on 401, typed helpers.
