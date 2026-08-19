import pytest


@pytest.mark.asyncio
async def test_customer_register_login_and_me(client, org_a):
    resp = await client.post(
        "/api/v1/storefront/auth/register",
        json={
            "first_name": "Anna",
            "last_name": "Shopper",
            "email": "anna@shop.io",
            "password": "StrongPass123",
            "phone": "+998901234567",
        },
    )
    assert resp.status_code == 201, resp.text
    tokens = resp.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/api/v1/storefront/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["email"] == "anna@shop.io"
    assert body["first_name"] == "Anna"
    assert body["last_name"] == "Shopper"
    assert body["phone"] == "+998901234567"
    assert body["customer_id"]

    login = await client.post(
        "/api/v1/storefront/auth/login",
        json={"email": "ANNA@shop.io", "password": "StrongPass123"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]

    bad = await client.post(
        "/api/v1/storefront/auth/login",
        json={"email": "anna@shop.io", "password": "WrongPass1"},
    )
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_customer_register_duplicate_email_conflict(client, org_a):
    payload = {
        "first_name": "Bob",
        "last_name": "Shopper",
        "email": "bob@shop.io",
        "password": "StrongPass123",
    }
    first = await client.post("/api/v1/storefront/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/storefront/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.asyncio
async def test_customer_refresh_and_logout(client, org_a):
    reg = await client.post(
        "/api/v1/storefront/auth/register",
        json={
            "first_name": "Carl",
            "last_name": "Shopper",
            "email": "carl@shop.io",
            "password": "StrongPass123",
        },
    )
    refresh = reg.json()["refresh_token"]

    rotated = await client.post(
        "/api/v1/storefront/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert rotated.status_code == 200
    new_refresh = rotated.json()["refresh_token"]
    assert new_refresh != refresh

    replayed = await client.post(
        "/api/v1/storefront/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert replayed.status_code == 401

    logout = await client.post(
        "/api/v1/storefront/auth/logout",
        json={"refresh_token": new_refresh},
    )
    assert logout.status_code == 204

    after = await client.post(
        "/api/v1/storefront/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_customer_token_cannot_access_admin_api(client, org_a):
    reg = await client.post(
        "/api/v1/storefront/auth/register",
        json={
            "first_name": "Dana",
            "last_name": "Shopper",
            "email": "dana@shop.io",
            "password": "StrongPass123",
        },
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 401
    orders = await client.get("/api/v1/orders", headers=headers)
    assert orders.status_code == 401


@pytest.mark.asyncio
async def test_customer_accounts_are_org_scoped(client, org_a, org_b):
    payload = {
        "first_name": "Eva",
        "last_name": "Shopper",
        "email": "eva@shop.io",
        "password": "StrongPass123",
    }
    reg = await client.post("/api/v1/stores/org-a/auth/register", json=payload)
    assert reg.status_code == 201

    same_email_other_org = await client.post(
        "/api/v1/stores/org-b/auth/register", json=payload
    )
    assert same_email_other_org.status_code == 201

    login = await client.post(
        "/api/v1/stores/org-a/auth/login",
        json={"email": "eva@shop.io", "password": "StrongPass123"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get("/api/v1/stores/org-a/auth/me", headers=headers)
    assert me.status_code == 200

    wrong_store = await client.get("/api/v1/stores/org-b/auth/me", headers=headers)
    assert wrong_store.status_code == 400


@pytest.mark.asyncio
async def test_customer_profile_update(client, org_a):
    reg = await client.post(
        "/api/v1/storefront/auth/register",
        json={
            "first_name": "Frank",
            "last_name": "Shopper",
            "email": "frank@shop.io",
            "password": "StrongPass123",
        },
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    updated = await client.patch(
        "/api/v1/storefront/auth/me",
        headers=headers,
        json={
            "first_name": "Franklin",
            "phone": "+998900000000",
            "address": "12 Main Street",
        },
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["first_name"] == "Franklin"
    assert body["phone"] == "+998900000000"
    assert body["address"] == "12 Main Street"

    wrong_pw = await client.patch(
        "/api/v1/storefront/auth/me",
        headers=headers,
        json={"current_password": "nope", "password": "NewPass1234"},
    )
    assert wrong_pw.status_code == 400
    assert wrong_pw.json()["error"]["code"] == "INVALID_PASSWORD"

    changed = await client.patch(
        "/api/v1/storefront/auth/me",
        headers=headers,
        json={"current_password": "StrongPass123", "password": "NewPass1234"},
    )
    assert changed.status_code == 200

    old_login = await client.post(
        "/api/v1/storefront/auth/login",
        json={"email": "frank@shop.io", "password": "StrongPass123"},
    )
    assert old_login.status_code == 401
    new_login = await client.post(
        "/api/v1/storefront/auth/login",
        json={"email": "frank@shop.io", "password": "NewPass1234"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_slug_customer_auth_routes(client, org_a):
    resp = await client.post(
        "/api/v1/stores/org-a/auth/register",
        json={
            "first_name": "Gina",
            "last_name": "Shopper",
            "email": "gina@shop.io",
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 201, resp.text
    tokens = resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/api/v1/stores/org-a/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "gina@shop.io"

    wrong_store = await client.get("/api/v1/stores/does-not-exist/auth/me", headers=headers)
    assert wrong_store.status_code == 404
