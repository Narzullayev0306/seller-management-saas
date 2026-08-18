import pytest

from tests.conftest import login


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _setup(client, token: str, stock: int = 20):
    h = await _headers(token)
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={
                "name": "Order Widget",
                "sku": "ORDW-1",
                "category": "Tools",
                "price": 25,
                "cost_price": 10,
                "stock_quantity": stock,
            },
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers",
            headers=h,
            json={"first_name": "Ord", "last_name": "Cust", "email": "ordcust@x.io"},
        )
    ).json()
    return h, product, customer


@pytest.mark.asyncio
async def test_create_order_computes_totals(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/orders",
        headers=h,
        json={
            "customer_id": customer["id"],
            "discount": 10,
            "tax": 5,
            "items": [
                {"product_id": product["id"], "quantity": 2},
                {"product_id": product["id"], "quantity": 1},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    order = resp.json()
    assert order["subtotal"] == "75.00"
    assert order["total"] == "70.00"
    assert order["status"] == "pending"
    assert order["order_number"].startswith("ORD-")


@pytest.mark.asyncio
async def test_create_order_decrements_stock(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    await client.post(
        "/api/v1/orders",
        headers=h,
        json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 3}]},
    )
    fetched = (await client.get(f"/api/v1/products/{product['id']}", headers=h)).json()
    assert fetched["stock_quantity"] == 17


@pytest.mark.asyncio
async def test_insufficient_stock_rejected(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"], stock=5)
    resp = await client.post(
        "/api/v1/orders",
        headers=h,
        json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 6}]},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"
    assert resp.json()["error"]["details"]["available"] == 5


@pytest.mark.asyncio
async def test_failed_order_rolls_back_stock(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"], stock=5)
    await client.post(
        "/api/v1/orders",
        headers=h,
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_id": product["id"], "quantity": 2},
                {"product_id": product["id"], "quantity": 99},
            ],
        },
    )
    fetched = (await client.get(f"/api/v1/products/{product['id']}", headers=h)).json()
    assert fetched["stock_quantity"] == 5


@pytest.mark.asyncio
async def test_discount_exceeding_subtotal_rejected(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/orders",
        headers=h,
        json={"customer_id": customer["id"], "discount": 9999, "items": [{"product_id": product["id"], "quantity": 1}]},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_empty_items_rejected(client, org_a):
    h, _, customer = await _setup(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/orders", headers=h, json={"customer_id": customer["id"], "items": []}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_order_number_unique_per_org(client, org_a, org_b):
    h_a, p_a, c_a = await _setup(client, org_a["access_token"])
    h_b, p_b, c_b = await _setup(client, org_b["access_token"])
    oa = await client.post(
        "/api/v1/orders", headers=h_a, json={"customer_id": c_a["id"], "items": [{"product_id": p_a["id"], "quantity": 1}]}
    )
    ob = await client.post(
        "/api/v1/orders", headers=h_b, json={"customer_id": c_b["id"], "items": [{"product_id": p_b["id"], "quantity": 1}]}
    )
    assert oa.status_code == 201 and ob.status_code == 201


@pytest.mark.asyncio
async def test_delivery_finalizes_sale_and_updates_counters(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    seller = (
        await client.post(
            "/api/v1/sellers",
            headers=h,
            json={"first_name": "S", "last_name": "T", "email": "st@x.io", "commission_rate": 10},
        )
    ).json()
    order = (
        await client.post(
            "/api/v1/orders",
            headers=h,
            json={"seller_id": seller["id"], "customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 2}]},
        )
    ).json()

    resp = await client.patch(
        f"/api/v1/orders/{order['id']}", headers=h, json={"status": "confirmed"}
    )
    assert resp.status_code == 200
    resp = await client.patch(
        f"/api/v1/orders/{order['id']}", headers=h, json={"status": "processing"}
    )
    assert resp.status_code == 200
    resp = await client.patch(
        f"/api/v1/orders/{order['id']}", headers=h, json={"status": "shipped"}
    )
    assert resp.status_code == 200
    resp = await client.patch(
        f"/api/v1/orders/{order['id']}", headers=h, json={"status": "delivered"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "delivered"

    seller_fetched = (await client.get(f"/api/v1/sellers/{seller['id']}", headers=h)).json()
    assert seller_fetched["total_sales"] == "50.00"
    assert seller_fetched["total_orders"] == 1

    customer_fetched = (await client.get(f"/api/v1/customers/{customer['id']}", headers=h)).json()
    assert customer_fetched["total_orders"] == 1
    assert customer_fetched["total_spent"] == "50.00"

    analytics = await client.get("/api/v1/analytics/dashboard?range=today", headers=h)
    assert analytics.json()["summary"]["revenue"] == "50.00"
    assert analytics.json()["summary"]["total_commission"] == "5.00"


@pytest.mark.asyncio
async def test_cancel_restores_stock(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    order = (
        await client.post(
            "/api/v1/orders",
            headers=h,
            json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 4}]},
        )
    ).json()

    resp = await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "cancelled"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    product_fetched = (await client.get(f"/api/v1/products/{product['id']}", headers=h)).json()
    assert product_fetched["stock_quantity"] == 20

    customer_fetched = (await client.get(f"/api/v1/customers/{customer['id']}", headers=h)).json()
    assert customer_fetched["total_orders"] == 0
    assert customer_fetched["total_spent"] == "0.00"

    analytics = await client.get("/api/v1/analytics/dashboard?range=today", headers=h)
    assert analytics.json()["summary"]["orders_count"] == 0


@pytest.mark.asyncio
async def test_delivered_order_cannot_be_cancelled(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    order = (
        await client.post(
            "/api/v1/orders",
            headers=h,
            json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
        )
    ).json()
    for status in ("confirmed", "processing", "shipped", "delivered"):
        resp = await client.patch(
            f"/api/v1/orders/{order['id']}", headers=h, json={"status": status}
        )
        assert resp.status_code == 200, resp.text

    resp = await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "cancelled"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


@pytest.mark.asyncio
async def test_cancelled_order_cannot_change(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    order = (
        await client.post(
            "/api/v1/orders",
            headers=h,
            json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
        )
    ).json()
    await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "cancelled"})
    resp = await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "delivered"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


@pytest.mark.asyncio
async def test_invalid_order_status_rejected(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    order = (
        await client.post(
            "/api/v1/orders",
            headers=h,
            json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
        )
    ).json()
    resp = await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "teleported"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_order_status_filters(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    for _ in range(3):
        await client.post(
            "/api/v1/orders",
            headers=h,
            json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
        )
    filtered = await client.get("/api/v1/orders?status=pending", headers=h)
    assert filtered.json()["total"] == 3
    filtered = await client.get("/api/v1/orders?status=delivered", headers=h)
    assert filtered.json()["total"] == 0


@pytest.mark.asyncio
async def test_seller_role_can_deliver_own_order(client, org_a):
    h, product, customer = await _setup(client, org_a["access_token"])
    seller = (
        await client.post(
            "/api/v1/sellers",
            headers=h,
            json={"first_name": "Own", "last_name": "Seller", "email": "ownseller@x.io", "commission_rate": 5},
        )
    ).json()

    user = (
        await client.post(
            "/api/v1/users",
            headers=h,
            json={"email": "s3@x.io", "full_name": "Seller Three", "password": "Pass12345", "role_codes": ["seller"]},
        )
    ).json()

    seller_tokens = await login(client, "s3@x.io", "Pass12345")
    sh = await _headers(seller_tokens["access_token"])

    await client.patch(f"/api/v1/sellers/{seller['id']}", headers=h, json={"user_id": user["id"]})

    order = (
        await client.post(
            "/api/v1/orders",
            headers=sh,
            json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
        )
    ).json()
    assert order["seller_id"] == seller["id"]

    for status in ("confirmed", "processing", "shipped", "delivered"):
        resp = await client.patch(
            f"/api/v1/orders/{order['id']}", headers=sh, json={"status": status}
        )
        assert resp.status_code == 200, resp.text
