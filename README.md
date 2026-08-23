# Seller Management SaaS

**Production-grade multi-tenant SaaS for managing products, orders, customers, inventory, payments and analytics — with a public storefront, RBAC, PostgreSQL row-level security and an event-driven core.**

[![CI](https://github.com/Narzullayev0306/seller-management-saas/actions/workflows/ci.yml/badge.svg)](https://github.com/Narzullayev0306/seller-management-saas/actions/workflows/ci.yml)
![Backend tests](https://img.shields.io/badge/backend%20tests-149-brightgreen)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-cache%20%7C%20rate%20limit-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[Documentation](docs/) · [API Reference](docs/API.md) · [Architecture](docs/ARCHITECTURE.md) · [Database ERD](docs/ERD.md) · [Deployment](DEPLOYMENT.md)

<!-- TODO: add real product screenshots here (dashboard, products, orders, storefront, mobile) once captured.
<p align="center">
  <img src="docs/assets/dashboard.png" alt="Dashboard" width="49%">
  <img src="docs/assets/storefront.png" alt="Storefront" width="49%">
</p>
-->

## Why this project is different

Most portfolio CRUD apps stop at "it works". This one is engineered around the problems that break real production systems:

| Problem in production | How it is solved here |
| --- | --- |
| Tenant A seeing tenant B's data | JWT-derived `organization_id` + repository layer that *forces* org filtering — cross-tenant reads are structurally impossible; verified by a dedicated isolation test suite |
| Double-click "Pay" creating two orders | Idempotent checkout keyed by `Idempotency-Key` header |
| Two buyers grabbing the last item simultaneously | `SELECT … FOR UPDATE` row locks on inventory adjustments |
| Order status corrupted by invalid transitions | Explicit order state machine (`pending → confirmed → processing → shipped → delivered / cancelled`) |
| Emails/payment webhooks lost on crash | Transactional outbox pattern with a background worker |
| Brute-force login/register | Redis-backed rate limiting incl. trusted-proxy-aware client IP resolution |
| Database-level tenant leaks | Supabase Row-Level Security policies on every org-scoped table |

## Architecture

```
                ┌───────────────┐          ┌────────────────────┐
                │   Customer    │          │  Admin / Staff     │
                └───────┬───────┘          └─────────┬──────────┘
                        │                            │
                        ▼                            ▼
              ┌──────────────────┐        ┌──────────────────────┐
              │    Storefront    │        │   Dashboard / API    │
              │  Next.js 16 RSC  │        │      Next.js 16      │
              └────────┬─────────┘        └──────────┬───────────┘
                       │                             │
                       └──────────────┬──────────────┘
                                      ▼
                    ┌─────────────────────────────────┐
                    │         FastAPI Backend         │
                    │   api → services → repositories │
                    │  JWT (org claim) · RBAC · rate  │
                    │  limiting · idempotency guard   │
                    └──────┬─────────────────────┬────┘
                           │                     │
          ┌────────────────▼─────────┐   ┌───────▼─────────────────┐
          │      PostgreSQL 16       │   │         Redis           │
          │ multi-tenant schema,     │   │ catalog cache (tenant-  │
          │ Supabase RLS policies,   │   │ aware) · rate limits    │
          │ FOR UPDATE locks         │   │                         │
          └────────────────┬─────────┘   └─────────────────────────┘
                           │ outbox events (same DB transaction)
                           ▼
                 ┌────────────────────┐
                 │   Outbox Worker    │──▶ email dispatch · external services
                 └────────────────────┘
```

Strict layering, dependency direction inward:

```
api → services → repositories → models/db
```

### Event-driven core (transactional outbox)

```
┌─────────────────────────────────────┐
│ DB transaction                      │
│  order + stock movement             │
│  + outbox_events row  ← atomic      │
└──────────────┬──────────────────────┘
               ▼
      outbox_events table
               ▼
      worker polls & dispatches  ──▶  email / external services
```

Side effects survive crashes and are never sent for rolled-back transactions.

## Multi-Tenant Architecture

```
Organization
├── Members (organization_members) ── User ── Roles
├── Products ── Categories ── Variants
├── Orders ── OrderItems ── Payments ── Coupons
├── Customers
├── Sellers · Suppliers
├── Inventory Movements
├── Notifications
├── Audit Logs
└── Outbox Events
```

- Users can belong to **multiple organizations** and switch between them; each session is scoped to one organization via the JWT `org` claim.
- The tenant is derived from the token — **never from the request** — and every repository query is forced to filter by it.
- Alembic migration ships **Supabase RLS policies** on every org-scoped table as defense-in-depth under the service-role app user.

## Security

- Multi-tenant data isolation enforced at three levels: application scoping, forced repository filters, database RLS
- Role-based access control: 5 roles (`owner`, `admin`, `manager`, `seller`, `viewer`) over a 32-permission catalog, server-enforced via FastAPI dependencies
- bcrypt password hashing; short-lived JWT access tokens (15 min) with rotating, hashed, revocable refresh tokens
- Redis-backed rate limiting on login/register, trusted-proxy-aware client IP resolution
- Idempotent checkout (`Idempotency-Key`), `FOR UPDATE` inventory locking, explicit order state machine
- Full audit trail: who, what, entity, metadata, when — for every mutating action
- One-time email tokens (verification, password reset, team invites); CORS restricted to the frontend origin; parameterized queries only; secrets exclusively in environment variables

## Features

**Dashboard & analytics** — revenue, orders, avg order value, commission; daily revenue/orders series, top products/sellers, low-stock widgets, order-status donut, period-over-period comparison.

**Commerce core** — products with categories & variants, customers, sellers (commissions), suppliers, coupons, orders with line items, payment status tracking (pending / paid / partially paid / refunded) and per-order history timeline. Stock decrements on confirmation, restores on cancellation, sales + commission record on delivery.

**Public storefront** — per-organization storefront under an org slug: catalog, product pages, cart, checkout (idempotent), customer order lookup.

**Inventory** — stock levels, movement log (purchase / sale / adjustment), audited manual adjustments.

**Team & organizations** — invitations with self-set passwords, inline role changes, suspend/reactivate members, ownership transfer, plan selection, type-to-confirm company closure.

**Account security** — email verification, forgot/reset password, in-app notifications (low stock, new/cancelled orders, invites) with unread badge.

**List UX everywhere** — search, pagination, filtering, sorting on every list page; loading skeletons, empty/error states, toasts.

**Responsive** — desktop sidebar collapses to a mobile drawer; tables and toolbars adapt down to phone widths.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16 (App Router, RSC), React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Database | PostgreSQL 16 (uuid PKs, indexes, constraints, RLS) |
| Cache / limits | Redis (tenant-aware catalog cache, rate limiting) |
| Auth | bcrypt, PyJWT (access + rotating refresh tokens) |
| Testing | pytest + httpx — **149 backend tests**, ESLint + tsc (frontend) |
| CI | GitHub Actions: ruff, pip-audit, pytest (Postgres service), tsc, eslint, npm audit, Docker builds |
| Infra | Docker Compose (dev + prod files), background outbox worker |

## Getting Started

### Docker (recommended)

```bash
git clone https://github.com/Narzullayev0306/seller-management-saas.git
cd seller-management-saas
cp .env.example .env          # optional — defaults work out of the box
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- Swagger UI: http://localhost:8000/docs

Alembic migrations run automatically on start. The database seeds itself with realistic demo data on first login.

### Demo accounts

The seed creates one demo organization (**TechMart**) with five users — one per role:

| Role | Email | Password |
| --- | --- | --- |
| Owner | `owner@techmart.uz` | `DemoPass123!` |
| Admin | `admin@techmart.uz` | `AdminPass123!` |
| Manager | `manager@techmart.uz` | `ManagerPass123!` |
| Seller | `seller@techmart.uz` | `SellerPass123!` |
| Viewer | `viewer@techmart.uz` | `ViewerPass123!` |

Seed volume: 100 products, 100 customers, 240+ orders across the past six months, 20 sellers, 12 suppliers, coupons — dashboards show meaningful numbers immediately.

### Local development (no Docker)

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
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

## API Documentation

Interactive OpenAPI docs at `http://localhost:8000/docs` (Swagger) and `/redoc`. Full endpoint reference: [`docs/API.md`](docs/API.md).

16 routers: auth, users, roles, sellers, suppliers, products, customers, orders, inventory, notifications, organizations, analytics, audit logs, uploads, coupons, storefront.

Conventions:

```json
// error envelope
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} } }

// list envelope
{ "items": [...], "page": 1, "page_size": 10, "total": 240, "total_pages": 24 }
```

Lists accept `search`, `page`, `page_size`, `sort_by`, `sort_order` plus domain filters. 401 responses trigger one automatic token refresh + retry.

## Testing

**149 automated backend tests** covering authentication, account security, RBAC, **multi-tenant organization isolation**, every business domain, coupons, variants, payments, storefront, idempotency, outbox, notifications and pagination:

```bash
docker compose exec backend pytest -q
```

CI runs the full matrix on every push: ruff + pip-audit + pytest (against a real Postgres 16 service), frontend typecheck + eslint + npm audit + production build, plus both Docker images.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/v1/          # 16 routers (auth, products, orders, storefront, ...)
│   │   ├── core/            # config, security, redis, rate limiting
│   │   ├── db/              # session, seed CLI
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── repositories/    # org-scoped data access (forced tenant filter)
│   │   ├── schemas/         # Pydantic v2 request/response models
│   │   └── services/        # business logic: orders, state machine, inventory,
│   │                        # payments, coupons, outbox, idempotency, RBAC...
│   ├── alembic/versions/    # 10 migrations: schema → storefront → outbox →
│   │                        # security → payments → RLS → variants → members
│   │                        # → coupons → customers/idempotency
│   └── tests/               # pytest suite (149 tests)
├── frontend/
│   ├── app/
│   │   ├── (auth)/          # login, register, verify email, accept invite
│   │   ├── dashboard/       # overview + all domain pages
│   │   └── storefront/      # public per-org storefront
│   ├── components/          # UI kit + notification bell, org switcher
│   ├── lib/                 # types, api-client, auth, hooks
│   └── proxy.ts             # route protection (Next 16 proxy)
├── docker/                  # postgres init SQL
├── docs/                    # ARCHITECTURE · API · ERD · RBAC · FOLDER_STRUCTURE · PHASES
├── docker-compose.yml       # dev stack
├── docker-compose.prod.yml  # production build (see DEPLOYMENT.md)
└── DEPLOYMENT.md
```

## Documentation

| Document | Contents |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layering, tenancy, key design decisions |
| [docs/API.md](docs/API.md) | Full endpoint reference with envelopes |
| [docs/ERD.md](docs/ERD.md) | Entity-relationship diagram |
| [docs/RBAC.md](docs/RBAC.md) | Roles, permission catalog, enforcement points |
| [docs/FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md) | Codebase layout rationale |
| [docs/PHASES.md](docs/PHASES.md) | Build roadmap and progress |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment guide |

## Roadmap

- [ ] Hosted live demo with seeded data
- [ ] E2E browser tests (register → login → product → checkout → dashboard)
- [ ] Observability: structured request IDs, error tracking, metrics
- [ ] Release tags & changelog

---

Built by [Islom Narzullayev](https://github.com/Narzullayev0306) — [portfolio](https://portfolio-six-phi-7ekaz47rl0.vercel.app).
Licensed under [MIT](./LICENSE).
