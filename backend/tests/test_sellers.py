import pytest


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _payload(**overrides):
    data = {
        "first_name": "Aziz",
        "last_name": "Karimov",
        "email": "aziz@x.io",
        "phone": "+998901112233",
        "status": "active",
        "commission_rate": 7,
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_create_and_get_seller(client, org_a):
    h = await _headers(org_a["access_token"])
    created = await client.post("/api/v1/sellers", headers=h, json=await _payload())
    assert created.status_code == 201
    body = created.json()
    assert body["commission_rate"] == "7.00"

    fetched = await client.get(f"/api/v1/sellers/{body['id']}", headers=h)
    assert fetched.status_code == 200


@pytest.mark.asyncio
async def test_duplicate_seller_email(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post("/api/v1/sellers", headers=h, json=await _payload())
    resp = await client.post(
        "/api/v1/sellers", headers=h, json=await _payload(first_name="Other")
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.asyncio
async def test_seller_email_unique_per_org(client, org_a, org_b):
    h_a = await _headers(org_a["access_token"])
    h_b = await _headers(org_b["access_token"])
    await client.post("/api/v1/sellers", headers=h_a, json=await _payload())
    resp = await client.post(
        "/api/v1/sellers", headers=h_b, json=await _payload(first_name="Other Org")
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_seller(client, org_a):
    h = await _headers(org_a["access_token"])
    created = (await client.post("/api/v1/sellers", headers=h, json=await _payload())).json()
    resp = await client.patch(
        f"/api/v1/sellers/{created['id']}", headers=h, json={"status": "suspended", "commission_rate": 10}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "suspended"
    assert resp.json()["commission_rate"] == "10.00"


@pytest.mark.asyncio
async def test_invalid_commission_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.post(
        "/api/v1/sellers", headers=h, json=await _payload(commission_rate=150)
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_status_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.post("/api/v1/sellers", headers=h, json=await _payload(status="ghost"))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_deactivate_seller(client, org_a):
    h = await _headers(org_a["access_token"])
    created = (await client.post("/api/v1/sellers", headers=h, json=await _payload())).json()
    resp = await client.delete(f"/api/v1/sellers/{created['id']}", headers=h)
    assert resp.status_code == 204

    fetched = (await client.get(f"/api/v1/sellers/{created['id']}", headers=h)).json()
    assert fetched["status"] == "inactive"


@pytest.mark.asyncio
async def test_status_filter_and_search(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post("/api/v1/sellers", headers=h, json=await _payload())
    await client.post(
        "/api/v1/sellers", headers=h, json=await _payload(first_name="Jasur", email="j@x.io", status="inactive")
    )

    active = await client.get("/api/v1/sellers?status=active", headers=h)
    assert active.json()["total"] == 1

    search = await client.get("/api/v1/sellers?search=jasur", headers=h)
    assert search.json()["total"] == 1


@pytest.mark.asyncio
async def test_seller_stats_endpoint(client, org_a):
    h = await _headers(org_a["access_token"])
    seller = (await client.post("/api/v1/sellers", headers=h, json=await _payload())).json()
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={"name": "Widget", "sku": "W-1", "category": "T", "price": 50, "cost_price": 20, "stock_quantity": 10},
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers", headers=h, json={"first_name": "C", "last_name": "D", "email": "cd@x.io"}
        )
    ).json()
    order = await client.post(
        "/api/v1/orders",
        headers=h,
        json={"seller_id": seller["id"], "customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 2}]},
    )
    assert order.status_code == 201
    for status in ("confirmed", "processing", "shipped", "delivered"):
        resp = await client.patch(
            f"/api/v1/orders/{order.json()['id']}", headers=h, json={"status": status}
        )
        assert resp.status_code == 200, resp.text

    stats = await client.get(f"/api/v1/sellers/{seller['id']}/stats", headers=h)
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_orders"] == 1
    assert body["total_sales"] == "100.00"
    assert body["total_commission"] == "7.00"
    assert len(body["recent_orders"]) == 1
    assert len(body["performance"]) == 1
