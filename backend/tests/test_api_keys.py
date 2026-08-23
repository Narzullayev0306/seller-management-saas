"""API keys: hashed secrets, scopes, and read-only public endpoints."""

import pytest


async def _create_key(client, token: str, **overrides) -> dict:
    payload = {
        "name": "POS Integration",
        "scopes": ["products.read", "inventory.read"],
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_api_key_lifecycle(client, org_a):
    token = org_a["access_token"]
    key = await _create_key(client, token)
    assert key["key"].startswith("smk_")
    assert key["prefix"].startswith("smk_")
    assert "key" not in key or key["prefix"] in key["key"]

    listed = await client.get(
        "/api/v1/api-keys", headers={"Authorization": f"Bearer {token}"}
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert "key" not in listed.json()[0]

    updated = await client.patch(
        f"/api/v1/api-keys/{key['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

    deleted = await client.delete(
        f"/api/v1/api-keys/{key['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_api_key_rejects_unknown_scopes(client, org_a):
    resp = await client.post(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
        json={"name": "Bad", "scopes": ["system.admin"]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "API_KEY_INVALID_SCOPES"


@pytest.mark.asyncio
async def test_public_endpoints_scope_enforced(client, org_a):
    token = org_a["access_token"]
    key = await _create_key(
        client, token, name="Read Only", scopes=["products.read"]
    )
    headers = {"Authorization": f"Bearer {key['key']}"}

    resp = await client.get("/api/v1/public/products", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []

    resp = await client.get("/api/v1/public/inventory", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "API_KEY_SCOPE_DENIED"

    resp = await client.get("/api/v1/public/products", headers={})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "API_KEY_REQUIRED"

    resp = await client.get(
        "/api/v1/public/products",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "API_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_public_products_scoped_to_org(client, org_a, org_b):
    key = await _create_key(client, org_a["access_token"])
    headers = {"Authorization": f"Bearer {key['key']}"}

    created = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
        json={
            "name": "Gadget",
            "sku": "GDG-1",
            "category": "Electronics",
            "price": "49.90",
            "cost_price": "20.00",
            "stock_quantity": 5,
            "low_stock_threshold": 3,
        },
    )
    assert created.status_code == 201, created.text

    resp = await client.get("/api/v1/public/products", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["sku"] == "GDG-1"

    resp = await client.get(
        f"/api/v1/public/products/{items[0]['id']}", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Gadget"


@pytest.mark.asyncio
async def test_revoked_key_rejected(client, org_a):
    token = org_a["access_token"]
    key = await _create_key(client, token)

    resp = await client.patch(
        f"/api/v1/api-keys/{key['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert resp.status_code == 200

    resp = await client.get(
        "/api/v1/public/products", headers={"Authorization": f"Bearer {key['key']}"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_API_KEY"
