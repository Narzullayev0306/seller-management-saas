import pytest

from tests.conftest import create_user, login


async def _product_payload():
    return {
        "name": "Test Widget",
        "sku": "TST-1",
        "category": "Tools",
        "price": 99.5,
        "cost_price": 50,
        "stock_quantity": 30,
        "status": "active",
    }


async def _create_product(client, token):
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json=await _product_payload(),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_viewer_cannot_create_product(client, org_a):
    token = org_a["access_token"]
    await create_user(client, token, "viewer@a.io", "viewer")
    viewer_tokens = await login(client, "viewer@a.io", "Pass12345")

    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
        json=await _product_payload(),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_viewer_can_read_products(client, org_a):
    token = org_a["access_token"]
    await _create_product(client, token)
    await create_user(client, token, "viewer@a.io", "viewer")
    viewer_tokens = await login(client, "viewer@a.io", "Pass12345")

    resp = await client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_manager_cannot_manage_users(client, org_a):
    token = org_a["access_token"]
    await create_user(client, token, "manager@a.io", "manager")
    manager_tokens = await login(client, "manager@a.io", "Pass12345")

    resp = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {manager_tokens['access_token']}"},
    )
    assert resp.status_code == 403

    resp = await client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {manager_tokens['access_token']}"},
        json={"email": "x@a.io", "full_name": "X Y", "password": "Pass12345", "role_codes": ["viewer"]},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_manager_can_manage_orders(client, org_a):
    token = org_a["access_token"]
    await create_user(client, token, "manager@a.io", "manager")
    manager_tokens = await login(client, "manager@a.io", "Pass12345")
    headers = {"Authorization": f"Bearer {manager_tokens['access_token']}"}

    product = await _create_product(client, token)
    cust = await client.post(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "A", "last_name": "B", "email": "ab@x.io"},
    )
    order = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": cust.json()["id"],
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    )
    assert order.status_code == 201
    assert order.json()["total"] == "199.00"


@pytest.mark.asyncio
async def test_seller_role_only_sees_own_orders(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await _create_product(client, token)
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

    user = await create_user(client, token, "seller@a.io", "seller")
    linked = await client.patch(
        f"/api/v1/sellers/{seller_id}", headers=headers, json={"user_id": str(user["id"])}
    )
    assert linked.status_code == 200
    seller_tokens = await login(client, "seller@a.io", "Pass12345")
    seller_headers = {"Authorization": f"Bearer {seller_tokens['access_token']}"}

    other_order = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": cust_id, "items": [{"product_id": product["id"], "quantity": 1}]},
    )
    assert other_order.status_code == 201

    self_order = await client.post(
        "/api/v1/orders",
        headers=seller_headers,
        json={"customer_id": cust_id, "items": [{"product_id": product["id"], "quantity": 1}]},
    )
    assert self_order.status_code == 201
    assert self_order.json()["seller_id"] == seller_id

    listing = await client.get("/api/v1/orders", headers=seller_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    hidden = await client.get(
        f"/api/v1/orders/{other_order.json()['id']}", headers=seller_headers
    )
    assert hidden.status_code == 403


@pytest.mark.asyncio
async def test_owner_cannot_deactivate_self(client, org_a):
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {org_a['access_token']}"}
    )
    user_id = me.json()["id"]
    resp = await client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
        json={"is_active": False},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CANNOT_DEACTIVATE_SELF"


@pytest.mark.asyncio
async def test_audit_log_requires_audit_read(client, org_a):
    token = org_a["access_token"]
    await create_user(client, token, "manager@a.io", "manager")
    manager_tokens = await login(client, "manager@a.io", "Pass12345")
    resp = await client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {manager_tokens['access_token']}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_owner_sees_audit_logs(client, org_a):
    resp = await client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
    )
    assert resp.status_code == 200
    actions = [item["action"] for item in resp.json()["items"]]
    assert "auth.register" in actions
