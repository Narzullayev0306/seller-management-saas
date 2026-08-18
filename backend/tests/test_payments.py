import pytest
from httpx import AsyncClient


async def _product(client: AsyncClient, token: str, sku: str, price: float = 20, stock: int = 5) -> str:
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": f"Pay Product {sku}",
            "sku": sku,
            "category": "Gadgets",
            "price": price,
            "cost_price": 8,
            "stock_quantity": stock,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _checkout(client: AsyncClient, product_id: str, quantity: int = 1) -> dict:
    resp = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Pay",
            "last_name": "Guest",
            "email": "pay-guest@example.com",
            "items": [{"product_id": product_id, "quantity": quantity}],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_checkout_creates_paid_payment_via_mock_provider(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pid = await _product(client, token, "PAY-1")

    body = await _checkout(client, pid, 2)
    assert body["payment_status"] == "paid"
    assert body["payment_id"]

    payments = await client.get(
        f"/api/v1/orders/{body['order_id']}/payments", headers=headers
    )
    assert payments.status_code == 200
    items = payments.json()
    assert len(items) == 1
    p = items[0]
    assert p["provider"] == "mock"
    assert p["provider_payment_id"].startswith("mock_")
    assert p["status"] == "paid"
    assert p["amount"] == "40.00"
    assert p["paid_at"] is not None
    assert p["currency"] == "USD"


@pytest.mark.asyncio
async def test_checkout_with_decline_provider_marks_order_failed(client, org_a, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "payment_provider", "decline")
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pid = await _product(client, token, "PAY-2")

    body = await _checkout(client, pid, 1)
    assert body["payment_status"] == "failed"

    payments = await client.get(
        f"/api/v1/orders/{body['order_id']}/payments", headers=headers
    )
    p = payments.json()[0]
    assert p["provider"] == "decline"
    assert p["status"] == "failed"
    assert p["failure_message"] == "payment declined"


@pytest.mark.asyncio
async def test_order_payments_scoped_to_org(client, org_a, org_b):
    token = org_a["access_token"]
    pid = await _product(client, token, "PAY-3")
    body = await _checkout(client, pid, 1)

    other = await client.get(
        f"/api/v1/orders/{body['order_id']}/payments",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
    )
    assert other.status_code == 404


@pytest.mark.asyncio
async def test_order_payment_status_update_accepts_failed(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pid = await _product(client, token, "PAY-4")
    body = await _checkout(client, pid, 1)

    resp = await client.patch(
        f"/api/v1/orders/{body['order_id']}/payment",
        headers=headers,
        json={"payment_status": "failed"},
    )
    assert resp.status_code == 200
    assert resp.json()["payment_status"] == "failed"
