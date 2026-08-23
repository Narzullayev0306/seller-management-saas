"""Return requests (customer -> admin) and refunds workflow."""

import pytest


async def _product(client, token: str, sku: str = "RET-1") -> dict:
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Return Product",
            "sku": sku,
            "category": "Furniture",
            "price": 30.0,
            "cost_price": 12.0,
            "stock_quantity": 10,
            "low_stock_threshold": 2,
            "status": "active",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _register_customer(client, org_a, email: str = "ret@test.io") -> dict:
    resp = await client.post(
        "/api/v1/stores/org-a/auth/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "first_name": "Ret",
            "last_name": "Customer",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    me = await client.get(
        "/api/v1/stores/org-a/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200, me.text
    return {**body, "customer": me.json()}


async def _order_with_status(client, org_a, product: dict, status: str) -> dict:
    token = org_a["access_token"]
    reg = await _register_customer(client, org_a)
    resp = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": reg["customer"]["customer_id"],
            "items": [{"product_id": product["id"], "quantity": 3}],
        },
    )
    assert resp.status_code == 201, resp.text
    order_id = resp.json()["id"]
    steps = {
        "confirmed": ["confirmed"],
        "shipped": ["confirmed", "processing", "shipped"],
        "delivered": ["confirmed", "processing", "shipped", "delivered"],
    }
    for step in steps.get(status, []):
        resp = await client.patch(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": step},
        )
        assert resp.status_code == 200, resp.text
    return {**reg, "order_id": order_id}


async def _request_return(client, reg: dict, order_id: str, item_id: str, quantity=1, **extra):
    resp = await client.post(
        f"/api/v1/stores/org-a/returns?order_id={order_id}",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
        json={"order_item_id": item_id, "quantity": quantity, **extra},
    )
    return resp


@pytest.mark.asyncio
async def test_customer_requests_return_flow(client, org_a):
    token = org_a["access_token"]
    p = await _product(client, token)
    data = await _order_with_status(client, org_a, p, "delivered")

    resp = await client.get(
        f"/api/v1/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = resp.json()["items"][0]["id"]

    resp = await _request_return(client, data, data["order_id"], item_id, quantity=1)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["quantity"] == 1
    assert body["product_name"] == "Return Product"

    # Quantity cap: only 2 more units remain.
    resp = await _request_return(client, data, data["order_id"], item_id, quantity=3)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "RETURN_QUANTITY_EXCEEDED"


@pytest.mark.asyncio
async def test_return_requires_delivered_or_shipped(client, org_a):
    p = await _product(client, org_a["access_token"], sku="RET-2")
    data = await _order_with_status(client, org_a, p, "pending")
    resp = await client.get(
        f"/api/v1/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
    )
    item_id = resp.json()["items"][0]["id"]
    resp = await _request_return(client, data, data["order_id"], item_id, quantity=1)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "RETURN_NOT_ELIGIBLE"


@pytest.mark.asyncio
async def test_return_forbidden_for_other_customer(client, org_a):
    token = org_a["access_token"]
    p = await _product(client, token, sku="RET-3")
    data = await _order_with_status(client, org_a, p, "delivered")
    other = await _register_customer(client, org_a, email="other@test.io")
    resp = await client.get(
        f"/api/v1/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = resp.json()["items"][0]["id"]
    resp = await client.post(
        f"/api/v1/stores/org-a/returns?order_id={data['order_id']}",
        headers={"Authorization": f"Bearer {other['access_token']}"},
        json={"order_item_id": item_id, "quantity": 1},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "RETURN_FORBIDDEN"


@pytest.mark.asyncio
async def test_approve_creates_refund_and_workflow(client, org_a):
    token = org_a["access_token"]
    p = await _product(client, token, sku="RET-4")
    data = await _order_with_status(client, org_a, p, "delivered")
    resp = await client.get(
        f"/api/v1/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = resp.json()["items"][0]["id"]

    ret = await _request_return(client, data, data["order_id"], item_id, quantity=2)
    return_id = ret.json()["id"]

    resp = await client.patch(
        f"/api/v1/returns/{return_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "approve"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    refunds = await client.get(
        "/api/v1/refunds", headers={"Authorization": f"Bearer {token}"}
    )
    assert refunds.status_code == 200
    assert len(refunds.json()) == 1
    assert refunds.json()[0]["amount"] == "60.00"  # 30.00 x 2
    assert refunds.json()[0]["return_request_id"] == return_id

    resp = await client.patch(
        f"/api/v1/returns/{return_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "receive"},
    )
    assert resp.json()["status"] == "received"
    resp = await client.patch(
        f"/api/v1/returns/{return_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "complete"},
    )
    assert resp.json()["status"] == "completed"

    # Rejecting an approved return is not allowed.
    resp = await client.patch(
        f"/api/v1/returns/{return_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "reject"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "RETURN_BAD_TRANSITION"


@pytest.mark.asyncio
async def test_manual_refund_and_process(client, org_a):
    token = org_a["access_token"]
    p = await _product(client, token, sku="RET-5")
    data = await _order_with_status(client, org_a, p, "delivered")

    resp = await client.post(
        "/api/v1/refunds",
        headers={"Authorization": f"Bearer {token}"},
        json={"order_id": data["order_id"], "amount": 10.0, "reason": "Goodwill"},
    )
    assert resp.status_code == 201, resp.text
    refund_id = resp.json()["id"]
    assert resp.json()["amount"] == "10.00"

    # Over-refund rejected.
    resp = await client.post(
        "/api/v1/refunds",
        headers={"Authorization": f"Bearer {token}"},
        json={"order_id": data["order_id"], "amount": 1000.0},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "REFUND_EXCEEDS_ORDER"

    resp = await client.patch(
        f"/api/v1/refunds/{refund_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "process"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "processed"


@pytest.mark.asyncio
async def test_cross_org_isolation(client, org_a, org_b):
    token_a = org_a["access_token"]
    p = await _product(client, token_a, sku="RET-6")
    data = await _order_with_status(client, org_a, p, "delivered")
    resp = await client.get(
        f"/api/v1/orders/{data['order_id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    item_id = resp.json()["items"][0]["id"]
    ret = await _request_return(client, data, data["order_id"], item_id, quantity=1)

    resp = await client.patch(
        f"/api/v1/returns/{ret.json()['id']}",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
        json={"action": "approve"},
    )
    assert resp.status_code == 404
