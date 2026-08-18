import pytest


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _product(client, token: str, stock: int = 30) -> dict:
    resp = await client.post(
        "/api/v1/products",
        headers=await _headers(token),
        json={
            "name": "Inventory Item",
            "sku": f"INV-{stock}",
            "category": "Tools",
            "price": 20,
            "cost_price": 8,
            "stock_quantity": stock,
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_purchase_increases_stock(client, org_a):
    h = await _headers(org_a["access_token"])
    product = await _product(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "purchase", "quantity": 50, "reason": "new batch"},
    )
    assert resp.status_code == 201
    assert resp.json()["stock_quantity"] == 80


@pytest.mark.asyncio
async def test_adjustment_decreases_stock(client, org_a):
    h = await _headers(org_a["access_token"])
    product = await _product(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "adjustment", "quantity": 10, "reason": "damaged"},
    )
    assert resp.status_code == 201
    assert resp.json()["stock_quantity"] == 20


@pytest.mark.asyncio
async def test_decrease_below_zero_blocked(client, org_a):
    h = await _headers(org_a["access_token"])
    product = await _product(client, org_a["access_token"], stock=5)
    resp = await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "adjustment", "quantity": 99, "reason": "oops"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"


@pytest.mark.asyncio
async def test_invalid_movement_type_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    product = await _product(client, org_a["access_token"])
    resp = await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "teleport", "quantity": 5, "reason": "x"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_movement_history_records_types(client, org_a):
    h = await _headers(org_a["access_token"])
    product = await _product(client, org_a["access_token"], stock=10)
    await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "purchase", "quantity": 20, "reason": "restock"},
    )
    await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "adjustment", "quantity": 5, "reason": "damage"},
    )

    movements = await client.get("/api/v1/inventory/movements?product_id=" + product["id"], headers=h)
    assert movements.status_code == 200
    body = movements.json()
    assert body["total"] == 3
    types = sorted(m["type"] for m in body["items"])
    assert types == ["adjustment", "purchase", "purchase"]


@pytest.mark.asyncio
async def test_stock_overview_low_and_out_filters(client, org_a):
    h = await _headers(org_a["access_token"])
    await _product(client, org_a["access_token"], stock=100)
    low = await client.post(
        "/api/v1/products",
        headers=h,
        json={"name": "Low Item", "sku": "LOW-1", "category": "T", "price": 1, "cost_price": 1, "stock_quantity": 4, "low_stock_threshold": 10},
    )
    out = await client.post(
        "/api/v1/products",
        headers=h,
        json={"name": "Out Item", "sku": "OUT-1", "category": "T", "price": 1, "cost_price": 1, "stock_quantity": 0},
    )
    assert low.status_code == 201 and out.status_code == 201

    overview = await client.get("/api/v1/inventory", headers=h)
    assert overview.json()["total"] == 3

    low_only = await client.get("/api/v1/inventory?stock_status=low_stock", headers=h)
    assert low_only.json()["total"] == 1
    assert low_only.json()["items"][0]["sku"] == "LOW-1"

    out_only = await client.get("/api/v1/inventory?stock_status=out_of_stock", headers=h)
    assert out_only.json()["total"] == 1
    assert out_only.json()["items"][0]["sku"] == "OUT-1"


@pytest.mark.asyncio
async def test_movement_ledger_previous_and_new_stock(client, org_a):
    h = await _headers(org_a["access_token"])
    product = await _product(client, org_a["access_token"], stock=10)
    await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "purchase", "quantity": 20, "reason": "restock"},
    )
    await client.post(
        "/api/v1/inventory/adjustments",
        headers=h,
        json={"product_id": product["id"], "type": "adjustment", "quantity": 5, "reason": "damage"},
    )

    movements = await client.get(
        "/api/v1/inventory/movements?product_id=" + product["id"],
        headers=h,
    )
    assert movements.status_code == 200
    items = sorted(
        movements.json()["items"],
        key=lambda m: (m["created_at"], m["id"]),
    )
    assert items[0]["type"] == "purchase"
    assert items[0]["previous_stock"] == 0
    assert items[0]["new_stock"] == 10
    assert items[1]["type"] == "purchase"
    assert items[1]["previous_stock"] == 10
    assert items[1]["new_stock"] == 30
    assert items[2]["type"] == "adjustment"
    assert items[2]["previous_stock"] == 30
    assert items[2]["new_stock"] == 25


@pytest.mark.asyncio
async def test_sale_movement_is_internal_only(client, org_a):
    h = await _headers(org_a["access_token"])
    product = await _product(client, org_a["access_token"], stock=10)
    customer = (
        await client.post(
            "/api/v1/customers", headers=h, json={"first_name": "A", "last_name": "B", "email": "ab3@x.io"}
        )
    ).json()
    await client.post(
        "/api/v1/orders",
        headers=h,
        json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 2}]},
    )
    movements = await client.get("/api/v1/inventory/movements", headers=h)
    types = [m["type"] for m in movements.json()["items"]]
    assert "sale" in types
    assert any(m["quantity"] < 0 for m in movements.json()["items"])
