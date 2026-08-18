"""Tests for account security, notifications, company settings and suppliers."""

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.security import hash_refresh_token
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.auth_token import AuthToken
from app.models.user import User


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _install_token(email: str, purpose: str) -> str:
    """Insert a raw token directly (email delivery is simulated)."""
    raw = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == email)).scalar_one()
        db.add(
            AuthToken(
                user_id=user.id,
                purpose=purpose,
                token_hash=hash_refresh_token(raw),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        db.commit()
    return raw


async def _product(client, token: str, **overrides) -> dict:
    payload = {
        "name": "Test Item",
        "sku": f"SKU-{secrets.token_hex(4).upper()}",
        "category": "Misc",
        "price": 10,
        "cost_price": 5,
        "stock_quantity": 100,
        "low_stock_threshold": 5,
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/v1/products", headers=await _headers(token), json=payload
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- password reset --------------------------------------------------------

@pytest.mark.asyncio
async def test_forgot_password_never_leaks_accounts(client, org_a):
    resp = await client.post(
        "/api/v1/auth/forgot-password", json={"email": org_a["email"]}
    )
    assert resp.status_code == 200

    ghost = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nobody@test.io"}
    )
    assert ghost.status_code == 200
    assert "If an account exists" in ghost.json()["message"]


@pytest.mark.asyncio
async def test_reset_password_with_invalid_token_rejected(client, org_a):
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "NewPass12345"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_password_reset_full_flow(client, org_a):
    raw = _install_token(org_a["email"], "reset_password")
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw, "new_password": "BrandNewPass1!"},
    )
    assert resp.status_code == 200

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": org_a["email"], "password": "BrandNewPass1!"},
    )
    assert login.status_code == 200

    # token is single-use
    again = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw, "new_password": "AnotherPass1!"},
    )
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "TOKEN_USED"


# --- email verification ----------------------------------------------------

@pytest.mark.asyncio
async def test_verify_email_marks_user_verified(client, org_a):
    raw = _install_token(org_a["email"], "verify_email")
    resp = await client.post("/api/v1/auth/verify-email", json={"token": raw})
    assert resp.status_code == 200

    me = await client.get(
        "/api/v1/auth/me", headers=await _headers(org_a["access_token"])
    )
    assert me.status_code == 200
    assert me.json()["email_verified"] is True


# --- notifications ---------------------------------------------------------

@pytest.mark.asyncio
async def test_low_stock_notification_on_product_create(client, org_a):
    h = await _headers(org_a["access_token"])
    await _product(client, org_a["access_token"], stock_quantity=2)

    count = await client.get("/api/v1/notifications/unread-count", headers=h)
    assert count.status_code == 200
    assert count.json()["count"] >= 1

    listing = await client.get("/api/v1/notifications", headers=h)
    assert listing.status_code == 200
    types = {n["type"] for n in listing.json()["items"]}
    assert "low_stock" in types


@pytest.mark.asyncio
async def test_mark_notifications_read(client, org_a):
    h = await _headers(org_a["access_token"])
    await _product(client, org_a["access_token"], stock_quantity=1)

    listing = (await client.get("/api/v1/notifications", headers=h)).json()
    assert listing["total"] >= 1
    target = listing["items"][0]
    resp = await client.patch(
        f"/api/v1/notifications/{target['id']}/read", headers=h
    )
    assert resp.status_code == 200
    assert resp.json()["read"] is True

    count = (await client.get("/api/v1/notifications/unread-count", headers=h)).json()
    assert count["count"] == listing["total"] - 1

    cleared = await client.patch("/api/v1/notifications/read-all", headers=h)
    assert cleared.status_code == 200
    count = (await client.get("/api/v1/notifications/unread-count", headers=h)).json()
    assert count["count"] == 0


@pytest.mark.asyncio
async def test_new_order_creates_audit_and_notification(client, org_a):
    h = await _headers(org_a["access_token"])
    customer = (await client.post(
        "/api/v1/customers", headers=h,
        json={"first_name": "Ann", "last_name": "Lee", "email": "ann@test.io"},
    )).json()
    product = await _product(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/orders", headers=h,
        json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 2}]},
    )
    assert resp.status_code == 201
    assert resp.json()["created_by"] is not None

    with SessionLocal() as db:
        found = db.execute(
            select(AuditLog).where(AuditLog.action == "order.created")
        ).scalar_one_or_none()
        assert found is not None


# --- company settings ------------------------------------------------------

@pytest.mark.asyncio
async def test_company_settings_update_and_read(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.patch(
        "/api/v1/organizations/me",
        headers=h,
        json={
            "currency": "UZS",
            "timezone": "Asia/Tashkent",
            "phone": "+998901234567",
            "address": "Tashkent, Uzbekistan",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "UZS"
    assert body["timezone"] == "Asia/Tashkent"
    assert body["phone"] == "+998901234567"

    read = await client.get("/api/v1/organizations/me", headers=h)
    assert read.status_code == 200
    assert read.json()["currency"] == "UZS"


# --- suppliers -------------------------------------------------------------

@pytest.mark.asyncio
async def test_supplier_crud_search_and_isolation(client, org_a, org_b):
    h = await _headers(org_a["access_token"])
    created = await client.post(
        "/api/v1/suppliers", headers=h,
        json={"name": "Acme Parts", "email": "acme@test.io", "phone": "+998900000000"},
    )
    assert created.status_code == 201
    sid = created.json()["id"]

    listed = await client.get("/api/v1/suppliers?search=acme", headers=h)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = await client.patch(
        f"/api/v1/suppliers/{sid}", headers=h, json={"status": "inactive"}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "inactive"

    # org isolation: org B cannot see or touch A's supplier
    hb = await _headers(org_b["access_token"])
    cross = await client.get(f"/api/v1/suppliers/{sid}", headers=hb)
    assert cross.status_code == 404
    cross_del = await client.delete(f"/api/v1/suppliers/{sid}", headers=hb)
    assert cross_del.status_code == 404

    deleted = await client.delete(f"/api/v1/suppliers/{sid}", headers=h)
    assert deleted.status_code == 204


# --- orders: payment status + shipping + history ---------------------------

@pytest.mark.asyncio
async def test_order_payment_shipping_and_history(client, org_a):
    h = await _headers(org_a["access_token"])
    customer = (await client.post(
        "/api/v1/customers", headers=h,
        json={"first_name": "Bob", "last_name": "Brown", "email": "bob@test.io"},
    )).json()
    product = await _product(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/orders", headers=h,
        json={
            "customer_id": customer["id"],
            "shipping_fee": 9.99,
            "payment_status": "paid",
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["shipping_fee"] == "9.99"
    assert body["payment_status"] == "paid"
    assert body["total"] == "29.99"

    payment = await client.patch(
        f"/api/v1/orders/{body['id']}/payment", headers=h, json={"payment_status": "refunded"}
    )
    assert payment.status_code == 200
    assert payment.json()["payment_status"] == "refunded"

    history = await client.get(f"/api/v1/orders/{body['id']}/history", headers=h)
    assert history.status_code == 200
    actions = {entry["action"] for entry in history.json()}
    assert "order.payment_status_changed" in actions
    assert "order.created" in actions

    filtered = await client.get("/api/v1/orders?payment_status=refunded", headers=h)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1


# --- team invites ----------------------------------------------------------

@pytest.mark.asyncio
async def test_invite_and_accept_flow(client, org_a):
    h = await _headers(org_a["access_token"])
    invite = await client.post(
        "/api/v1/users/invite", headers=h,
        json={"email": "newbie@test.io", "role_codes": ["manager"]},
    )
    assert invite.status_code == 201
    assert invite.json()["status"] == "invited"

    raw = _install_token("newbie@test.io", "invite")
    accept = await client.post(
        "/api/v1/users/invites/accept",
        json={"token": raw, "full_name": "Newbie User", "password": "NewbiePass123"},
    )
    assert accept.status_code == 200

    login = await client.post(
        "/api/v1/auth/login", json={"email": "newbie@test.io", "password": "NewbiePass123"}
    )
    assert login.status_code == 200
    me = await client.get(
        "/api/v1/auth/me", headers=await _headers(login.json()["access_token"])
    )
    assert me.json()["status"] == "active"
    assert me.json()["email_verified"] is True


@pytest.mark.asyncio
async def test_invite_rejects_duplicate_email(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post(
        "/api/v1/users/invite", headers=h,
        json={"email": "dup@test.io", "role_codes": ["manager"]},
    )
    again = await client.post(
        "/api/v1/users/invite", headers=h,
        json={"email": "dup@test.io", "role_codes": ["manager"]},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.asyncio
async def test_users_list_supports_status_filter(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post(
        "/api/v1/users/invite", headers=h,
        json={"email": "pending@test.io", "role_codes": ["viewer"]},
    )
    listed = await client.get("/api/v1/users?status=invited", headers=h)
    assert listed.status_code == 200
    emails = {u["email"] for u in listed.json()["items"]}
    assert "pending@test.io" in emails


@pytest.mark.asyncio
async def test_invite_resend_flow(client, org_a):
    h = await _headers(org_a["access_token"])
    invite = await client.post(
        "/api/v1/users/invite", headers=h,
        json={"email": "resend@test.io", "role_codes": ["viewer"]},
    )
    assert invite.status_code == 201
    user_id = invite.json()["id"]

    before = _install_token("resend@test.io", "invite")
    resend = await client.post(
        "/api/v1/users/invites/resend", headers=h, json={"user_id": user_id}
    )
    assert resend.status_code == 200
    assert resend.json()["status"] == "invited"

    after = _install_token("resend@test.io", "invite")
    assert after != before
    accept = await client.post(
        "/api/v1/users/invites/accept",
        json={"token": after, "full_name": "Resend User", "password": "ResendPass123"},
    )
    assert accept.status_code == 200

    rejected = await client.post(
        "/api/v1/users/invites/resend", headers=h, json={"user_id": user_id}
    )
    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "NOT_INVITED"
