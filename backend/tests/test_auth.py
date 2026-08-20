import pytest


@pytest.mark.asyncio
async def test_register_returns_tokens(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "NewCo",
            "full_name": "Ali Valiyev",
            "email": "ali@newco.io",
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_creates_customer_role(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Buyer Botir",
            "email": "botir@buyer.io",
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 201
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {resp.json()['access_token']}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert [r["code"] for r in body["roles"]] == ["customer"]
    assert body["permissions"] == []


@pytest.mark.asyncio
async def test_customer_role_is_not_admin(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Buyer Lola",
            "email": "lola@buyer.io",
            "password": "StrongPass123",
        },
    )
    token = resp.json()["access_token"]
    users = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert users.status_code == 403
    dash = await client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dash.status_code == 403


@pytest.mark.asyncio
async def test_register_duplicate_email(client, org_a):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Other Co",
            "full_name": "Someone Else",
            "email": org_a["email"],
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.asyncio
async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Weak Co",
            "full_name": "Weak User",
            "email": "weak@co.io",
            "password": "123",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success_and_me(client, org_a):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": org_a["email"], "password": org_a["password"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == org_a["email"]
    assert "owner" in [r["code"] for r in body["roles"]]
    assert "products.create" in body["permissions"]


@pytest.mark.asyncio
async def test_login_wrong_password(client, org_a):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": org_a["email"], "password": "WrongPass123"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@nowhere.io", "password": "Whatever123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates_token(client, org_a):
    first = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": org_a["refresh_token"]}
    )
    assert first.status_code == 200
    new_refresh = first.json()["refresh_token"]
    assert new_refresh != org_a["refresh_token"]

    second = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert second.status_code == 200


@pytest.mark.asyncio
async def test_reused_revoked_token_revokes_whole_family(client, org_a):
    """Reuse of a revoked refresh token compromises the family: every token in
    the family (including the rotated successor) must be revoked."""
    first = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": org_a["refresh_token"]}
    )
    assert first.status_code == 200
    new_refresh = first.json()["refresh_token"]

    reuse = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": org_a["refresh_token"]}
    )
    assert reuse.status_code == 401

    # The rotated token shares the same family and must be dead too.
    second = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert second.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh(client, org_a):
    resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": org_a["refresh_token"]}
    )
    assert resp.status_code == 204

    reuse = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": org_a["refresh_token"]}
    )
    assert reuse.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions_and_revoke(client, org_a):
    headers = {"Authorization": f"Bearer {org_a['access_token']}"}
    sessions = await client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    body = sessions.json()
    assert isinstance(body, list) and len(body) >= 1
    assert "family_id" in body[0]
    assert "user_agent" in body[0]
    assert "created_ip" in body[0]

    sid = body[0]["id"]
    resp = await client.delete(f"/api/v1/auth/sessions/{sid}", headers=headers)
    assert resp.status_code == 204

    remaining = await client.get("/api/v1/auth/sessions", headers=headers)
    assert all(s["id"] != sid for s in remaining.json())


@pytest.mark.asyncio
async def test_revoke_other_sessions_keeps_current(client, org_a):
    # Second login = a second device/session.
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": org_a["email"], "password": org_a["password"]},
    )
    assert login_resp.status_code == 200
    second_access = login_resp.json()["access_token"]

    current_id = (
        await client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {second_access}"},
        )
    ).json()[0]["id"]

    resp = await client.post(
        "/api/v1/auth/sessions/revoke-others",
        headers={"Authorization": f"Bearer {second_access}"},
        json={"current_session_id": current_id},
    )
    assert resp.status_code == 200
    assert resp.json()["revoked"] >= 1

    sessions = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {second_access}"},
    )
    assert len(sessions.json()) == 1
    assert sessions.json()[0]["id"] == current_id


@pytest.mark.asyncio
async def test_cannot_revoke_other_users_session(client, org_a, org_b):
    other_session = (
        await client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {org_b['access_token']}"},
        )
    ).json()[0]["id"]

    resp = await client.delete(
        f"/api/v1/auth/sessions/{other_session}",
        headers={"Authorization": f"Bearer {org_a['access_token']}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_garbage_access_token(client):
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_passwords_never_returned(client, org_a):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": org_a["email"], "password": org_a["password"]},
    )
    token = login.json()["access_token"]
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    body = me.json()
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_change_password_success(client, org_a):
    token = org_a["access_token"]
    # Change password
    resp = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": org_a["password"],
            "new_password": "NewSecretPassword123!",
        },
    )
    assert resp.status_code == 200

    # Old password fails
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": org_a["email"], "password": org_a["password"]},
    )
    assert old_login.status_code == 401

    # New password succeeds
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": org_a["email"], "password": "NewSecretPassword123!"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client, org_a):
    token = org_a["access_token"]
    resp = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "WrongOldPassword999!",
            "new_password": "NewSecretPassword123!",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_PASSWORD"
