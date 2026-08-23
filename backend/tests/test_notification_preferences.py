"""Notification preferences: API + fan-out enforcement."""

import pytest

from tests.conftest import create_user, login


def _process_outbox() -> None:
    """Deliver pending outbox events synchronously (worker is not running in tests)."""
    from app.db.session import SessionLocal
    from app.worker import process_pending

    with SessionLocal() as db:
        process_pending(db)


async def _manager_headers(client, token: str, email: str) -> dict:
    """Create a manager user and return their auth headers."""
    await create_user(client, token, email, "manager")
    manager_tokens = await login(client, email, "Pass12345")
    return {"Authorization": f"Bearer {manager_tokens['access_token']}"}


async def _order_setup(client, token: str, customer_email: str, product_sku: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    customer = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"first_name": "Ord", "last_name": "Cust", "email": customer_email},
    )
    assert customer.status_code == 201
    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Widget",
            "sku": product_sku,
            "category": "Furniture",
            "price": "10.00",
            "cost_price": "4.00",
            "stock_quantity": 10,
            "low_stock_threshold": 5,
            "status": "active",
        },
    )
    assert product.status_code == 201
    order = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "items": [{"product_id": product.json()["id"], "quantity": 1}],
        },
    )
    assert order.status_code == 201
    return {"headers": headers}


@pytest.mark.asyncio
async def test_preferences_defaults_and_update(client, org_a):
    headers = {"Authorization": f"Bearer {org_a['access_token']}"}
    resp = await client.get("/api/v1/notifications/preferences", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["in_app_enabled"] is True
    assert body["new_order_alerts"] is True
    assert body["low_stock_alerts"] is True
    assert body["marketing_emails"] is False

    resp = await client.put(
        "/api/v1/notifications/preferences",
        headers=headers,
        json={"in_app_enabled": False, "marketing_emails": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["in_app_enabled"] is False
    assert body["marketing_emails"] is True
    # Unspecified fields are untouched.
    assert body["new_order_alerts"] is True


@pytest.mark.asyncio
async def test_preferences_respected_by_fanout(client, org_a):
    """With in_app_enabled=False a user stops receiving fan-out notifications."""

    # Manager is the fan-out recipient; opt them out of everything.
    manager_h = await _manager_headers(client, org_a["access_token"], "manager@test.io")
    await client.put(
        "/api/v1/notifications/preferences",
        headers=manager_h,
        json={"in_app_enabled": False, "new_order_alerts": False, "low_stock_alerts": False},
    )

    # Owner (the actor) creates the order; fan-out targets the manager.
    await _order_setup(client, org_a["access_token"], "ordcust@x.io", "WID-1")
    _process_outbox()

    unread = await client.get("/api/v1/notifications/unread-count", headers=manager_h)
    assert unread.json()["count"] == 0


@pytest.mark.asyncio
async def test_fanout_still_notifies_when_enabled(client, org_a):
    """Default (no preferences set) behavior: fan-out notifications are created."""
    manager_h = await _manager_headers(client, org_a["access_token"], "manager2@test.io")

    await _order_setup(client, org_a["access_token"], "ordcust2@x.io", "WID-2")
    _process_outbox()

    unread = await client.get("/api/v1/notifications/unread-count", headers=manager_h)
    assert unread.json()["count"] >= 1


@pytest.mark.asyncio
async def test_low_stock_alert_respects_preference(client, org_a):
    headers = {"Authorization": f"Bearer {org_a['access_token']}"}
    manager_h = await _manager_headers(client, org_a["access_token"], "manager3@test.io")
    # Opt the manager out of low-stock alerts only.
    await client.put(
        "/api/v1/notifications/preferences",
        headers=manager_h,
        json={"in_app_enabled": True, "low_stock_alerts": False},
    )

    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Running Low",
            "sku": "LOW-1",
            "category": "Furniture",
            "price": "5.00",
            "cost_price": "2.00",
            "stock_quantity": 1,
            "low_stock_threshold": 5,
            "status": "active",
        },
    )
    assert product.status_code == 201
    _process_outbox()

    unread = await client.get("/api/v1/notifications/unread-count", headers=manager_h)
    assert unread.json()["count"] == 0
