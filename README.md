# Seller Management SaaS

A full-stack, multi-tenant seller management platform: companies (organizations) manage
sellers, products, customers, orders, inventory and sales analytics behind a role-based
access control system — with a complete audit trail.

Built as a portfolio-grade monorepo: **Next.js 16 (App Router, TypeScript, Tailwind)**
frontend, **FastAPI (Python 3.13, SQLAlchemy 2.0, Alembic, Pydantic v2)** backend and
**PostgreSQL**, orchestrated with **Docker Compose**.

## Features

- **Authentication** — register (creates organization + owner), login, logout; bcrypt
  password hashing; short-lived JWT access tokens (15 min) with rotating, hashed,
  revocable refresh tokens.
- **Account security** — email verification on registration (with resend), forgot /
  reset password flows, and email-based team invitations: invitees receive a link
  and set their own password (no shared credentials). All links are one-time tokens.
  Emails are sent via SMTP when configured, and logged to the console otherwise.
  Email dispatch runs as FastAPI background tasks so responses never wait on SMTP.
- **Team management** — invite members with a role, change roles inline
  (owner-protected), resend invitations, remove invited members (hard delete) or
  suspend/reactivate active ones.
- **Multi-organization** — users can belong to several organizations
  (`organization_members`) and switch between them from the sidebar; each session
  is scoped to one organization via the JWT `org` claim, and every query is
  filtered by the active organization.
- **In-app notifications** — low-stock alerts, new orders, cancelled orders and team
  invitations delivered to a notification bell (unread badge, mark read / mark all
  read); permission-gated per role.
- **Authorization** — 5 built-in roles (`owner`, `admin`, `manager`, `seller`, `viewer`)
  over a permission catalog (32 permissions); server-enforced via FastAPI dependencies
  and mirrored in the UI (menus/buttons hidden without permission).
- **Multi-tenant isolation** — every tenant-owned table carries `organization_id`;
  the tenant is derived from the JWT, never from the request; all repository queries
  are forced to filter by organization.
- **Core domains** — products (categories, stock status), customers, sellers
  (commission rates), suppliers (company directory with status), orders with line
  items and a transactional lifecycle (pending → confirmed → processing → shipped →
  delivered / cancelled) that decrements stock on confirmation and restores it on
  cancellation, and records sales + commission on delivery. Orders track payment
  status (pending / paid / partially paid / refunded), shipping fees and the
  responsible user, with a per-order history timeline.
- **Inventory** — stock levels, movements log (purchase / sale / adjustment),
  manual adjustments with audit trail.
- **Company settings** — organization profile (name, logo, contact details, currency,
  timezone) editable from the dashboard by users with the settings permission.
- **Billing & ownership** — owner-only plan selection (free / pro / enterprise),
  ownership transfer to another active member, and a type-to-confirm "close
  company" flow that locks every member out (soft-delete).
- **Analytics dashboard** — revenue, orders, avg order value, customers, commission,
  daily revenue/orders series, top products and top sellers, with range presets
  (today / 7d / 30d / 90d / year) — plus live widgets: recent orders, low-stock
  products, order status distribution (donut) and revenue vs previous period
  comparison.
- **Audit log** — every meaningful action is recorded (who, what, entity, meta, when).
- **Validation** — backend (Pydantic patterns, max lengths, formats) and frontend
  (form validation before submit, field-level errors).
- **Error handling** — consistent JSON error envelope and correct HTTP status codes:
  `400` bad request, `401` unauthorized, `403` forbidden, `404` not found,
  `422` validation, `500` internal.
- **UI states** — loading skeletons/spinners, empty states, error states with
  retry, processing states on buttons, toast notifications.
- **List UX** — search, pagination (never loads all records), filtering
  (status / category / stock status / type) and sorting on every list page.
- **Responsive** — desktop sidebar layout collapses to a mobile drawer;
  tables and toolbars adapt to tablet and phone widths.
- **Security** — password hashing (bcrypt), JWT security, rotating refresh tokens,
  CORS restricted to the frontend origin, input validation everywhere,
  SQL injection protection via SQLAlchemy parameterized queries, secrets only in
  environment variables (never committed).
- **Logging** — backend structured request logging plus an in-app audit log.
- **Docker** — `docker compose up` runs frontend, backend and PostgreSQL;
  `docker-compose.prod.yml` + `Dockerfile.prod` deploy production builds
  (see `DEPLOYMENT.md`).
- **Database security** — Alembic migration ships Supabase row-level-security
  policies on every org-scoped table (`auth.uid()`-based, applied only where the
  Supabase `auth` schema exists); defense-in-depth under the service-role app user.

## Architecture

```
┌──────────────────────┐         ┌──────────────────────────────────────┐
│   Next.js Frontend   │  HTTP   │   FastAPI Backend                   │
│   App Router, RSC    │  JSON   │   /api/v1/*                         │
│   - Auth pages       │ ──────▶ │   ├─ API layer (routers, deps)      │
│   - Dashboard shell  │         │   ├─ Service layer (business logic) │
│   - Domain CRUD      │         │   ├─ Repository layer (data access) │
│   - proxy.ts guard   │         │   └─ Models (SQLAlchemy ORM)        │
└──────────────────────┘         └─────────────────┬────────────────────┘
                                                   │ SQLAlchemy
                                          ┌────────▼────────┐
                                          │    PostgreSQL    │
                                          │  (multi-tenant)  │
                                          └─────────────────┘
```

Layering is strict and dependency direction is inward:

```
api → services → repositories → models/db
```

Key decisions:

- **Tenancy**: organization_id derived from the JWT; repository base class forces the
  filter, making cross-tenant reads structurally impossible.
- **Transactions**: order creation (items + stock decrement), delivery (sale + commission)
  and cancellation (stock restore) run in single DB transactions.
- **Auth**: access token in memory (15 min) + refresh token rotation with revocation;
  frontend mirrors the session in a cookie used by `proxy.ts` for optimistic route
  guarding; real authorization is always enforced server-side.

## Tech Stack

| Layer       | Technology                                              |
| ----------- | ------------------------------------------------------- |
| Frontend    | Next.js 16, React 19, TypeScript, Tailwind CSS 4        |
| Backend     | Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Database    | PostgreSQL 16 (uuid PKs, indexes, constraints)          |
| Security    | bcrypt, PyJWT, CORS                                     |
| Testing     | pytest + httpx (backend, 122 tests), ESLint + tsc (frontend) |
| Infra       | Docker Compose (frontend + backend + postgres)          |

## Installation

### Prerequisites

- Docker + Docker Compose (recommended path)
- Or: Python 3.13+ and Node.js 20+ (local path)

### Docker (recommended)

```bash
git clone <repo-url> seller-management-saas
cd seller-management-saas

cp .env.example .env          # optional, defaults work out of the box
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- API docs (Swagger UI): http://localhost:8000/docs

The backend automatically runs Alembic migrations on start. The database is seeded
with realistic demo data the first time you log in (see "Demo accounts" below).

### Local development (no Docker)

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
set DATABASE_URL=postgresql+psycopg://seller:seller_dev_password@localhost:5432/seller_management
alembic upgrade head
python -m app.db.seed --if-empty
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

All secrets live in environment variables — nothing is hardcoded. See `.env.example`:

| Variable                     | Default                               | Description                          |
| ---------------------------- | ------------------------------------- | ------------------------------------ |
| `POSTGRES_USER`              | `seller`                              | Postgres user                        |
| `POSTGRES_PASSWORD`          | `seller_dev_password`                 | Postgres password (change in prod)   |
| `POSTGRES_DB`                | `seller_management`                   | Postgres database name               |
| `DATABASE_URL`               | `postgresql+psycopg://seller:...`     | SQLAlchemy connection string         |
| `JWT_SECRET`                 | `dev-secret-change-me`                | JWT signing secret (change in prod)  |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15`                              | Access token lifetime                |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7`                                | Refresh token lifetime               |
| `FRONTEND_URL`               | `http://localhost:3000`               | Allowed CORS origin                  |
| `NEXT_PUBLIC_API_URL`        | `http://localhost:8000/api/v1`        | Frontend → backend base URL          |
| `SMTP_HOST`                  | *(unset)*                             | SMTP server for outgoing email       |
| `SMTP_PORT`                  | `587`                                 | SMTP port (465 for implicit TLS)     |
| `SMTP_USER`                  | *(unset)*                             | SMTP username                        |
| `SMTP_PASSWORD`              | *(unset)*                             | SMTP password                        |
| `SMTP_FROM`                  | `no-reply@example.com`                | From address for emails              |
| `SMTP_USE_TLS`               | `true`                                | Use STARTTLS (false → implicit TLS)  |
| `EMAIL_ENABLED`              | `false`                               | Send emails; when false, emails are  |
|                              |                                       | logged to the backend console        |

## Demo Accounts

The seed creates one demo organization with five users (one per role):

| Role    | Email               | Password       |
| ------- | ------------------- | -------------- |
| Owner   | `owner@techmart.uz` | `DemoPass123!` |
| Admin   | `admin@techmart.uz` | `AdminPass123!` |
| Manager | `manager@techmart.uz` | `ManagerPass123!` |
| Seller  | `seller@techmart.uz` | `SellerPass123!` |
| Viewer  | `viewer@techmart.uz` | `ViewerPass123!` |

The seed also includes 12 suppliers, 20 sellers, 100 products, 100 customers and
240+ orders spread over the past six months, so the dashboard shows meaningful
numbers.

## API Documentation

OpenAPI (Swagger UI) is served at http://localhost:8000/docs. Summary:

| Area          | Endpoints                                                     |
| ------------- | ------------------------------------------------------------- |
| Auth          | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `GET /auth/me`, `GET /auth/memberships`, `POST /auth/switch-org` |
| Account security | `POST /auth/forgot-password`, `/auth/reset-password`, `/auth/verify-email`, `/auth/resend-verification` |
| Users         | `GET/POST /users`, `PATCH/DELETE /users/{id}`, `GET /users/{id}`, `POST /users/invite`, `POST /users/invites/accept`, `POST /users/invites/resend`, `PUT /users/{id}/roles` |
| Sellers       | `GET/POST /sellers`, `PATCH/DELETE /sellers/{id}`, `GET /sellers/{id}` |
| Suppliers     | `GET/POST /suppliers`, `PATCH/DELETE /suppliers/{id}`, `GET /suppliers/{id}` |
| Products      | `GET/POST /products`, `PATCH/DELETE /products/{id}`, `GET /products/categories`, `GET /products/{id}` |
| Customers     | `GET/POST /customers`, `PATCH/DELETE /customers/{id}`, `GET /customers/{id}` |
| Orders        | `GET/POST /orders`, `PATCH /orders/{id}`, `PATCH /orders/{id}/payment`, `GET /orders/{id}/history`, `GET /orders/{id}` |
| Inventory     | `GET /inventory`, `GET /inventory/movements`, `POST /inventory/adjustments` |
| Notifications | `GET /notifications`, `GET /notifications/unread-count`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all` |
| Organizations | `GET/PATCH /organizations/me`, `PATCH /organizations/me/plan`, `POST /organizations/me/transfer-ownership`, `POST /organizations/me/close` |
| Analytics     | `GET /analytics/dashboard?range=7d`                           |
| Audit         | `GET /audit-logs`                                             |

Conventions:

- **Auth**: `Authorization: Bearer <access_token>`; 401 → frontend automatically
  refreshes the token once and retries.
- **Error envelope**:

  ```json
  { "success": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} } }
  ```

- **List envelope**:

  ```json
  { "items": [...], "page": 1, "page_size": 10, "total": 240, "total_pages": 24 }
  ```

- Lists accept `search`, `page`, `page_size`, `sort_by`, `sort_order` plus
  domain filters (`status`, `category`, `stock_status`, `type`, ...).
- Every mutating action is written to the audit log.

## Testing

Backend (122 tests — auth, account security, RBAC, org isolation, every domain,
notifications, membership/org switching, pagination):

```bash
docker compose exec backend pytest -q
```

Frontend (ESLint + TypeScript):

```bash
docker compose exec frontend npm run lint
docker compose exec frontend npx tsc --noEmit
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/v1/          # routers (auth, users, sellers, products, ...)
│   │   ├── core/            # config, exceptions, security
│   │   ├── db/              # session, seed CLI
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # org-scoped data access
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # business logic (orders, inventory, analytics, audit)
│   ├── alembic/             # migrations
│   ├── tests/               # pytest suite (122 tests)
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── (auth)/          # login, register, forgot/reset password, verify
│   │   │                    # email, accept invite
│   │   ├── dashboard/       # overview + products, orders, customers, sellers,
│   │   │                    # suppliers, inventory, users, audit, settings
│   │   └── layout.tsx       # root layout + AuthProvider
│   ├── components/          # UI kit + notification bell, org switcher,
│   │                        # command search
│   ├── lib/                 # types, api-client, auth, formatting, hooks
│   └── proxy.ts             # route protection (Next 16 proxy)
├── docker/                  # postgres init SQL
├── docs/                    # ARCHITECTURE, API, ERD, RBAC, PHASES
├── docker-compose.yml
├── docker-compose.prod.yml  # production build (see DEPLOYMENT.md)
├── DEPLOYMENT.md
└── .env.example
```

## UI Overview & Features

The platform provides a responsive, role-gated dashboard layout:

- **Dashboard Overview**: Metrics widgets (revenue, orders, average order value, commission), daily sales trend charts, recent orders table, low-stock alerts, and donut charts.
- **Product & Inventory Management**: Paginated product catalog with category/stock filters, instant low-stock indicators, and manual stock adjustment audit logs.
- **Order Lifecycle Manager**: Filterable order list, multi-step order status transition workflow (pending → confirmed → processing → shipped → delivered / cancelled), line-item management, and payment status updates.
- **Team & RBAC Administration**: Owner & Admin management of team members, invitation lifecycle, inline role switching, and organization switching drawer.
- **Audit & Analytics**: Searchable audit logs capturing all system operations with actor IDs, metadata, and IP addresses.

## Demo

1. `docker compose up --build`
2. Open http://localhost:3000 → Register a new organization, or sign in with the
   seeded owner account above.
3. Browse the dashboard, create a product, create an order and move it through
   statuses, adjust stock, invite team members, then review the audit log.