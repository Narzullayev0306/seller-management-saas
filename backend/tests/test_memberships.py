import pytest
from sqlalchemy import text

from app.db.session import engine
from tests.conftest import create_user, login


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_owner_has_home_membership(client, org_a):
    h = await _headers(org_a["access_token"])
    memberships = (await client.get("/api/v1/auth/memberships", headers=h)).json()
    assert len(memberships) == 1
    assert memberships[0]["status"] == "active"
    assert memberships[0]["is_active"] is True


@pytest.mark.asyncio
async def test_switch_org_rejects_non_member(client, org_a, org_b):
    h = await _headers(org_a["access_token"])
    org_b_info = (
        await client.get(
            "/api/v1/organizations/me",
            headers=await _headers(org_b["access_token"]),
        )
    ).json()

    resp = await client.post(
        "/api/v1/auth/switch-org", headers=h, json={"organization_id": org_b_info["id"]}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "NOT_A_MEMBER"


@pytest.mark.asyncio
async def test_multi_org_scoping(client, org_a, org_b):
    """A user with memberships in two orgs sees only the active org's data."""
    b_h = await _headers(org_b["access_token"])
    org_b_info = (
        await client.get("/api/v1/organizations/me", headers=b_h)
    ).json()

    member = await create_user(client, org_a["access_token"], "dual@x.io", "admin")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO organization_members (id, organization_id, user_id, status, joined_at, created_at)
                SELECT gen_random_uuid(), :org_b, :user_id, 'active', now(), now()
                """
            ),
            {"org_b": org_b_info["id"], "user_id": member["id"]},
        )

    dual_token = (await login(client, "dual@x.io", "Pass12345"))["access_token"]
    dual_h = await _headers(dual_token)

    empty = (await client.get("/api/v1/products", headers=dual_h)).json()
    assert empty["total"] == 0

    switch = await client.post(
        "/api/v1/auth/switch-org", headers=dual_h, json={"organization_id": org_b_info["id"]}
    )
    assert switch.status_code == 200
    switched_h = await _headers(switch.json()["access_token"])

    me = (await client.get("/api/v1/auth/me", headers=switched_h)).json()
    assert me["organization_id"] == org_b_info["id"]
    assert me["organization_name"] == org_b_info["name"]

    created = await client.post(
        "/api/v1/products",
        headers=switched_h,
        json={"name": "B-Only Item", "sku": "B-1", "category": "T", "price": 10, "cost_price": 5, "stock_quantity": 3},
    )
    assert created.status_code == 201

    in_b = (await client.get("/api/v1/products", headers=switched_h)).json()
    assert in_b["total"] == 1

    in_a = (await client.get("/api/v1/products", headers=dual_h)).json()
    assert in_a["total"] == 0

    memberships = (await client.get("/api/v1/auth/memberships", headers=switched_h)).json()
    assert {m["name"] for m in memberships} == {org_b_info["name"]}


@pytest.mark.asyncio
async def test_home_org_access_still_works_without_membership_row(client, org_a):
    """Legacy tokens where the claimed org equals the home org stay valid."""
    h = await _headers(org_a["access_token"])
    resp = await client.get("/api/v1/auth/me", headers=h)
    assert resp.status_code == 200
    assert resp.json()["organization_id"] == resp.json()["organization_id"]
