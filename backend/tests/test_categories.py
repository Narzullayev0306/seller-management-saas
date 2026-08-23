"""Category tree: CRUD, nesting, cycle guards, product linking."""

import pytest

CATEGORY_PAYLOAD = {"name": "Furniture", "slug": "furniture"}


async def _create_category(client, token: str, payload: dict) -> dict:
    resp = await client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_and_get_category(client, org_a):
    cat = await _create_category(client, org_a["access_token"], CATEGORY_PAYLOAD)
    assert cat["slug"] == "furniture"
    assert cat["product_count"] == 0

    resp = await client.get(
        f"/api/v1/categories/{cat['id']}",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Furniture"


@pytest.mark.asyncio
async def test_category_tree_nesting(client, org_a):
    token = org_a["access_token"]
    root = await _create_category(client, token, {"name": "Home"})
    child = await _create_category(
        client, token, {"name": "Sofas", "parent_id": root["id"]}
    )
    await _create_category(
        client, token, {"name": "Tees", "parent_id": child["id"]}
    )

    resp = await client.get(
        "/api/v1/categories/tree",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    tree = resp.json()
    assert len(tree) == 1
    assert tree[0]["name"] == "Home"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "Sofas"
    assert len(tree[0]["children"][0]["children"]) == 1


@pytest.mark.asyncio
async def test_category_slug_deduplicated(client, org_a):
    token = org_a["access_token"]
    first = await _create_category(client, token, {"name": "Chairs"})
    second = await _create_category(client, token, {"name": "Chairs"})
    assert first["slug"] == "chairs"
    assert second["slug"] == "chairs-2"


@pytest.mark.asyncio
async def test_category_cycle_rejected(client, org_a):
    token = org_a["access_token"]
    parent = await _create_category(client, token, {"name": "Parent"})
    child = await _create_category(
        client, token, {"name": "Child", "parent_id": parent["id"]}
    )
    resp = await client.patch(
        f"/api/v1/categories/{parent['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"parent_id": child["id"]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CATEGORY_CYCLE"


@pytest.mark.asyncio
async def test_category_self_parent_rejected(client, org_a):
    cat = await _create_category(client, org_a["access_token"], {"name": "Solo"})
    resp = await client.patch(
        f"/api/v1/categories/{cat['id']}",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
        json={"parent_id": cat["id"]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CATEGORY_SELF_PARENT"


@pytest.mark.asyncio
async def test_delete_guards(client, org_a):
    token = org_a["access_token"]
    cat = await _create_category(client, token, {"name": "Lamps"})
    resp = await client.delete(
        f"/api/v1/categories/{cat['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    child = await _create_category(client, token, {"name": "Desk"})
    await _create_category(client, token, {"name": "Drawer", "parent_id": child["id"]})
    resp = await client.delete(
        f"/api/v1/categories/{child['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CATEGORY_HAS_CHILDREN"


@pytest.mark.asyncio
async def test_delete_blocked_when_products_attached(client, org_a):
    token = org_a["access_token"]
    cat = await _create_category(client, token, {"name": "Cups"})
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Mug",
            "sku": "CAT-MUG",
            "category": "Cups",
            "category_id": cat["id"],
            "price": 9.99,
            "cost_price": 4.0,
            "stock_quantity": 5,
            "low_stock_threshold": 1,
            "status": "active",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["category_id"] == cat["id"]

    resp = await client.delete(
        f"/api/v1/categories/{cat['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CATEGORY_HAS_PRODUCTS"


@pytest.mark.asyncio
async def test_rename_syncs_product_category_name(client, org_a):
    token = org_a["access_token"]
    cat = await _create_category(client, token, {"name": "Old Name"})
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Item",
            "sku": "CAT-SYNC",
            "category": "Old Name",
            "category_id": cat["id"],
            "price": 1.0,
            "cost_price": 0.5,
            "stock_quantity": 2,
            "low_stock_threshold": 0,
            "status": "active",
        },
    )
    assert resp.status_code == 201
    product_id = resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/categories/{cat['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name"},
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["category"] == "New Name"
    assert resp.json()["category_id"] == cat["id"]


@pytest.mark.asyncio
async def test_category_scoped_to_own_org(client, org_a, org_b):
    cat = await _create_category(client, org_a["access_token"], {"name": "A Only"})
    resp = await client.get(
        f"/api/v1/categories/{cat['id']}",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_product_rejects_foreign_category(client, org_a, org_b):
    cat = await _create_category(client, org_b["access_token"], {"name": "B Cat"})
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
        json={
            "name": "Bad",
            "sku": "CAT-FOREIGN",
            "category": "B Cat",
            "category_id": cat["id"],
            "price": 1.0,
            "cost_price": 0.5,
            "stock_quantity": 1,
            "low_stock_threshold": 0,
            "status": "active",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CATEGORY_NOT_FOUND"
