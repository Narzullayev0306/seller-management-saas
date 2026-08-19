import pytest


@pytest.mark.asyncio
async def _create_product(client, token, name, sku, price=25, stock=10):
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "sku": sku,
            "category": "Gadgets",
            "price": price,
            "cost_price": 10,
            "stock_quantity": stock,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_guest_cart_lifecycle(client, org_a):
    product = await _create_product(client, org_a["access_token"], "Cart Thing", "CRT-1")
    pid = product["id"]
    headers = {"X-Cart-Token": "guest-session-123"}

    empty = await client.get("/api/v1/storefront/cart", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["item_count"] == 0

    added = await client.post(
        "/api/v1/storefront/cart/items",
        headers=headers,
        json={"product_id": pid, "quantity": 2},
    )
    assert added.status_code == 201, added.text
    body = added.json()
    assert body["item_count"] == 2
    assert body["subtotal"] == "50.00"
    item = body["items"][0]
    assert item["name"] == "Cart Thing"
    assert item["quantity"] == 2

    re_added = await client.post(
        "/api/v1/storefront/cart/items",
        headers=headers,
        json={"product_id": pid, "quantity": 3},
    )
    assert re_added.json()["item_count"] == 5

    updated = await client.patch(
        f"/api/v1/storefront/cart/items/{item['id']}",
        headers=headers,
        json={"quantity": 4},
    )
    assert updated.status_code == 200
    assert updated.json()["item_count"] == 4

    fetched = await client.get("/api/v1/storefront/cart", headers=headers)
    assert fetched.json()["item_count"] == 4

    removed = await client.delete(
        f"/api/v1/storefront/cart/items/{item['id']}", headers=headers
    )
    assert removed.json()["item_count"] == 0

    added2 = await client.post(
        "/api/v1/storefront/cart/items",
        headers=headers,
        json={"product_id": pid, "quantity": 1},
    )
    assert added2.json()["item_count"] == 1
    cleared = await client.delete("/api/v1/storefront/cart", headers=headers)
    assert cleared.json()["item_count"] == 0


@pytest.mark.asyncio
async def test_cart_requires_identity(client, org_a):
    resp = await client.post(
        "/api/v1/storefront/cart/items",
        json={"product_id": "00000000-0000-0000-0000-000000000001", "quantity": 1},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CART_IDENTITY_REQUIRED"


@pytest.mark.asyncio
async def test_cart_insufficient_stock(client, org_a):
    product = await _create_product(
        client, org_a["access_token"], "Low Cart Thing", "LCT-1", stock=2
    )
    headers = {"X-Cart-Token": "guest-low-stock"}
    resp = await client.post(
        "/api/v1/storefront/cart/items",
        headers=headers,
        json={"product_id": product["id"], "quantity": 5},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"


@pytest.mark.asyncio
async def test_cart_rejects_foreign_product(client, org_a, org_b):
    product_b = await _create_product(
        client, org_b["access_token"], "Other Store Thing", "OST-1"
    )
    headers = {"X-Cart-Token": "guest-foreign"}
    resp = await client.post(
        "/api/v1/storefront/cart/items",
        headers=headers,
        json={"product_id": product_b["id"], "quantity": 1},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_customer_cart_and_guest_merge(client, org_a):
    product = await _create_product(client, org_a["access_token"], "Merge Thing", "MRG-1")
    pid = product["id"]
    guest_headers = {"X-Cart-Token": "guest-to-merge"}

    await client.post(
        "/api/v1/storefront/cart/items",
        headers=guest_headers,
        json={"product_id": pid, "quantity": 2},
    )

    reg = await client.post(
        "/api/v1/storefront/auth/register",
        json={
            "first_name": "Mia",
            "last_name": "Shopper",
            "email": "mia@shop.io",
            "password": "StrongPass123",
        },
    )
    token = reg.json()["access_token"]

    merged = await client.post(
        "/api/v1/storefront/cart/items",
        headers={**guest_headers, "Authorization": f"Bearer {token}"},
        json={"product_id": pid, "quantity": 1},
    )
    assert merged.status_code == 201
    assert merged.json()["item_count"] == 3

    account_cart = await client.get(
        "/api/v1/storefront/cart",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert account_cart.json()["item_count"] == 3

    guest_cart = await client.get("/api/v1/storefront/cart", headers=guest_headers)
    assert guest_cart.json()["item_count"] == 0


@pytest.mark.asyncio
async def test_checkout_uses_customer_account_and_clears_cart(client, org_a):
    product = await _create_product(
        client, org_a["access_token"], "Account Checkout", "ACC-1", stock=10
    )
    pid = product["id"]

    reg = await client.post(
        "/api/v1/storefront/auth/register",
        json={
            "first_name": "Nico",
            "last_name": "Shopper",
            "email": "nico@shop.io",
            "password": "StrongPass123",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/storefront/cart/items",
        headers=headers,
        json={"product_id": pid, "quantity": 2},
    )
    cart_before = await client.get("/api/v1/storefront/cart", headers=headers)
    assert cart_before.json()["item_count"] == 2

    checkout = await client.post(
        "/api/v1/storefront/checkout",
        headers=headers,
        json={
            "first_name": "Nico Updated",
            "last_name": "Shopper",
            "email": "nico@shop.io",
            "items": [{"product_id": pid, "quantity": 2}],
        },
    )
    assert checkout.status_code == 201, checkout.text
    assert checkout.json()["total"] == "50.00"

    cart_after = await client.get("/api/v1/storefront/cart", headers=headers)
    assert cart_after.json()["item_count"] == 0

    me = await client.get("/api/v1/storefront/auth/me", headers=headers)
    assert me.json()["first_name"] == "Nico Updated"

    customers = await client.get(
        "/api/v1/customers?search=nico@shop.io",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
    )
    assert customers.json()["total"] == 1
    customer = customers.json()["items"][0]
    assert customer["first_name"] == "Nico Updated"


@pytest.mark.asyncio
async def test_guest_checkout_clears_guest_cart(client, org_a):
    product = await _create_product(
        client, org_a["access_token"], "Guest Cart Checkout", "GCC-1", stock=10
    )
    headers = {"X-Cart-Token": "guest-checkout-token"}
    await client.post(
        "/api/v1/storefront/cart/items",
        headers=headers,
        json={"product_id": product["id"], "quantity": 1},
    )
    checkout = await client.post(
        "/api/v1/storefront/checkout",
        headers=headers,
        json={
            "first_name": "Guest",
            "last_name": "Buyer",
            "email": "gb@example.com",
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
    )
    assert checkout.status_code == 201
    cart = await client.get("/api/v1/storefront/cart", headers=headers)
    assert cart.json()["item_count"] == 0


@pytest.mark.asyncio
async def test_slug_cart_routes(client, org_a):
    product = await _create_product(client, org_a["access_token"], "Slug Cart", "SLC-1")
    headers = {"X-Cart-Token": "slug-guest"}
    added = await client.post(
        "/api/v1/stores/org-a/cart/items",
        headers=headers,
        json={"product_id": product["id"], "quantity": 1},
    )
    assert added.status_code == 201
    fetched = await client.get("/api/v1/stores/org-a/cart", headers=headers)
    assert fetched.json()["item_count"] == 1
