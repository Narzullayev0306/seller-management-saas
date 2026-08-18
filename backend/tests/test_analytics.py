import pytest


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _seed_sales(client, token: str, n_orders: int = 5):
    h = await _headers(token)
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={"name": "Analytics Item", "sku": "ANL-1", "category": "Gadgets", "price": 100, "cost_price": 40, "stock_quantity": 100},
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers", headers=h, json={"first_name": "An", "last_name": "Lytic", "email": "anlytic@x.io"}
        )
    ).json()
    for _ in range(n_orders):
        order = (
            await client.post(
                "/api/v1/orders",
                headers=h,
                json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
            )
        ).json()
        await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "delivered"})


@pytest.mark.asyncio
async def test_summary_metrics(client, org_a):
    h = await _headers(org_a["access_token"])
    await _seed_sales(client, org_a["access_token"], n_orders=5)

    resp = await client.get("/api/v1/analytics/dashboard?range=today", headers=h)
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert summary["revenue"] == "500.00"
    assert summary["orders_count"] == 5
    assert summary["products_count"] == 1
    assert summary["customers_count"] == 1
    assert summary["avg_order_value"] == "100.00"


@pytest.mark.asyncio
async def test_revenue_series_and_top_items(client, org_a):
    h = await _headers(org_a["access_token"])
    await _seed_sales(client, org_a["access_token"], n_orders=3)

    body = (await client.get("/api/v1/analytics/dashboard?range=today", headers=h)).json()
    assert len(body["revenue_over_time"]) == 1
    assert body["revenue_over_time"][0]["value"] == "300.00"
    assert body["orders_over_time"][0]["value"] == "3"
    assert body["top_products"][0]["name"] == "Analytics Item"
    assert body["top_products"][0]["value"] == "300.00"
    assert body["sales_by_category"][0]["category"] == "Gadgets"
    assert body["sales_by_category"][0]["value"] == "300.00"


@pytest.mark.asyncio
async def test_cancelled_orders_excluded(client, org_a):
    h = await _headers(org_a["access_token"])
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={"name": "Cancelled Item", "sku": "CNL-1", "category": "T", "price": 50, "cost_price": 20, "stock_quantity": 10},
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers", headers=h, json={"first_name": "C", "last_name": "D", "email": "cd2@x.io"}
        )
    ).json()
    order = (
        await client.post(
            "/api/v1/orders",
            headers=h,
            json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
        )
    ).json()
    await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "cancelled"})

    summary = (await client.get("/api/v1/analytics/dashboard?range=today", headers=h)).json()["summary"]
    assert summary["orders_count"] == 0
    assert summary["revenue"] == "0.00"


@pytest.mark.asyncio
async def test_custom_range_requires_dates(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.get("/api/v1/analytics/dashboard?range=custom", headers=h)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_RANGE"


@pytest.mark.asyncio
async def test_invalid_range_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.get("/api/v1/analytics/dashboard?range=decade", headers=h)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_custom_range_with_dates(client, org_a):
    h = await _headers(org_a["access_token"])
    await _seed_sales(client, org_a["access_token"], n_orders=2)
    resp = await client.get(
        "/api/v1/analytics/dashboard?range=custom&start=2020-01-01&end=2030-12-31", headers=h
    )
    assert resp.status_code == 200
    assert resp.json()["summary"]["orders_count"] == 2


@pytest.mark.asyncio
async def test_dashboard_widgets_present(client, org_a):
    h = await _headers(org_a["access_token"])
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={"name": "Widgets Item", "sku": "WDG-1", "category": "Gadgets", "price": 100, "cost_price": 40, "stock_quantity": 100, "low_stock_threshold": 200},
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers", headers=h, json={"first_name": "An", "last_name": "Lytic", "email": "wlytic@x.io"}
        )
    ).json()
    for _ in range(3):
        order = (
            await client.post(
                "/api/v1/orders",
                headers=h,
                json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
            )
        ).json()
        await client.patch(f"/api/v1/orders/{order['id']}", headers=h, json={"status": "delivered"})

    body = (await client.get("/api/v1/analytics/dashboard?range=today", headers=h)).json()

    assert len(body["recent_orders"]) == 3
    first = body["recent_orders"][0]
    assert first["order_number"].startswith("ORD-")
    assert first["customer_name"] == "An Lytic"
    assert first["total"] == "100.00"
    assert first["status"] == "delivered"

    assert len(body["low_stock_products"]) == 1
    assert body["low_stock_products"][0]["name"] == "Widgets Item"
    assert body["low_stock_products"][0]["stock_quantity"] == 97

    by_status = {s["status"]: s["count"] for s in body["status_distribution"]}
    assert by_status["delivered"] == 3

    comparison = body["revenue_comparison"]
    assert comparison["current"] == "300.00"
    assert comparison["previous"] == "0.00"
    assert comparison["change_percent"] == "100"


@pytest.mark.asyncio
async def test_dashboard_widgets_empty(client, org_a):
    h = await _headers(org_a["access_token"])
    body = (await client.get("/api/v1/analytics/dashboard?range=today", headers=h)).json()
    assert body["recent_orders"] == []
    assert body["low_stock_products"] == []
    assert body["status_distribution"] == []
    assert body["revenue_comparison"]["current"] == "0.00"
    assert body["revenue_comparison"]["change_percent"] == "0"
