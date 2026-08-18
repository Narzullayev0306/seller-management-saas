import pytest
from httpx import AsyncClient


async def _product(client: AsyncClient, token: str, price: float = 100, stock: int = 20) -> str:
    resp = await client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": f"Coupon Product {price}",
            "sku": f"CPN-{price}",
            "category": "Gadgets",
            "price": price,
            "cost_price": 30,
            "stock_quantity": stock,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _coupon(client: AsyncClient, token: str, code: str = "SAVE10", **overrides) -> dict:
    payload = {
        "code": code,
        "discount_type": "percent",
        "discount_value": 10,
        "min_subtotal": 0,
        "max_redemptions": None,
        "max_per_customer": None,
        "active": True,
    }
    payload.update(overrides)
    resp = await client.post(
        "/api/v1/coupons",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _customer(client: AsyncClient, token: str, email: str = "coup@test.io") -> str:
    resp = await client.post(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "Coup", "last_name": "Buyer", "email": email},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_and_list_coupons(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    await _coupon(client, token, "SAVE10")
    await _coupon(client, token, "FLAT5", discount_type="fixed", discount_value=5)

    listing = await client.get("/api/v1/coupons", headers=headers)
    assert listing.status_code == 200
    codes = {c["code"] for c in listing.json()["items"]}
    assert codes == {"SAVE10", "FLAT5"}


@pytest.mark.asyncio
async def test_coupon_code_case_insensitive_unique(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    created = await _coupon(client, token, "save10")
    assert created["code"] == "SAVE10"

    dup = await client.post(
        "/api/v1/coupons",
        headers=headers,
        json={
            "code": "Save10",
            "discount_type": "percent",
            "discount_value": 20,
        },
    )
    assert dup.status_code == 400
    assert dup.json()["error"]["code"] == "COUPON_EXISTS"


@pytest.mark.asyncio
async def test_checkout_with_percent_coupon(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pid = await _product(client, token, price=100)
    await _coupon(client, token, "SAVE10")

    checkout = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Coup",
            "last_name": "Guest",
            "email": "cg@example.com",
            "coupon_code": "save10",
            "items": [{"product_id": pid, "quantity": 2}],
        },
    )
    assert checkout.status_code == 201, checkout.text
    body = checkout.json()
    assert body["total"] == "180.00"
    assert body["discount"] == "20.00"
    assert body["coupon_code"] == "save10"

    orders = await client.get("/api/v1/orders", headers=headers)
    order = next(o for o in orders.json()["items"] if o["order_number"] == body["order_number"])
    assert order["discount"] == "20.00"


@pytest.mark.asyncio
async def test_checkout_fixed_coupon_capped_at_subtotal(client, org_a):
    token = org_a["access_token"]
    pid = await _product(client, token, price=5)
    await _coupon(client, token, "BIG5", discount_type="fixed", discount_value=50)

    checkout = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Coup",
            "last_name": "Guest",
            "email": "cg2@example.com",
            "coupon_code": "BIG5",
            "items": [{"product_id": pid, "quantity": 1}],
        },
    )
    assert checkout.status_code == 201, checkout.text
    assert checkout.json()["total"] == "0.00"


@pytest.mark.asyncio
async def test_coupon_min_subtotal_enforced(client, org_a):
    token = org_a["access_token"]
    pid = await _product(client, token, price=10)
    await _coupon(client, token, "MIN50", min_subtotal=50)

    checkout = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Coup",
            "last_name": "Guest",
            "email": "cg3@example.com",
            "coupon_code": "MIN50",
            "items": [{"product_id": pid, "quantity": 1}],
        },
    )
    assert checkout.status_code == 400
    assert checkout.json()["error"]["code"] == "COUPON_MIN_SUBTOTAL"


@pytest.mark.asyncio
async def test_coupon_max_redemptions_enforced(client, org_a):
    token = org_a["access_token"]
    pid = await _product(client, token, price=100)
    await _coupon(client, token, "ONCE", max_redemptions=1)

    def payload(email):
        return {
            "first_name": "Coup",
            "last_name": "Guest",
            "email": email,
            "coupon_code": "ONCE",
            "items": [{"product_id": pid, "quantity": 1}],
        }

    first = await client.post("/api/v1/storefront/checkout", json=payload("once1@example.com"))
    assert first.status_code == 201
    second = await client.post("/api/v1/storefront/checkout", json=payload("once2@example.com"))
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "COUPON_USED_UP"


@pytest.mark.asyncio
async def test_coupon_validate_endpoint(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    await _coupon(client, token, "SAVE10")

    ok = await client.get("/api/v1/coupons/validate?code=save10&subtotal=100", headers=headers)
    assert ok.status_code == 200
    assert ok.json()["valid"] is True
    assert ok.json()["discount_type"] == "percent"

    bad = await client.get("/api/v1/coupons/validate?code=NOPE", headers=headers)
    assert bad.status_code == 200
    assert bad.json()["valid"] is False
    assert bad.json()["message"] == "COUPON_NOT_FOUND"


@pytest.mark.asyncio
async def test_admin_order_with_coupon(client, org_a):
    token = org_a["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pid = await _product(client, token, price=100)
    await _coupon(client, token, "ADM10")
    cid = await _customer(client, token)

    resp = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": cid,
            "coupon_code": "adm10",
            "items": [{"product_id": pid, "quantity": 1}],
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["discount"] == "10.00"
    assert resp.json()["total"] == "90.00"


@pytest.mark.asyncio
async def test_expired_coupon_rejected(client, org_a):
    from datetime import UTC, datetime, timedelta

    token = org_a["access_token"]
    pid = await _product(client, token, price=100)
    await _coupon(
        client, token, "OLDPP",
        expires_at=(datetime.now(UTC) - timedelta(days=1)).isoformat(),
    )

    checkout = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Coup",
            "last_name": "Guest",
            "email": "cg4@example.com",
            "coupon_code": "OLDPP",
            "items": [{"product_id": pid, "quantity": 1}],
        },
    )
    assert checkout.status_code == 400
    assert checkout.json()["error"]["code"] == "COUPON_EXPIRED"


@pytest.mark.asyncio
async def test_coupon_scoped_to_org(client, org_a, org_b):
    token_a = org_a["access_token"]
    await _coupon(client, token_a, "AONLY")

    pid = await _product(client, token_a, price=100)
    checkout = await client.post(
        "/api/v1/storefront/checkout",
        json={
            "first_name": "Coup",
            "last_name": "Guest",
            "email": "cg5@example.com",
            "coupon_code": "AONLY",
            "items": [{"product_id": pid, "quantity": 1}],
        },
    )
    assert checkout.status_code == 201

    other = await client.get(
        "/api/v1/coupons?search=AONLY",
        headers={"Authorization": f"Bearer {org_b['access_token']}"},
    )
    assert other.json()["total"] == 0


@pytest.mark.asyncio
async def test_coupon_requires_coupons_permission(client, org_a):
    from tests.conftest import create_user, login

    token = org_a["access_token"]
    await create_user(client, token, "seller-only@x.io", "seller")

    seller_login = await login(client, "seller-only@x.io", "Pass12345")
    resp = await client.post(
        "/api/v1/coupons",
        headers={"Authorization": f"Bearer {seller_login['access_token']}"},
        json={"code": "NOPE", "discount_type": "percent", "discount_value": 10},
    )
    assert resp.status_code == 403
