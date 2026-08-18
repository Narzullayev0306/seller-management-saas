# Development Phases & Implementation Order

Work is incremental: each phase ends with verification (tests, lint, typecheck,
migrations, API smoke test) before moving on.

## PHASE 1 — Skeleton & Docker  ✅
- Monorepo scaffold: `backend/`, `frontend/`, `docker/`, `docs/`, `.env.example`, `docker-compose.yml`
- Backend: `pyproject.toml`, app factory, config, health endpoint, Dockerfile
- Frontend: Next.js scaffold (TypeScript + Tailwind), Dockerfile
- Postgres container + init SQL (uuid extension)
- **Verify**: `docker compose up --build` → `/api/health` responds, frontend renders

## PHASE 2 — Models & Migrations
- All SQLAlchemy models (ERD), naming conventions, indexes, constraints
- Alembic init + initial migration (autogenerate, then review)
- **Verify**: migration applies cleanly on fresh DB; downgrade works

## PHASE 3 — Auth
- bcrypt hashing, JWT access (15 min), refresh tokens (rotating, hashed, revocable)
- `/auth/register|login|refresh|logout|me`
- **Verify**: pytest auth suite green; token rotation & revocation tested

## PHASE 4 — RBAC & Org Isolation
- Permission catalog + system roles seeded per org at registration
- `require_permissions` dependency; org context derived from token
- Org-scoped repository base (forces `organization_id` filter)
- **Verify**: pytest rbac + isolation suites green (A can't read B)

## PHASE 5 — Domain APIs
Order: users → sellers → products → customers → orders (+items, transactional
lifecycle) → inventory (movements, adjustments) → analytics (summary, series)
→ audit logs.
- Centralized exception handling + consistent envelopes wired app-wide
- Pagination/search/filter/sort helpers (whitelisted sort columns)
- **Verify**: per-module pytest suites; OpenAPI docs checked; error codes used

## PHASE 6 — Seed Data
- CLI seed: 1 org, 5 users (one per role), 20 sellers, 100 products,
  100 customers, 200+ orders across 6 months, movements, sales, audit rows
- **Verify**: seeded DB shows sensible dashboard numbers

## PHASE 7 — Backend Tests Hardening
- Full suite: auth, rbac, isolation, CRUD per entity, orders (transaction rollback),
  inventory, analytics, pagination, validation, error codes
- **Verify**: `pytest` green from clean DB

## PHASE 8 — Frontend Shell & Auth UI
- shadcn/ui setup, root providers, API client + token refresh, auth store
- Login/register pages, protected route shell (sidebar + topbar), route guards
- **Verify**: register → login → logout flows; token refresh works

## PHASE 9 — Frontend Pages
Order: dashboard (StatCards + charts) → products → sellers → customers →
orders (line-item form) → inventory → users → audit → settings
- Reusable DataTable/Pagination/Search/Filter/ConfirmDialog/forms everywhere
- TanStack Query keys + invalidation per entity; permission-aware UI
- **Verify**: manual E2E walkthrough of every page; responsive checks

## PHASE 10 — Documentation & Polish
- README (portfolio-ready), API docs notes, screenshots placeholder
- Final security review (secrets, CORS, error leaks, permission gaps)
- Final polish pass (empty states, loading, errors, accessibility basics)
- **Verify**: full `docker compose up --build` from clean state; walkthrough all acceptance criteria

## Definition of Done (per phase)
1. All tests for the phase pass (pytest / build)
2. Typecheck + lint clean (backend: ruff; frontend: tsc + eslint)
3. Migrations apply cleanly
4. No TODOs, no fake implementations
5. Manual smoke test of the affected features