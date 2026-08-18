"""Security boundary tests: Organization A must never access Organization B's data."""

import pytest


async def _seed_org(client, token: str, prefix: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": f"{prefix} Product",
            "sku": f"{prefix}-SKU",
            "category": "Tools",
            "price": 10,
            "cost_price": 5,
            "stock_quantity": 50,
        },
    )
    assert product.status_code == 201

    seller = await client.post(
        "/api/v1/sellers",
        headers=headers,
        json={"first_name": f"{prefix}FN", "last_name": f"{prefix}LN", "commission_rate": 5},
    )
    customer = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"first_name": f"{prefix}CFN", "last_name": f"{prefix}CLN", "email": f"{prefix.lower()}@x.io"},
    )
    order = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "seller_id": seller.json()["id"],
            "customer_id": customer.json()["id"],
            "items": [{"product_id": product.json()["id"], "quantity": 2}],
        },
    )
    assert order.status_code == 201, order.text

    return {
        "product": product.json(),
        "seller": seller.json(),
        "customer": customer.json(),
        "order": order.json(),
    }


@pytest.mark.asyncio
async def test_cross_org_product_access_denied(client, org_a, org_b):
    data_a = await _seed_org(client, org_a["access_token"], "A")
    headers_b = {"Authorization": f"Bearer {org_b['access_token']}"}

    resp = await client.get(f"/api/v1/products/{data_a['product']['id']}", headers=headers_b)
    assert resp.status_code == 404

    resp = await client.get("/api/v1/products", headers=headers_b)
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_cross_org_order_access_denied(client, org_a, org_b):
    data_a = await _seed_org(client, org_a["access_token"], "A")
    headers_b = {"Authorization": f"Bearer {org_b['access_token']}"}

    resp = await client.get(f"/api/v1/orders/{data_a['order']['id']}", headers=headers_b)
    assert resp.status_code == 404

    listing = await client.get("/api/v1/orders", headers=headers_b)
    assert listing.json()["total"] == 0


@pytest.mark.asyncio
async def test_cross_org_customer_access_denied(client, org_a, org_b):
    data_a = await _seed_org(client, org_a["access_token"], "A")
    headers_b = {"Authorization": f"Bearer {org_b['access_token']}"}

    resp = await client.get(f"/api/v1/customers/{data_a['customer']['id']}", headers=headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_org_update_and_delete_denied(client, org_a, org_b):
    data_a = await _seed_org(client, org_a["access_token"], "A")
    headers_b = {"Authorization": f"Bearer {org_b['access_token']}"}

    resp = await client.patch(
        f"/api/v1/products/{data_a['product']['id']}",
        headers=headers_b,
        json={"price": 999},
    )
    assert resp.status_code == 404

    resp = await client.delete(
        f"/api/v1/sellers/{data_a['seller']['id']}", headers=headers_b
    )
    assert resp.status_code == 404

    resp = await client.patch(
        f"/api/v1/orders/{data_a['order']['id']}",
        headers=headers_b,
        json={"status": "delivered"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_org_analytics_isolated(client, org_a, org_b):
    await _seed_org(client, org_a["access_token"], "A")
    await _seed_org(client, org_b["access_token"], "B")

    for token in (org_a["access_token"], org_b["access_token"]):
        resp = await client.get(
            "/api/v1/analytics/dashboard?range=year",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["orders_count"] == 1
        assert resp.json()["summary"]["products_count"] == 1


@pytest.mark.asyncio
async def test_cross_org_user_management_denied(client, org_a, org_b):
    me_a = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {org_a['access_token']}"}
    )
    user_a_id = me_a.json()["id"]

    resp = await client.patch(
        f"/api/v1/users/{user_a_id}",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
        json={"full_name": "Hacked Name"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_inventory_adjustment_cross_org_denied(client, org_a, org_b):
    data_a = await _seed_org(client, org_a["access_token"], "A")
    resp = await client.post(
        "/api/v1/inventory/adjustments",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
        json={
            "product_id": data_a["product"]["id"],
            "type": "purchase",
            "quantity": 100,
            "reason": "cross org attack",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_from_org_a_cannot_login_to_org_b_data_via_search(client, org_a, org_b):
    data_a = await _seed_org(client, org_a["access_token"], "A")
    headers_b = {"Authorization": f"Bearer {org_b['access_token']}"}

    resp = await client.get(
        "/api/v1/products?search=Product", headers=headers_b
    )
    assert resp.json()["total"] == 0
    assert data_a["product"]["name"] not in [i["name"] for i in resp.json()["items"]]
