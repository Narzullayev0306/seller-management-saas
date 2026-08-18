# Deployment

The SaaS is a multi-tenant FastAPI backend + Next.js frontend, deployed with
Docker Compose against a managed Supabase project (Postgres + Storage).

## Architecture

- `backend` — FastAPI, SQLAlchemy, Alembic. Runs migrations at container start,
  then serves `uvicorn` workers. Stores files in Supabase Storage via signed URLs.
- `frontend` — Next.js standalone server, statically built at image build time.
- `redis` — optional cache/rate-limit store (backend falls back to in-memory).
- `supabase` — managed Postgres (database) + Storage (product images).

## 1. Prerequisites

- A Supabase project: copy the project URL, anon key and service key from
  Project Settings > API.
- SMTP credentials for transactional email (optional; without them emails are
  logged to the backend console).

## 2. Configure environment

Copy `.env.example` to `.env` and fill in real values:

| Variable | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | yes | Supabase pooler DSN: `postgresql+psycopg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres` |
| `JWT_SECRET` | yes | Long random string (>= 32 bytes) for access/refresh tokens |
| `FRONTEND_URL` | yes | Public URL of the frontend, used in email links |
| `NEXT_PUBLIC_API_URL` | yes | Public URL of the backend API, e.g. `https://api.example.com/api/v1` |
| `SUPABASE_URL` | yes | Storage bucket for product images |
| `SUPABASE_ANON_KEY` | yes | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | yes | Supabase service key (storage signing) |
| `EMAIL_ENABLED` | no | `true` to send SMTP mail, default `false` (console only) |
| `SMTP_*` | no | Host, port, user, password, from address, TLS toggle |
| `REDIS_ENABLED` | no | `true` to use Redis for rate limits, default `true` in prod |

## 3. Deploy

```bash
cp .env.example .env        # fill in secrets
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

The backend runs `alembic upgrade head` on every start, so the schema is always
migrated before the API accepts traffic.

## 4. First run / seed

Register the first account at `FRONTEND_URL/register` — the owner is created
with the full permission set. For demo data (12 suppliers, sample products,
sellers, orders):

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.db.seed
```

## 5. Database migration workflow

Migrations are Alembic revisions in `backend/alembic/versions/`.

```bash
docker compose -f docker-compose.prod.yml exec backend alembic revision --autogenerate -m "describe change"
# review backend/alembic/versions/*.py, then:
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Row-level security: `backend/alembic/versions/d1e2f3a4b5c6_*.py` enables RLS
policies on every org-scoped table. The app connects as the table owner /
service role so behaviour is unchanged; the policies lock down direct database
access from Supabase anon/authenticated clients.

## 6. Backups

Supabase provides automatic daily backups on the Pro plan (Project Settings >
Backups). For the self-hosted path, back up the Postgres database:

```bash
docker compose -f docker-compose.prod.yml exec backend pg_dump "$DATABASE_URL" -Fc > backup.dump
```

## 7. Operations

- Health check: `GET /health` on the backend.
- Logs: `docker compose -f docker-compose.prod.yml logs -f <service>`.
- Restart one service: `docker compose -f docker-compose.prod.yml restart backend`.
- Zero-downtime-ish upgrades: rebuild and recreate in order:
  `docker compose -f docker-compose.prod.yml up -d --build --force-recreate`.
- Scale the API: increase `--workers` in the backend `command`, then a reverse
  proxy (Caddy/Nginx/Traefik) can terminate TLS and load-balance `8000`.
