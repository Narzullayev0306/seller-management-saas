# Architecture

## 1. Overview

Seller Management SaaS is a multi-tenant, multi-user application where companies
(organizations) manage sellers, products, customers, orders, inventory and sales.

The system is built as a **monorepo** with two independent applications:

| Layer    | Technology                    | Role                                |
| -------- | ----------------------------- | ----------------------------------- |
| Frontend | Next.js (App Router), TypeScript, Tailwind, shadcn/ui, TanStack Query, React Hook Form, Zod, Recharts | Client SPA served by Next.js        |
| Backend  | FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL | REST API + business logic + security |
| Cache    | Redis                         | Catalog cache + rate limiting       |
| Infra    | Docker Compose                | Frontend + backend + worker + Postgres + Redis (+ Caddy in prod) |

## 2. High-level diagram

```
┌──────────────────────┐        ┌──────────────────────────────────────┐
│  Next.js Frontend    │  HTTP  │  FastAPI Backend                     │
│  - Auth pages        │ ─────▶ │  /api/v1/*                           │
│  - Dashboard/CRUD    │  JSON  │  ├─ API layer (routers, deps)        │
│  - TanStack Query    │        │  ├─ Service layer (business logic)   │
│  - React Hook Form   │        │  ├─ Repository layer (data access)   │
│                      │        │  └─ Models (SQLAlchemy ORM)          │
└──────────────────────┘        └───────────────┬──────────────────────┘
                                                │ SQLAlchemy
                                        ┌───────▼────────┐
                                        │   PostgreSQL    │
                                        │  (multi-tenant) │
                                        └─────────────────┘
```

## 3. Backend architecture

Layered, dependency direction is strictly inward:

```
api (HTTP layer)
  │  — routers, request/response schemas, auth dependencies
  ▼
services (business logic)
  │  — order transaction, inventory logic, analytics, audit logging
  ▼
repositories (data access)
  │  — thin wrappers over SQLAlchemy sessions, scoped by organization
  ▼
models + db (ORM, engine, migrations)
```

### 3.1 Key decisions

- **Multi-tenancy**: `organization_id` column on every tenant-owned table.
  The organization is derived from the authenticated user's JWT — never from
  request bodies/query params. Every repository query is forced to filter by
  `organization_id`, making cross-tenant access structurally impossible.
- **Transactions**: order creation + inventory decrement + sale recording run
  in a single DB transaction; any failure rolls back everything.
- **Auth**: short-lived JWT access tokens (15 min) + rotating refresh tokens
  stored hashed in the DB (revocable).
- **RBAC**: fixed system roles per organization, each mapped to granular
  permissions. Enforcement is a FastAPI dependency
  (`require_permissions(...)`) applied per endpoint.
- **Error handling**: global exception handlers map domain errors to a
  consistent JSON envelope; internal exceptions are logged, never leaked.

## 4. Frontend architecture

- **App Router** with route groups: `(auth)` for login/register, `dashboard/`
  for the authenticated shell (sidebar + top bar) and `storefront/` for the
  public per-org storefront (with customer account, cart, checkout).
- **Server state**: TanStack Query with a centralized API client
  (`lib/api-client`) that injects the access token and transparently refreshes
  expired tokens (one automatic retry on 401).
- **Forms**: React Hook Form + Zod schemas shared per entity.
- **Components**: shadcn/ui primitives + reusable domain components
  (`DataTable`, `Pagination`, `SearchInput`, `FilterDropdown`, `StatCard`,
  `ChartCard`, `ConfirmDialog`, `EmptyState`, `LoadingState`, `ErrorState`).
- **Routing**: `proxy.ts` (Next 16 proxy) guards `/dashboard` routes;
  real security is enforced by the backend.

## 5. Security model

| Concern            | Mitigation                                                            |
| ------------------ | --------------------------------------------------------------------- |
| Passwords          | bcrypt hashing, never stored in plaintext                              |
| Tokens             | JWT access (15 min), rotating refresh tokens stored hashed, revocable |
| Tenancy            | org derived from token; org filter forced in every repo query         |
| Authorization      | Permission dependency on every protected endpoint                     |
| Injection          | SQLAlchemy parameterized queries; validated sort fields (whitelist)   |
| Validation         | Pydantic schemas for every request body/query                         |
| Secrets            | `.env` only; `.env.example` committed, real values never committed    |
| CORS               | Restricted to configured frontend origin                              |
| Brute force        | Slow hashing + Redis-backed rate limiting on auth endpoints (in-memory fallback) |
| Audit              | Every sensitive action recorded in `audit_logs`                       |

## 6. Docker topology

```
docker-compose.yml (dev)
├── postgres   (postgres:16-alpine, healthcheck, volume)
├── redis      (redis:7-alpine, cache + rate limiting; optional at runtime)
├── migrate    (one-shot: alembic upgrade head)
├── backend    (uvicorn on :8000, --reload)
├── worker     (python -m app.worker — outbox dispatch: emails, webhooks)
└── frontend   (Next.js dev server on :3000)

docker-compose.prod.yml
├── redis      (persistent volume)
├── migrate    (one-shot: alembic upgrade head)
├── backend    (uvicorn, 4 workers)
├── worker     (outbox dispatch)
├── frontend   (Next.js standalone build)
└── caddy      (TLS termination + reverse proxy on :80/:443)
```

- **Redis** backs the tenant-aware catalog cache and rate limiting. It is
  enabled by default in production (`REDIS_ENABLED=true`) and disabled in the
  dev compose default (`REDIS_ENABLED=false`) — the backend falls back to
  in-memory rate limiting and skips caching when disabled.
- **Outbox worker** polls `outbox_events` written in the same transaction as
  the business change, so side effects survive crashes.
- The managed path (Vercel + Supabase) runs the API via
  `backend/api/index.py` and Postgres/Storage from Supabase; see DEPLOYMENT.md.

## 7. Observability

- Every response carries an `X-Request-Id`; `/api/health/ready` reports DB +
  Redis status. Optional Sentry instrumentation via `SENTRY_DSN`.

