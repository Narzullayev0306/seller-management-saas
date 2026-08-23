"""Purchase orders: create, order, receive (stock in), cancel."""

import pytest


async def _product(client, token: str, sku: str = "PO-1", stock: int = 5) -> dict:
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "PO Product",
            "sku": sku,
            "category": "Furniture",
            "price": 15.0,
            "cost_price": 6.0,
            "stock_quantity": stock,
            "low_stock_threshold": 2,
            "status": "active",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _supplier(client, token: str, name: str = "Supplier Co") -> dict:
    resp = await client.post(
        "/api/v1/suppliers",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "email": "sup@po.io", "phone": "123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_po(client, token: str, product: dict, quantity: int = 10, supplier_id=None) -> dict:
    body = {
        "items": [{"product_id": product["id"], "quantity": quantity, "unit_cost": 4.5}],
    }
    if supplier_id:
        body["supplier_id"] = supplier_id
    resp = await client.post(
        "/api/v1/purchase-orders",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_and_receive_purchase_order(client, org_a):
    token = org_a["access_token"]
    p = await _product(client, token)
    sup = await _supplier(client, token)
    po = await _create_po(client, token, p, quantity=10, supplier_id=sup["id"])

    assert po["status"] == "draft"
    assert po["po_number"].startswith("PO-")
    assert po["supplier_name"] == "Supplier Co"
    assert po["total"] == "45.00"
    assert po["items"][0]["product_name"] == "PO Product"

    # Order it.
    resp = await client.patch(
        f"/api/v1/purchase-orders/{po['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "ordered"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ordered"

    # Receive it: stock increases.
    resp = await client.patch(
        f"/api/v1/purchase-orders/{po['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "received"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "received"

    resp = await client.get(
        f"/api/v1/products/{p['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["stock_quantity"] == 15  # 5 + 10


@pytest.mark.asyncio
async def test_po_number_increments(client, org_a):
    token = org_a["access_token"]
    p = await _product(client, token, sku="PO-2")
    first = await _create_po(client, token, p)
    second = await _create_po(client, token, p)
    assert first["po_number"] == "PO-000001"
    assert second["po_number"] == "PO-000002"


@pytest.mark.asyncio
async def test_received_po_cannot_transition_or_delete(client, org_a):
    token = org_a["access_token"]
    p = await _product(client, token, sku="PO-3")
    po = await _create_po(client, token, p)
    await client.patch(
        f"/api/v1/purchase-orders/{po['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "ordered"},
    )
    await client.patch(
        f"/api/v1/purchase-orders/{po['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "received"},
    )
    resp = await client.patch(
        f"/api/v1/purchase-orders/{po['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "cancelled"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PO_BAD_TRANSITION"

    resp = await client.delete(
        f"/api/v1/purchase-orders/{po['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PO_RECEIVED"


@pytest.mark.asyncio
async def test_foreign_supplier_and_product_rejected(client, org_a, org_b):
    token_a = org_a["access_token"]
    p_b = await _product(client, org_b["access_token"], sku="PO-B")
    sup_b = await _supplier(client, org_b["access_token"], name="B Sup")

    resp = await client.post(
        "/api/v1/purchase-orders",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"supplier_id": sup_b["id"], "items": [{"product_id": p_b["id"], "quantity": 1, "unit_cost": 1.0}]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_org_isolation(client, org_a, org_b):
    p = await _product(client, org_a["access_token"], sku="PO-4")
    po = await _create_po(client, org_a["access_token"], p)
    resp = await client.get(
        f"/api/v1/purchase-orders/{po['id']}",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
    )
    assert resp.status_code == 404
