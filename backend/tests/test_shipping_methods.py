"""Shipping methods: admin CRUD, storefront listing, checkout fee integration."""

import pytest


async def _create_method(client, token: str, **overrides) -> dict:
    payload = {
        "name": "Standard",
        "description": "3-5 business days",
        "price": 5.0,
        "estimated_delivery_days": 5,
        "is_active": True,
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/v1/shipping-methods",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _product(client, token: str, sku: str = "SHIP-1") -> dict:
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Ship Product",
            "sku": sku,
            "category": "Furniture",
            "price": 20.0,
            "cost_price": 8.0,
            "stock_quantity": 10,
            "low_stock_threshold": 2,
            "status": "active",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_shipping_method_crud(client, org_a):
    token = org_a["access_token"]
    method = await _create_method(client, token, name="Express", price=9.99)
    assert method["price"] == "9.99"

    resp = await client.get(
        "/api/v1/shipping-methods",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.patch(
        f"/api/v1/shipping-methods/{method['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"price": 12.0, "is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == "12.00"

    resp = await client.get(
        "/api/v1/shipping-methods",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json() == []

    resp = await client.delete(
        f"/api/v1/shipping-methods/{method['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_shipping_method_duplicate_name_rejected(client, org_a):
    token = org_a["access_token"]
    await _create_method(client, token, name="Standard")
    resp = await client.post(
        "/api/v1/shipping-methods",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Standard", "price": 1.0},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SHIPPING_METHOD_NAME_TAKEN"


@pytest.mark.asyncio
async def test_shipping_methods_scoped_to_org(client, org_a, org_b):
    method = await _create_method(client, org_a["access_token"])
    resp = await client.get(
        f"/api/v1/shipping-methods/{method['id']}",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_storefront_lists_active_methods_only(client, org_a):
    token = org_a["access_token"]
    await _create_method(client, token, name="Cheap", price=1.0)
    hidden = await _create_method(client, token, name="Hidden", price=50.0)
    await client.patch(
        f"/api/v1/shipping-methods/{hidden['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )

    resp = await client.get("/api/v1/stores/org-a/shipping-methods")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert names == ["Cheap"]

    legacy = await client.get("/api/v1/storefront/shipping-methods")
    assert legacy.status_code == 200
    assert [m["name"] for m in legacy.json()] == ["Cheap"]


@pytest.mark.asyncio
async def test_checkout_uses_shipping_method_fee(client, org_a):
    token = org_a["access_token"]
    method = await _create_method(client, token, name="Courier", price=7.5)
    p = await _product(client, token)

    resp = await client.post(
        "/api/v1/stores/org-a/checkout",
        json={
            "first_name": "Sam",
            "last_name": "Buyer",
            "email": "sam@ship.io",
            "shipping_method_id": method["id"],
            "items": [{"product_id": p["id"], "quantity": 2}],
        },
    )
    assert resp.status_code == 201, resp.text
    order_id = resp.json()["order_id"]

    order_resp = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_resp.status_code == 200
    assert order_resp.json()["shipping_fee"] == "7.50"
    assert order_resp.json()["total"] == "47.50"


@pytest.mark.asyncio
async def test_checkout_rejects_foreign_shipping_method(client, org_a, org_b):
    method = await _create_method(client, org_b["access_token"], name="B Courier")
    p = await _product(client, org_a["access_token"], sku="SHIP-F")

    resp = await client.post(
        "/api/v1/stores/org-a/checkout",
        json={
            "first_name": "Sam",
            "last_name": "Buyer",
            "email": "sam2@ship.io",
            "shipping_method_id": method["id"],
            "items": [{"product_id": p["id"], "quantity": 1}],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SHIPPING_METHOD_NOT_FOUND"
