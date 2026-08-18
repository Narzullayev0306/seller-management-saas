import pytest


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _seed(client, token: str, n: int = 10):
    h = await _headers(token)
    for i in range(n):
        await client.post(
            "/api/v1/products",
            headers=h,
            json={"name": f"Item {i}", "sku": f"PG-{i}", "category": "Tools", "price": 10 + i, "cost_price": 5, "stock_quantity": 50},
        )


@pytest.mark.asyncio
async def test_pagination_envelope(client, org_a):
    h = await _headers(org_a["access_token"])
    await _seed(client, org_a["access_token"], n=10)

    page1 = await client.get("/api/v1/products?page=1&page_size=4", headers=h)
    body = page1.json()
    assert body["total"] == 10
    assert body["total_pages"] == 3
    assert body["page"] == 1
    assert len(body["items"]) == 4

    page3 = await client.get("/api/v1/products?page=3&page_size=4", headers=h)
    assert len(page3.json()["items"]) == 2

    beyond = await client.get("/api/v1/products?page=99&page_size=4", headers=h)
    assert beyond.json()["items"] == []
    assert beyond.json()["total_pages"] == 3


@pytest.mark.asyncio
async def test_pagination_params_validated(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.get("/api/v1/products?page=0", headers=h)
    assert resp.status_code == 422

    resp = await client.get("/api/v1/products?page_size=500", headers=h)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_sorting(client, org_a):
    h = await _headers(org_a["access_token"])
    await _seed(client, org_a["access_token"], n=5)

    asc = await client.get("/api/v1/products?sort_by=price&sort_order=asc", headers=h)
    prices = [float(i["price"]) for i in asc.json()["items"]]
    assert prices == sorted(prices)

    desc = await client.get("/api/v1/products?sort_by=price&sort_order=desc", headers=h)
    prices = [float(i["price"]) for i in desc.json()["items"]]
    assert prices == sorted(prices, reverse=True)


@pytest.mark.asyncio
async def test_invalid_sort_column_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.get(
        "/api/v1/products?sort_by=password_hash", headers=h
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_sort_order_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.get("/api/v1/products?sort_order=sideways", headers=h)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pagination_applies_to_all_lists(client, org_a):
    h = await _headers(org_a["access_token"])
    await _seed(client, org_a["access_token"], n=10)

    for path in ["/api/v1/products", "/api/v1/sellers", "/api/v1/customers", "/api/v1/orders", "/api/v1/inventory"]:
        resp = await client.get(f"{path}?page=1&page_size=2", headers=h)
        assert resp.status_code == 200, path
        body = resp.json()
        assert "items" in body and "total" in body and "total_pages" in body
        assert len(body["items"]) <= 2
