"""Billing: plan catalog, summary, change-plan invoicing, usage limits and feature gating."""

import pytest

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.services import billing_service


async def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_billing_plans_and_summary(client, org_a):
    h = await _auth(org_a["access_token"])
    resp = await client.get("/api/v1/billing/plans", headers=h)
    assert resp.status_code == 200
    plans = resp.json()
    assert {p["code"] for p in plans} == {"free", "pro", "enterprise"}
    pro = next(p for p in plans if p["code"] == "pro")
    assert pro["price"] == "29.00"
    assert "webhooks" in pro["features"]

    resp = await client.get("/api/v1/billing/summary", headers=h)
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["plan"] == "free"
    assert summary["plan_name"] == "Free"
    assert summary["usage"]["users"] >= 1
    assert summary["usage"]["products"] == 0
    assert summary["subscription_status"] == "active"


@pytest.mark.asyncio
async def test_change_plan_creates_invoice(client, org_a):
    h = await _auth(org_a["access_token"])
    resp = await client.post("/api/v1/billing/change-plan", headers=h, json={"plan": "pro"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["plan"] == "pro"
    assert resp.json()["price"] == "29.00"

    invoices = await client.get("/api/v1/billing/invoices", headers=h)
    assert invoices.status_code == 200
    rows = invoices.json()
    assert len(rows) == 1
    assert rows[0]["plan"] == "pro"
    assert rows[0]["amount"] == "29.00"
    assert rows[0]["invoice_number"].startswith("INV-")

    summary = await client.get("/api/v1/billing/summary", headers=h)
    assert summary.json()["plan"] == "pro"

    # Switching to enterprise adds a second invoice.
    resp = await client.post("/api/v1/billing/change-plan", headers=h, json={"plan": "enterprise"})
    assert resp.status_code == 200
    invoices = await client.get("/api/v1/billing/invoices", headers=h)
    assert len(invoices.json()) == 2


@pytest.mark.asyncio
async def test_non_owner_cannot_change_plan(client, org_a):
    from tests.conftest import create_user

    await create_user(client, org_a["access_token"], "member@billing.io", "manager")
    resp = await client.post(
        "/api/v1/billing/change-plan",
        headers=await _auth(org_a["access_token"]),
        json={"plan": "enterprise"},
    )
    assert resp.status_code == 200
    # manager lacks billing.manage -> owner-only
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "member@billing.io", "password": "Pass12345"},
    )
    member_token = login.json()["access_token"]
    resp = await client.post(
        "/api/v1/billing/change-plan",
        headers=await _auth(member_token),
        json={"plan": "free"},
    )
    assert resp.status_code == 403
    # manager also lacks billing.read -> cannot view the summary.
    resp = await client.get("/api/v1/billing/summary", headers=await _auth(member_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_usage_limit_blocks_user_creation(client, org_a, monkeypatch):
    from tests.conftest import create_user

    # Patch the catalog so the free plan allows only 2 users (owner + 1).
    catalog = dict(billing_service.PLAN_CATALOG)
    catalog["free"] = {**catalog["free"], "limits": {**catalog["free"]["limits"], "users": 2}}
    monkeypatch.setattr(billing_service, "PLAN_CATALOG", catalog)

    await create_user(client, org_a["access_token"], "one@limit.io", "viewer")
    resp = await client.post(
        "/api/v1/users",
        headers=await _auth(org_a["access_token"]),
        json={"email": "two@limit.io", "full_name": "Two", "password": "Pass12345", "role_codes": ["viewer"]},
    )
    assert resp.status_code == 402
    assert resp.json()["error"]["code"] == "PLAN_LIMIT"

    # Upgrading to pro (users: 100) unlocks creation again.
    await client.post("/api/v1/billing/change-plan", headers=await _auth(org_a["access_token"]), json={"plan": "pro"})
    resp = await client.post(
        "/api/v1/users",
        headers=await _auth(org_a["access_token"]),
        json={"email": "two@limit.io", "full_name": "Two", "password": "Pass12345", "role_codes": ["viewer"]},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_usage_limit_blocks_product_creation(client, org_a, monkeypatch):
    catalog = dict(billing_service.PLAN_CATALOG)
    catalog["free"] = {**catalog["free"], "limits": {**catalog["free"]["limits"], "products": 1}}
    monkeypatch.setattr(billing_service, "PLAN_CATALOG", catalog)
    h = await _auth(org_a["access_token"])

    resp = await client.post(
        "/api/v1/products",
        headers=h,
        json={"name": "P1", "sku": "P-1", "category": "Test", "price": 10, "cost_price": 5, "stock_quantity": 1},
    )
    assert resp.status_code == 201, resp.text

    resp = await client.post(
        "/api/v1/products",
        headers=h,
        json={"name": "P2", "sku": "P-2", "category": "Test", "price": 10, "cost_price": 5, "stock_quantity": 1},
    )
    assert resp.status_code == 402
    assert resp.json()["error"]["code"] == "PLAN_LIMIT"


@pytest.mark.asyncio
async def test_feature_gating_domains(client, org_a):
    h = await _auth(org_a["access_token"])
    # Free plan has no custom_domain feature.
    resp = await client.post(
        "/api/v1/domains",
        headers=h,
        json={"domain": "shop.example.com"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "PLAN_FEATURE"

    # Upgrade to pro (custom_domain included) then add + verify + delete.
    await client.post("/api/v1/billing/change-plan", headers=h, json={"plan": "pro"})
    resp = await client.post("/api/v1/domains", headers=h, json={"domain": "shop.example.com"})
    assert resp.status_code == 201, resp.text
    domain = resp.json()
    assert domain["status"] == "pending"
    assert len(domain["verification_token"]) >= 8

    listed = await client.get("/api/v1/domains", headers=h)
    assert len(listed.json()) == 1

    resp = await client.post(
        f"/api/v1/domains/{domain['id']}/verify",
        headers=h,
        json={"token": domain["verification_token"]},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "verified"
    assert resp.json()["verified_at"] is not None

    resp = await client.post(
        f"/api/v1/domains/{domain['id']}/verify",
        headers=h,
        json={"token": "wrong-token"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "DOMAIN_VERIFY_FAILED"

    resp = await client.delete(f"/api/v1/domains/{domain['id']}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_domain_duplicate_rejected(client, org_a):
    h = await _auth(org_a["access_token"])
    await client.post("/api/v1/billing/change-plan", headers=h, json={"plan": "pro"})
    await client.post("/api/v1/domains", headers=h, json={"domain": "dup.example.com"})
    resp = await client.post("/api/v1/domains", headers=h, json={"domain": "dup.example.com"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "DOMAIN_TAKEN"


@pytest.mark.asyncio
async def test_subscription_seeded_for_existing_org(client, org_a):
    from sqlalchemy import select

    with SessionLocal() as db:
        org = db.execute(
            select(Organization).where(Organization.slug == "org-a")
        ).scalar_one()
        sub = billing_service.get_or_create_subscription(db, org.id)
        db.commit()
        assert sub.plan == org.plan == "free"
