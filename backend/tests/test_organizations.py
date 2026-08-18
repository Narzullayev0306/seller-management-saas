import pytest

from tests.conftest import create_user, login


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_plan_change_owner_only(client, org_a):
    h = await _headers(org_a["access_token"])
    await create_user(client, org_a["access_token"], "member@plan.io", "viewer")
    member_token = (await login(client, "member@plan.io", "Pass12345"))["access_token"]
    member_h = await _headers(member_token)

    ok = await client.patch("/api/v1/organizations/me/plan", headers=h, json={"plan": "pro"})
    assert ok.status_code == 200
    assert ok.json()["plan"] == "pro"

    denied = await client.patch("/api/v1/organizations/me/plan", headers=member_h, json={"plan": "free"})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "OWNER_ONLY"

    bad = await client.patch("/api/v1/organizations/me/plan", headers=h, json={"plan": "gold"})
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_transfer_ownership(client, org_a):
    h = await _headers(org_a["access_token"])
    member = await create_user(client, org_a["access_token"], "member@trans.io", "manager")
    member_h = await _headers((await login(client, "member@trans.io", "Pass12345"))["access_token"])

    denied = await client.post(
        "/api/v1/organizations/me/transfer-ownership", headers=member_h, json={"user_id": member["id"]}
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "OWNER_ONLY"

    resp = await client.post(
        "/api/v1/organizations/me/transfer-ownership", headers=h, json={"user_id": member["id"]}
    )
    assert resp.status_code == 200

    me_old_owner = (await client.get("/api/v1/auth/me", headers=h)).json()
    assert "owner" not in [r["code"] for r in me_old_owner["roles"]]
    me_new_owner = (await client.get("/api/v1/auth/me", headers=member_h)).json()
    assert "owner" in [r["code"] for r in me_new_owner["roles"]]


@pytest.mark.asyncio
async def test_transfer_ownership_rejects_inactive_and_self(client, org_a):
    h = await _headers(org_a["access_token"])
    member = await create_user(client, org_a["access_token"], "member2@trans.io", "viewer")

    users = (await client.get("/api/v1/users?page_size=100", headers=h)).json()["items"]
    owner = next(u for u in users if "owner" in u["roles"])
    self_resp = await client.post(
        "/api/v1/organizations/me/transfer-ownership", headers=h, json={"user_id": owner["id"]}
    )
    assert self_resp.status_code == 400
    assert self_resp.json()["error"]["code"] == "SELF_TRANSFER"

    not_found_resp = await client.post(
        "/api/v1/organizations/me/transfer-ownership",
        headers=h,
        json={"user_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert not_found_resp.status_code == 404

    await client.patch(f"/api/v1/users/{member['id']}", headers=h, json={"is_active": False})
    inactive_resp = await client.post(
        "/api/v1/organizations/me/transfer-ownership", headers=h, json={"user_id": member["id"]}
    )
    assert inactive_resp.status_code == 400
    assert inactive_resp.json()["error"]["code"] == "TARGET_INACTIVE"


@pytest.mark.asyncio
async def test_close_company_locks_everyone_out(client, org_a):
    h = await _headers(org_a["access_token"])
    await create_user(client, org_a["access_token"], "member3@close.io", "viewer")
    member_h = await _headers((await login(client, "member3@close.io", "Pass12345"))["access_token"])

    denied = await client.post("/api/v1/organizations/me/close", headers=member_h)
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "OWNER_ONLY"

    resp = await client.post("/api/v1/organizations/me/close", headers=h)
    assert resp.status_code == 200

    me_after = await client.get("/api/v1/auth/me", headers=h)
    assert me_after.status_code == 401
    assert me_after.json()["error"]["code"] == "ORG_INACTIVE"

    member_after = await client.get("/api/v1/auth/me", headers=member_h)
    assert member_after.status_code == 401
    assert member_after.json()["error"]["code"] == "ORG_INACTIVE"
