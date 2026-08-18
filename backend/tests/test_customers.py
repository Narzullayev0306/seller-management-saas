import pytest


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_update_customer(client, org_a):
    h = await _headers(org_a["access_token"])
    created = await client.post(
        "/api/v1/customers",
        headers=h,
        json={"first_name": "Malika", "last_name": "Saidova", "email": "malika@x.io", "phone": "+998901223344"},
    )
    assert created.status_code == 201
    body = created.json()

    updated = await client.patch(
        f"/api/v1/customers/{body['id']}", headers=h, json={"address": "Tashkent, Labzak 5"}
    )
    assert updated.status_code == 200
    assert updated.json()["address"] == "Tashkent, Labzak 5"


@pytest.mark.asyncio
async def test_delete_customer_without_orders(client, org_a):
    h = await _headers(org_a["access_token"])
    created = (
        await client.post(
            "/api/v1/customers", headers=h, json={"first_name": "A", "last_name": "B", "email": "ab@x.io"}
        )
    ).json()
    resp = await client.delete(f"/api/v1/customers/{created['id']}", headers=h)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_customer_with_orders_blocked(client, org_a):
    h = await _headers(org_a["access_token"])
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={"name": "W", "sku": "W1", "category": "T", "price": 10, "cost_price": 4, "stock_quantity": 9},
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers", headers=h, json={"first_name": "A", "last_name": "B", "email": "ab2@x.io"}
        )
    ).json()
    await client.post(
        "/api/v1/orders",
        headers=h,
        json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
    )
    resp = await client.delete(f"/api/v1/customers/{customer['id']}", headers=h)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CUSTOMER_HAS_ORDERS"


@pytest.mark.asyncio
async def test_customer_search_and_sort(client, org_a):
    h = await _headers(org_a["access_token"])
    await client.post("/api/v1/customers", headers=h, json={"first_name": "Zebo", "last_name": "Aliyeva", "email": "z@x.io"})
    await client.post("/api/v1/customers", headers=h, json={"first_name": "Bek", "last_name": "Rasulov", "email": "b@x.io"})

    search = await client.get("/api/v1/customers?search=zebo", headers=h)
    assert search.json()["total"] == 1

    sorted_asc = await client.get("/api/v1/customers?sort_by=first_name&sort_order=asc", headers=h)
    names = [i["first_name"] for i in sorted_asc.json()["items"]]
    assert names == sorted(names)


@pytest.mark.asyncio
async def test_invalid_email_rejected(client, org_a):
    h = await _headers(org_a["access_token"])
    resp = await client.post(
        "/api/v1/customers", headers=h, json={"first_name": "A", "last_name": "B", "email": "not-an-email"}
    )
    assert resp.status_code == 422
