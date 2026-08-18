import pytest
from httpx import AsyncClient


async def _product_with_variants(client: AsyncClient, token: str, sku: str = "TSHIRT", variant_suffix: str = "") -> dict:
    blk_sku = f"TSHIRT{variant_suffix}-BLK-M"
    wl_sku = f"TSHIRT{variant_suffix}-WHT-L"
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "T-Shirt",
            "sku": sku,
            "category": "Apparel",
            "price": 25,
            "cost_price": 10,
            "stock_quantity": 10,
            "variants": [
                {
                    "sku": blk_sku,
                    "name": "T-Shirt Black M",
                    "attributes": {"color": "Black", "size": "M"},
                    "price": 28,
                    "cost_price": 12,
                    "stock_quantity": 5,
                },
                {
                    "sku": wl_sku,
                    "name": "T-Shirt White L",
                    "attributes": {"color": "White", "size": "L"},
                    "price": 27,
                    "cost_price": 11,
                    "stock_quantity": 3,
                },
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_product_with_variants(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    body = await _product_with_variants(client, token)

    assert len(body["variants"]) == 2
    blk = next(v for v in body["variants"] if v["sku"] == "TSHIRT-BLK-M")
    assert blk["attributes"] == {"color": "Black", "size": "M"}
    assert blk["price"] == "28.00"
    assert blk["stock_quantity"] == 5

    detail = await client.get(f"/api/v1/products/{body['id']}", headers=headers)
    assert len(detail.json()["variants"]) == 2


@pytest.mark.asyncio
async def test_duplicate_variant_sku_across_products_rejected(client, org_a):
    token = org_a["access_token"]
    await _product_with_variants(client, token)

    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Other Shirt",
            "sku": "TSHIRT2",
            "category": "Apparel",
            "price": 20,
            "cost_price": 8,
            "stock_quantity": 5,
            "variants": [
                {
                    "sku": "TSHIRT-BLK-M",
                    "name": "Copy",
                    "attributes": {"color": "Black", "size": "M"},
                    "price": 28,
                    "cost_price": 12,
                    "stock_quantity": 1,
                }
            ],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VARIANT_SKU_TAKEN"


@pytest.mark.asyncio
async def test_update_product_syncs_variants(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    body = await _product_with_variants(client, token)
    pid = body["id"]

    resp = await client.patch(
        f"/api/v1/products/{pid}",
        headers=headers,
        json={
            "variants": [
                {
                    "sku": "TSHIRT-BLK-M",
                    "name": "T-Shirt Black M",
                    "attributes": {"color": "Black", "size": "M"},
                    "price": 30,
                    "cost_price": 12,
                    "stock_quantity": 4,
                    "active": True,
                },
                {
                    "sku": "TSHIRT-GRN-S",
                    "name": "T-Shirt Green S",
                    "attributes": {"color": "Green", "size": "S"},
                    "price": 26,
                    "cost_price": 10,
                    "stock_quantity": 2,
                    "active": True,
                },
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    skus = {v["sku"] for v in resp.json()["variants"]}
    assert skus == {"TSHIRT-BLK-M", "TSHIRT-GRN-S"}
    blk = next(v for v in resp.json()["variants"] if v["sku"] == "TSHIRT-BLK-M")
    assert blk["price"] == "30.00"
    assert blk["stock_quantity"] == 4


@pytest.mark.asyncio
async def test_order_with_variant_uses_variant_price_and_stock(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await _product_with_variants(client, token)
    blk = next(v for v in product["variants"] if v["sku"] == "TSHIRT-BLK-M")

    customer = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"first_name": "Var", "last_name": "Buyer", "email": "var@test.io"},
    )
    resp = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "items": [
                {"product_id": product["id"], "product_variant_id": blk["id"], "quantity": 2}
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["subtotal"] == "56.00"
    assert body["items"][0]["unit_price"] == "28.00"

    detail = await client.get(f"/api/v1/products/{product['id']}", headers=headers)
    variants = {v["sku"]: v for v in detail.json()["variants"]}
    assert variants["TSHIRT-BLK-M"]["stock_quantity"] == 3
    assert variants["TSHIRT-WHT-L"]["stock_quantity"] == 3


@pytest.mark.asyncio
async def test_order_variant_must_belong_to_product(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    p1 = await _product_with_variants(client, token, sku="TSHIRT1", variant_suffix="1")
    p2 = await _product_with_variants(client, token, sku="TSHIRT2", variant_suffix="2")

    customer = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"first_name": "Var", "last_name": "Mix", "email": "mix@test.io"},
    )
    resp = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "items": [
                {
                    "product_id": p1["id"],
                    "product_variant_id": p2["variants"][0]["id"],
                    "quantity": 1,
                }
            ],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VARIANT_NOT_FOUND"


@pytest.mark.asyncio
async def test_storefront_checkout_with_variant(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await _product_with_variants(client, token, sku="TSHIRT3")
    blk = next(v for v in product["variants"] if v["sku"] == "TSHIRT-BLK-M")

    me = (await client.get("/api/v1/auth/me", headers=headers)).json()
    slug = me["organization_slug"]
    assert slug, "org slug missing from /auth/me"

    catalog = await client.get(
        f"/api/v1/stores/{slug}/products/{product['id']}"
    )
    assert catalog.status_code == 200
    variants = {v["sku"]: v for v in catalog.json()["variants"]}
    assert variants["TSHIRT-BLK-M"]["attributes"]["color"] == "Black"

    checkout = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Guest",
            "last_name": "Var",
            "email": "gvar@example.com",
            "items": [
                {"product_id": product["id"], "product_variant_id": blk["id"], "quantity": 1}
            ],
        },
    )
    assert checkout.status_code == 201, checkout.text
    assert checkout.json()["total"] == "28.00"

    orders = await client.get("/api/v1/orders", headers=headers)
    order = next(o for o in orders.json()["items"] if o["order_number"] == checkout.json()["order_number"])
    assert order["items"][0]["unit_price"] == "28.00"
    assert order["items"][0]["product_variant_id"] == blk["id"]


@pytest.mark.asyncio
async def test_cancel_order_restores_variant_stock(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await _product_with_variants(client, token, sku="TSHIRT4")
    blk = next(v for v in product["variants"] if v["sku"] == "TSHIRT-BLK-M")

    customer = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"first_name": "Var", "last_name": "Cancel", "email": "vc@test.io"},
    )
    order = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "items": [
                {"product_id": product["id"], "product_variant_id": blk["id"], "quantity": 2}
            ],
        },
    )
    await client.delete(f"/api/v1/orders/{order.json()['id']}", headers=headers)

    detail = await client.get(f"/api/v1/products/{product['id']}", headers=headers)
    variants = {v["sku"]: v for v in detail.json()["variants"]}
    assert variants["TSHIRT-BLK-M"]["stock_quantity"] == 5
