import pytest

from tests.conftest import create_user, login


@pytest.mark.asyncio
async def test_role_matrix_lists_org_roles_and_catalog(client, org_a):
    token = org_a["access_token"]
    resp = await client.get(
        "/api/v1/roles/matrix",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    codes = {r["code"] for r in body["roles"]}
    assert codes == {"owner", "admin", "manager", "seller", "viewer", "customer"}
    owner = next(r for r in body["roles"] if r["code"] == "owner")
    assert owner["is_system"] is True
    assert "analytics.read" in owner["permissions"]
    customer = next(r for r in body["roles"] if r["code"] == "customer")
    assert customer["is_system"] is True
    assert customer["permissions"] == []
    seller = next(r for r in body["roles"] if r["code"] == "seller")
    assert "analytics.read" in seller["permissions"]
    assert "orders.read" in seller["permissions"]
    assert "users.read" not in seller["permissions"]
    perms = {p["code"] for p in body["permissions"]}
    assert "analytics.read" in perms
    assert len(perms) >= 24


@pytest.mark.asyncio
async def test_role_matrix_requires_users_read(client, org_a):
    token = org_a["access_token"]
    user = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "viewer@a.io", "full_name": "Viewer", "password": "Pass12345", "role_codes": ["viewer"]},
    )
    assert user.status_code == 201
    tokens = await client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@a.io", "password": "Pass12345"},
    )
    resp = await client.get(
        "/api/v1/roles/matrix",
        headers={"Authorization": f"Bearer {tokens.json()['access_token']}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_seller_analytics_scoped_to_own_orders(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Widget",
            "sku": "WGT-1",
            "category": "tools",
            "price": 100,
            "cost_price": 40,
            "stock_quantity": 20,
        },
    )
    assert product.status_code == 201
    product_id = product.json()["id"]
    cust = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"first_name": "A", "last_name": "B", "email": "ab@x.io"},
    )
    cust_id = cust.json()["id"]

    seller = await client.post(
        "/api/v1/sellers",
        headers=headers,
        json={"first_name": "F", "last_name": "G", "email": "fg@x.io", "commission_rate": 5},
    )
    seller_id = seller.json()["id"]
    other_seller = await client.post(
        "/api/v1/sellers",
        headers=headers,
        json={"first_name": "H", "last_name": "I", "email": "hi@x.io", "commission_rate": 5},
    )
    other_seller_id = other_seller.json()["id"]

    user = await create_user(client, token, "seller@a.io", "seller")
    linked = await client.patch(
        f"/api/v1/sellers/{seller_id}", headers=headers, json={"user_id": str(user["id"])}
    )
    assert linked.status_code == 200
    seller_tokens = await login(client, "seller@a.io", "Pass12345")
    seller_headers = {"Authorization": f"Bearer {seller_tokens['access_token']}"}

    await client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": cust_id, "items": [{"product_id": product_id, "quantity": 1}]},
    )
    mine = await client.post(
        "/api/v1/orders",
        headers=seller_headers,
        json={"customer_id": cust_id, "items": [{"product_id": product_id, "quantity": 1}]},
    )
    assert mine.status_code == 201
    delivered = await client.patch(
        f"/api/v1/orders/{mine.json()['id']}",
        headers=seller_headers,
        json={"status": "delivered"},
    )
    assert delivered.status_code == 200

    dash = await client.get("/api/v1/analytics/dashboard", headers=seller_headers)
    assert dash.status_code == 200
    body = dash.json()
    assert body["summary"]["orders_count"] == 1
    assert body["summary"]["revenue"] == "100.00"
    assert body["summary"]["customers_count"] == 1
    assert body["summary"]["products_count"] == 1
    assert body["summary"]["total_commission"] == "5.00"
    assert len(body["top_products"]) == 1
    assert body["top_products"][0]["id"] == product_id
    assert body["top_sellers"][0]["id"] == seller_id
    assert body["top_sellers"][0]["id"] != other_seller_id

    owner_dash = await client.get("/api/v1/analytics/dashboard", headers=headers)
    assert owner_dash.json()["summary"]["orders_count"] == 2
    assert len(owner_dash.json()["top_sellers"]) == 1


@pytest.mark.asyncio
async def test_unlinked_seller_gets_empty_dashboard(client, org_a):
    token = org_a["access_token"]
    user = await create_user(client, token, "lonely@a.io", "seller")
    assert user["id"]
    seller_tokens = await login(client, "lonely@a.io", "Pass12345")
    dash = await client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {seller_tokens['access_token']}"},
    )
    assert dash.status_code == 200
    body = dash.json()
    assert body["summary"]["orders_count"] == 0
    assert body["summary"]["revenue"] == "0.00"
    assert body["revenue_over_time"] == []
