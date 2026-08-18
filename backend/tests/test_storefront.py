import pytest


@pytest.mark.asyncio
async def test_catalog_lists_active_products(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(3):
        resp = await client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "name": f"Store Item {i}",
                "sku": f"STR-{i}",
                "category": "Gadgets",
                "price": 50 + i,
                "cost_price": 20,
                "stock_quantity": 10,
            },
        )
        assert resp.status_code == 201

    catalog = await client.get("/api/v1/storefront/catalog")
    assert catalog.status_code == 200
    body = catalog.json()
    assert body["total"] >= 3
    names = {p["name"] for p in body["items"]}
    assert "Store Item 0" in names
    assert "Gadgets" in body["categories"]
    assert body["items"][0]["stock_status"] in ("in_stock", "low_stock", "out_of_stock")


@pytest.mark.asyncio
async def test_catalog_filters_and_sorts(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Cheap Widget",
            "sku": "CWT-1",
            "category": "Widgets",
            "price": 10,
            "cost_price": 4,
            "stock_quantity": 5,
        },
    )
    await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Expensive Widget",
            "sku": "EWT-1",
            "category": "Widgets",
            "price": 200,
            "cost_price": 100,
            "stock_quantity": 5,
        },
    )

    filtered = await client.get("/api/v1/storefront/catalog?category=Widgets&sort_by=price_asc")
    items = filtered.json()["items"]
    assert [p["price"] for p in items] == sorted(p["price"] for p in items)
    assert all(p["category"] == "Widgets" for p in items)

    searched = await client.get("/api/v1/storefront/catalog?search=cheap")
    assert all("cheap" in p["name"].lower() for p in searched.json()["items"])


@pytest.mark.asyncio
async def test_product_detail_with_reviews_and_price_history(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Reviewable Thing",
            "sku": "REV-1",
            "category": "Gadgets",
            "price": 99,
            "cost_price": 40,
            "stock_quantity": 8,
        },
    )
    pid = product.json()["id"]

    review = await client.post(
        f"/api/v1/storefront/products/{pid}/reviews",
        json={"customer_name": "Anna Test", "rating": 5, "comment": "Love it!"},
    )
    assert review.status_code == 201
    await client.post(
        f"/api/v1/storefront/products/{pid}/reviews",
        json={"customer_name": "Bob Test", "rating": 3},
    )

    detail = await client.get(f"/api/v1/storefront/products/{pid}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["review_count"] == 2
    assert body["rating"] == "4.0"
    assert len(body["reviews"]) == 2

    updated = await client.patch(
        f"/api/v1/products/{pid}",
        headers=headers,
        json={"price": 89},
    )
    assert updated.status_code == 200
    detail2 = await client.get(f"/api/v1/storefront/products/{pid}")
    assert detail2.json()["price_history"][0]["old_price"] == "99.00"
    assert detail2.json()["price_history"][0]["new_price"] == "89.00"


@pytest.mark.asyncio
async def test_back_in_stock_requests_are_deduplicated(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Sold Out Thing",
            "sku": "SOT-1",
            "category": "Gadgets",
            "price": 5,
            "cost_price": 2,
            "stock_quantity": 0,
        },
    )
    pid = product.json()["id"]
    for _ in range(2):
        resp = await client.post(
            f"/api/v1/storefront/products/{pid}/back-in-stock",
            json={"email": "wait@example.com"},
        )
        assert resp.status_code == 204

    detail = await client.get(f"/api/v1/storefront/products/{pid}")
    assert detail.status_code == 200
    assert detail.json()["stock_status"] == "out_of_stock"


@pytest.mark.asyncio
async def test_guest_checkout_creates_order_and_reserves_stock(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Checkout Thing",
            "sku": "CHK-1",
            "category": "Gadgets",
            "price": 30,
            "cost_price": 12,
            "stock_quantity": 10,
        },
    )
    pid = product.json()["id"]

    checkout = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Guest",
            "last_name": "Shopper",
            "email": "guest@example.com",
            "items": [{"product_id": pid, "quantity": 3}],
        },
    )
    assert checkout.status_code == 201
    body = checkout.json()
    assert body["order_number"].startswith("ORD-")
    assert body["total"] == "90.00"
    assert body["items_count"] == 3

    orders = await client.get("/api/v1/orders", headers=headers)
    assert any(o["order_number"] == body["order_number"] for o in orders.json()["items"])

    overview = await client.get("/api/v1/inventory", headers=headers)
    item = next(p for p in overview.json()["items"] if p["sku"] == "CHK-1")
    assert item["stock_quantity"] == 7

    second = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Guest",
            "last_name": "Shopper",
            "email": "guest@example.com",
            "items": [{"product_id": pid, "quantity": 1}],
        },
    )
    assert second.status_code == 201

    customers = await client.get("/api/v1/customers?search=guest@example.com", headers=headers)
    assert customers.json()["total"] == 1


@pytest.mark.asyncio
async def test_guest_checkout_insufficient_stock(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Low Stock Thing",
            "sku": "LST-1",
            "category": "Gadgets",
            "price": 5,
            "cost_price": 2,
            "stock_quantity": 2,
        },
    )
    resp = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Gus",
            "last_name": "Shoop",
            "email": "g2@example.com",
            "items": [{"product_id": product.json()["id"], "quantity": 99}],
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"


@pytest.mark.asyncio
async def test_brands_and_categories_endpoints(client, org_a):
    brands = await client.get("/api/v1/storefront/brands")
    cats = await client.get("/api/v1/storefront/categories")
    assert brands.status_code == 200
    assert cats.status_code == 200
    assert all("product_count" in b for b in brands.json())
    assert all("product_count" in c for c in cats.json())
