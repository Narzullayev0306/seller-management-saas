"""Test fixtures.

A dedicated PostgreSQL test database is created (seller_management_test),
migrations are applied once per session, and every test function starts
with a clean schema.
"""

from __future__ import annotations

import os

os.environ["APP_ENV"] = "test"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["REDIS_ENABLED"] = "false"

# Point whatever DATABASE_URL is provided (docker service, CI localhost, custom)
# at the dedicated test database instead of assuming the docker hostname.
_BASE_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://seller:seller_dev_password@postgres:5432/seller_management",
)
TEST_DB_NAME = "seller_management_test"
os.environ["DATABASE_URL"] = _BASE_DB_URL.rsplit("/", 1)[0] + "/" + TEST_DB_NAME

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402, F401
from app.main import app  # noqa: E402


def _admin_engine():
    url = settings.database_url
    admin_url = url.rsplit("/", 1)[0] + "/postgres"
    return create_engine(admin_url, isolation_level="AUTOCOMMIT")


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    admin = _admin_engine()
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        ).scalar_one_or_none()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()

    from alembic.config import Config

    from alembic import command

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")

    yield

    with _admin_engine().connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)'))


@pytest.fixture(autouse=True)
def _clean_schema(_test_database):
    from app.db.base import Base

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.core import ratelimit

    ratelimit._in_memory_store.clear()
    yield
    ratelimit._in_memory_store.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def auth_headers(client):
    async def factory(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    return factory


async def register_org(client: AsyncClient, suffix: str = "") -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Org {suffix}".strip(),
            "full_name": "Test Owner",
"email": f"owner{suffix}@test.io".lower(),
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    email = f"owner{suffix}@test.io".lower()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO user_roles (id, user_id, role_id)
                SELECT gen_random_uuid(), u.id, r.id
                FROM users u
                JOIN organizations o ON o.id = u.organization_id
                JOIN roles r ON r.organization_id = o.id AND r.code = 'owner'
                WHERE u.email = :email
                """
            ),
            {"email": email},
        )
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "email": email,
        "password": "StrongPass123",
    }


@pytest.fixture
async def org_a(client):
    return await register_org(client, "A")


@pytest.fixture
async def org_b(client):
    return await register_org(client, "B")


async def create_user(client, token: str, email: str, role: str, password: str = "Pass12345"):
    resp = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": email, "full_name": "New User", "password": password, "role_codes": [role]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login(client, email: str, password: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def auth(client, token: str):
    return {"Authorization": f"Bearer {token}"}
