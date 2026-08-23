"""Storefront wishlist: guest + customer ownership, merge on login, API."""

import pytest


async def _product(client, token: str, sku: str = "WISH-1") -> dict:
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Wish Product",
            "sku": sku,
            "category": "Furniture",
            "price": 25.0,
            "cost_price": 10.0,
            "stock_quantity": 10,
            "low_stock_threshold": 2,
            "status": "active",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _register_customer(client, org_a, email: str = "wish@test.io") -> dict:
    resp = await client.post(
        "/api/v1/stores/org-a/auth/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "first_name": "Wish",
            "last_name": "Customer",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_guest_wishlist_lifecycle(client, org_a):
    p = await _product(client, org_a["access_token"])
    token = "guest-session-wishlist-1"

    resp = await client.get(
        "/api/v1/stores/org-a/wishlist", headers={"X-Wishlist-Token": token}
    )
    assert resp.status_code == 200
    assert resp.json()["item_count"] == 0

    resp = await client.post(
        "/api/v1/stores/org-a/wishlist/items",
        headers={"X-Wishlist-Token": token},
        json={"product_id": p["id"]},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["item_count"] == 1
    assert body["items"][0]["name"] == "Wish Product"

    # Idempotent add.
    resp = await client.post(
        "/api/v1/stores/org-a/wishlist/items",
        headers={"X-Wishlist-Token": token},
        json={"product_id": p["id"]},
    )
    assert resp.status_code == 201
    assert resp.json()["item_count"] == 1

    item_id = resp.json()["items"][0]["id"]
    resp = await client.delete(
        f"/api/v1/stores/org-a/wishlist/items/{item_id}",
        headers={"X-Wishlist-Token": token},
    )
    assert resp.status_code == 200
    assert resp.json()["item_count"] == 0


@pytest.mark.asyncio
async def test_wishlist_requires_identity(client, org_a):
    resp = await client.get("/api/v1/stores/org-a/wishlist")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "WISHLIST_IDENTITY_REQUIRED"


@pytest.mark.asyncio
async def test_wishlist_rejects_foreign_product(client, org_b):
    resp = await client.post(
        "/api/v1/stores/org-a/wishlist/items",
        headers={"X-Wishlist-Token": "guest-wishlist-x"},
        json={"product_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_customer_wishlist_and_guest_merge(client, org_a):
    p = await _product(client, org_a["access_token"])
    guest_token = "guest-wishlist-merge"
    await client.post(
        "/api/v1/stores/org-a/wishlist/items",
        headers={"X-Wishlist-Token": guest_token},
        json={"product_id": p["id"]},
    )

    reg = await _register_customer(client, org_a)
    customer_headers = {
        "Authorization": f"Bearer {reg['access_token']}",
        "X-Wishlist-Token": guest_token,
    }
    resp = await client.get("/api/v1/stores/org-a/wishlist", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["item_count"] == 1

    # A second product added under the customer account.
    p2 = await _product(client, org_a["access_token"], sku="WISH-2")
    resp = await client.post(
        "/api/v1/stores/org-a/wishlist/items",
        headers=customer_headers,
        json={"product_id": p2["id"]},
    )
    assert resp.json()["item_count"] == 2

    # Guest token no longer owns a separate wishlist (merged + deleted).
    guest_resp = await client.get(
        "/api/v1/stores/org-a/wishlist", headers={"X-Wishlist-Token": guest_token}
    )
    assert guest_resp.json()["item_count"] == 0


@pytest.mark.asyncio
async def test_customer_account_scoped_to_own_store(client, org_a, org_b):
    p = await _product(client, org_b["access_token"], sku="WISH-B")
    reg = await _register_customer(client, org_a)
    resp = await client.post(
        "/api/v1/stores/org-a/wishlist/items",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
        json={"product_id": p["id"]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_clear_wishlist(client, org_a):
    p = await _product(client, org_a["access_token"])
    token = "guest-wishlist-clear"
    await client.post(
        "/api/v1/stores/org-a/wishlist/items",
        headers={"X-Wishlist-Token": token},
        json={"product_id": p["id"]},
    )
    resp = await client.delete(
        "/api/v1/stores/org-a/wishlist", headers={"X-Wishlist-Token": token}
    )
    assert resp.status_code == 200
    assert resp.json()["item_count"] == 0
