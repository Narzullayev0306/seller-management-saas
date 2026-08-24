# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-23

First public release: a multi-tenant inventory & sales management SaaS
(FastAPI + Next.js), deployed as a live demo on Vercel + Supabase.

### Added

- **Core domain**: organizations, users with 5 RBAC roles (owner, admin,
  manager, seller, viewer) and 38 granular permissions, products, customers,
  sellers, suppliers, orders with full lifecycle
  (`pending → confirmed → processing → shipped → delivered / cancelled`),
- **Multi-tenancy**: row-level security policies on every org-scoped table;
  every query is org-scoped at the service layer.
- **Storefront**: public catalog, product quick view, search, server-side cart
  and customer accounts.
- **Dashboard**: analytics overview, product CRUD with image upload,
  order pipeline with inline status transitions, customer/seller/supplier
  management, reports, marketing, billing, settings, API keys.
- **API**: OpenAPI docs at `/docs`, health endpoints
  (`/api/health`, `/api/health/live`, `/api/health/ready`), request-ID and
  security-header middleware, optional Sentry instrumentation.
- **Auth**: JWT access/refresh rotation with refresh-token families,
  organization signup creates the first owner automatically.
- **Testing**: 228 backend pytest tests, frontend typecheck/lint, Playwright
  E2E suite (auth, products, orders, storefront), CodeQL static analysis.
- **Deployment**: Docker Compose dev/prod stacks with Redis-backed Celery
  workers, Vercel deployment path (serverless entrypoint `backend/api/index.py`),
  Supabase Postgres support, Alembic migrations run automatically on start.
- **Docs**: README with screenshots, DEPLOYMENT guide including backup /
  restore procedures, API reference.

### Security

- Demo credentials only — no real secrets in the repository; `.env` files are
  gitignored and Supabase keys are injected as Vercel environment variables.
