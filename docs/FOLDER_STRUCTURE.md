# Folder Structure

```
seller-management-saas/
├── README.md
├── .env.example
├── docker-compose.yml
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                  # app factory, CORS, exception handlers, router mount
│   │   ├── api/
│   │   │   ├── router.py            # aggregates all v1 routers
│   │   │   ├── deps.py              # get_db, get_current_user, require_permissions
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── sellers.py
│   │   │       ├── products.py
│   │   │       ├── customers.py
│   │   │       ├── orders.py
│   │   │       ├── inventory.py
│   │   │       ├── analytics.py
│   │   │       └── audit_logs.py
│   │   ├── core/
│   │   │   ├── config.py            # pydantic-settings (env)
│   │   │   ├── security.py          # bcrypt, JWT create/decode
│   │   │   └── exceptions.py        # domain errors + error codes
│   │   ├── db/
│   │   │   ├── base.py              # DeclarativeBase + naming convention
│   │   │   ├── session.py           # engine, sessionmaker, get_db
│   │   │   └── seed.py              # demo seed data (CLI entry)
│   │   ├── models/                  # SQLAlchemy 2.0 mapped classes
│   │   │   ├── organization.py
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── seller.py
│   │   │   ├── product.py
│   │   │   ├── customer.py
│   │   │   ├── order.py
│   │   │   ├── inventory.py
│   │   │   ├── sale.py
│   │   │   └── audit_log.py
│   │   ├── repositories/            # org-scoped data access
│   │   │   ├── base.py              # org-scoped query helpers + pagination
│   │   │   ├── user_repo.py
│   │   │   ├── seller_repo.py
│   │   │   ├── product_repo.py
│   │   │   ├── customer_repo.py
│   │   │   ├── order_repo.py
│   │   │   ├── inventory_repo.py
│   │   │   └── analytics_repo.py
│   │   ├── schemas/                 # Pydantic v2
│   │   │   ├── common.py            # Page, error envelope, sort/filter params
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── seller.py
│   │   │   ├── product.py
│   │   │   ├── customer.py
│   │   │   ├── order.py
│   │   │   ├── inventory.py
│   │   │   ├── analytics.py
│   │   │   └── audit.py
│   │   ├── services/
│   │   │   ├── auth_service.py      # register/login/refresh/logout
│   │   │   ├── order_service.py     # transactional order lifecycle
│   │   │   ├── inventory_service.py # movements, adjustments
│   │   │   ├── analytics_service.py # summary + series
│   │   │   ├── audit_service.py     # log action helper
│   │   │   └── rbac_service.py      # permission resolution
│   │   └── utils/
│   │       └── datetime.py          # UTC helpers
│   └── tests/
│       ├── conftest.py              # test DB (postgres), fixtures, factories
│       ├── test_auth.py
│       ├── test_rbac.py
│       ├── test_org_isolation.py
│       ├── test_products.py
│       ├── test_sellers.py
│       ├── test_customers.py
│       ├── test_orders.py
│       ├── test_inventory.py
│       ├── test_analytics.py
│       ├── test_validation.py
│       └── test_pagination.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── components.json              # shadcn/ui config
│   ├── public/
│   ├── app/
│   │   ├── layout.tsx               # root layout + providers
│   │   ├── globals.css
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   └── (dashboard)/
│   │       ├── layout.tsx           # sidebar + topbar shell
│   │       ├── page.tsx             # redirect → /dashboard
│   │       ├── dashboard/page.tsx
│   │       ├── sellers/page.tsx
│   │       ├── sellers/[id]/page.tsx
│   │       ├── products/page.tsx
│   │       ├── products/[id]/page.tsx
│   │       ├── customers/page.tsx
│   │       ├── customers/[id]/page.tsx
│   │       ├── orders/page.tsx
│   │       ├── orders/[id]/page.tsx
│   │       ├── inventory/page.tsx
│   │       ├── analytics/page.tsx
│   │       ├── users/page.tsx
│   │       ├── audit/page.tsx
│   │       └── settings/page.tsx
│   ├── components/
│   │   ├── ui/                      # shadcn/ui primitives (button, input, dialog…)
│   │   ├── layout/                  # sidebar.tsx, topbar.tsx, user-menu.tsx
│   │   ├── data-table/              # data-table.tsx, pagination.tsx
│   │   └── shared/                  # stat-card, chart-card, confirm-dialog,
│   │                                # empty-state, loading-state, error-state,
│   │                                # search-input, filter-dropdown, page-header
│   ├── features/
│   │   ├── auth/                    # login-form, register-form
│   │   ├── products/                # product-form, product-filters, product-table
│   │   ├── sellers/
│   │   ├── customers/
│   │   ├── orders/                  # order-form (line items), order-table
│   │   ├── inventory/
│   │   ├── users/
│   │   └── audit/
│   ├── hooks/                       # use-debounce, use-range-options
│   ├── lib/
│   │   ├── api-client.ts            # fetch wrapper + token refresh
│   │   ├── query-client.ts
│   │   ├── auth-store.ts            # token persistence
│   │   └── utils.ts                 # cn(), formatters
│   ├── providers/                   # query-provider, auth-provider
│   ├── schemas/                     # zod schemas per entity
│   ├── services/                    # auth.ts, users.ts, sellers.ts, products.ts,
│   │                                # customers.ts, orders.ts, inventory.ts,
│   │                                # analytics.ts, audit.ts
│   └── types/                       # API types mirroring backend schemas
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ERD.md
│   ├── API.md
│   ├── RBAC.md
│   ├── PHASES.md
│   └── FOLDER_STRUCTURE.md
│
└── docker/
    ├── postgres.init.sql            # enable uuid extension
    └── (optional extra docker files)
```