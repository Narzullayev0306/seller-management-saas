import pytest


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _payload(**overrides):
    data = {
        "name": "Ergonomic Chair",
        "sku": "CHAIR-01",
        "category": "Furniture",
        "price": 149.99,
        "cost_price": 90,
        "stock_quantity": 25,
        "low_stock_threshold": 5,
        "status": "active",
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_create_and_get_product(client, org_a):
    h = await _headers(org_a["access_token"])
    created = await client.post("/api/v1/products", headers=h, json=await _payload())
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Ergonomic Chair"
    assert body["stock_status"] == "in_stock"

    fetched = await client.get(f"/api/v1/products/{body['id']}", headers=h)
    assert fetched.status_code == 200
    assert fetched.json()["sku"] == "CHAIR-01"


@pytest.mark.asyncio
async def test_duplicate_sku_conflict(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post("/api/v1/products", headers=h, json=await _payload())
    resp = await client.post(
        "/api/v1/products", headers=h, json=await _payload(name="Different")
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SKU_TAKEN"


@pytest.mark.asyncio
async def test_update_product(client, org_a):
    h = await _headers(org_a["access_token"])
    created = (await client.post("/api/v1/products", headers=h, json=await _payload())).json()
    resp = await client.patch(
        f"/api/v1/products/{created['id']}", headers=h, json={"price": 199.99, "category": "Office"}
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == "199.99"
    assert resp.json()["category"] == "Office"


@pytest.mark.asyncio
async def test_update_stock_records_movement(client, org_a):
    h = await _headers(org_a["access_token"])
    created = (await client.post("/api/v1/products", headers=h, json=await _payload())).json()
    resp = await client.patch(
        f"/api/v1/products/{created['id']}", headers=h, json={"stock_quantity": 40}
    )
    assert resp.status_code == 200
    assert resp.json()["stock_quantity"] == 40

    movements = await client.get("/api/v1/inventory/movements", headers=h)
    types = [m["type"] for m in movements.json()["items"]]
    assert "purchase" in types
    assert "adjustment" in types


@pytest.mark.asyncio
async def test_negative_stock_blocked(client, org_a):
    h = await _headers(org_a["access_token"])
    created = (await client.post("/api/v1/products", headers=h, json=await _payload())).json()
    resp = await client.patch(
        f"/api/v1/products/{created['id']}", headers=h, json={"stock_quantity": -5}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_negative_price_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.post("/api/v1/products", headers=h, json=await _payload(price=-10))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_status_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.post("/api/v1/products", headers=h, json=await _payload(status="weird"))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_deactivate_product(client, org_a):
    h = await _headers(org_a["access_token"])
    created = (await client.post("/api/v1/products", headers=h, json=await _payload())).json()
    resp = await client.delete(f"/api/v1/products/{created['id']}", headers=h)
    assert resp.status_code == 204

    fetched = (await client.get(f"/api/v1/products/{created['id']}", headers=h)).json()
    assert fetched["status"] == "inactive"


@pytest.mark.asyncio
async def test_stock_status_filters(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post("/api/v1/products", headers=h, json=await _payload(sku="SKU-1", stock_quantity=50, low_stock_threshold=5))
    await client.post("/api/v1/products", headers=h, json=await _payload(sku="SKU-2", name="Low Item", stock_quantity=3, low_stock_threshold=10))
    await client.post("/api/v1/products", headers=h, json=await _payload(sku="SKU-3", name="Empty Item", stock_quantity=0))

    low = await client.get("/api/v1/products?stock_status=low_stock", headers=h)
    out = await client.get("/api/v1/products?stock_status=out_of_stock", headers=h)
    assert low.json()["total"] == 1
    assert out.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_and_category_filter(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post("/api/v1/products", headers=h, json=await _payload(sku="K-1"))
    await client.post("/api/v1/products", headers=h, json=await _payload(sku="K-2", name="Standing Desk", category="Office"))

    search = await client.get("/api/v1/products?search=desk", headers=h)
    assert search.json()["total"] == 1

    cat = await client.get("/api/v1/products?category=Office", headers=h)
    assert cat.json()["total"] == 1

    combined = await client.get("/api/v1/products?category=Office&search=chair", headers=h)
    assert combined.json()["total"] == 0
