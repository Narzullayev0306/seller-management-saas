import pytest
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.outbox import OutboxEvent
from app.models.storefront import BackInStockRequest
from app.worker import process_pending


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _count_events(event_type: str) -> int:
    with SessionLocal() as db:
        return db.execute(
            select(func.count(OutboxEvent.id)).where(
                OutboxEvent.event_type == event_type
            )
        ).scalar_one()


def _notifications(org_id: str, type_: str) -> int:
    with SessionLocal() as db:
        return db.execute(
            select(func.count(Notification.id)).where(
                Notification.organization_id == org_id,
                Notification.type == type_,
            )
        ).scalar_one()


@pytest.mark.asyncio
async def test_order_created_emits_outbox_events(client, org_a):
    h = await _headers(org_a["access_token"])
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={
                "name": "Outbox Widget",
                "sku": "OUTB-1",
                "category": "Tools",
                "price": 10,
                "cost_price": 5,
                "stock_quantity": 3,
                "low_stock_threshold": 5,
            },
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers",
            headers=h,
            json={"first_name": "Out", "last_name": "Box", "email": "outbox@x.io"},
        )
    ).json()

    resp = await client.post(
        "/api/v1/orders",
        headers=h,
        json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
    )
    assert resp.status_code == 201, resp.text

    assert _count_events("order.created") == 1
    assert _count_events("stock.low") == 2  # product create + order create

    with SessionLocal() as db:
        events = db.execute(
            select(OutboxEvent).where(OutboxEvent.processed_at.is_(None))
        ).scalars().all()
        assert len(events) == 3
        assert {e.event_type for e in events} == {"order.created", "stock.low"}


@pytest.mark.asyncio
async def test_worker_processes_events_into_notifications(client, org_a):
    from tests.conftest import create_user, login

    h = await _headers(org_a["access_token"])
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={
                "name": "Notif Widget",
                "sku": "NOTIF-1",
                "category": "Tools",
                "price": 10,
                "cost_price": 5,
                "stock_quantity": 2,
                "low_stock_threshold": 5,
            },
        )
    ).json()
    customer = (
        await client.post(
            "/api/v1/customers",
            headers=h,
            json={"first_name": "Not", "last_name": "If", "email": "notif@x.io"},
        )
    ).json()
    await create_user(client, org_a["access_token"], "manager1@x.io", "manager")
    manager_login = await login(client, "manager1@x.io", "Pass12345")
    mh = await _headers(manager_login["access_token"])
    order_resp = await client.post(
        "/api/v1/orders",
        headers=mh,
        json={"customer_id": customer["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
    )
    assert order_resp.status_code == 201, order_resp.text

    with SessionLocal() as db:
        processed = process_pending(db)
    assert processed == 3

    org_id = (await client.get("/api/v1/auth/me", headers=h)).json()["organization_id"]
    assert _notifications(org_id, "new_order") == 1  # owner only; manager (actor) excluded
    assert _notifications(org_id, "low_stock") == 2  # owner + manager, de-duplicated per product
    assert _count_events("order.created") == 1
    with SessionLocal() as db:
        unprocessed = db.execute(
            select(func.count(OutboxEvent.id)).where(OutboxEvent.processed_at.is_(None))
        ).scalar_one()
    assert unprocessed == 0


@pytest.mark.asyncio
async def test_restock_event_notifies_back_in_stock_subscribers(client, org_a):
    h = await _headers(org_a["access_token"])
    product = (
        await client.post(
            "/api/v1/products",
            headers=h,
            json={
                "name": "Restock Widget",
                "sku": "RESTK-1",
                "category": "Tools",
                "price": 10,
                "cost_price": 5,
                "stock_quantity": 0,
                "low_stock_threshold": 5,
            },
        )
    ).json()

    with SessionLocal() as db:
        db.add(
            BackInStockRequest(
                organization_id=(await client.get("/api/v1/auth/me", headers=h)).json()["organization_id"],
                product_id=product["id"],
                email="subscriber@x.io",
            )
        )
        db.commit()

    resp = await client.patch(
        f"/api/v1/products/{product['id']}",
        headers=h,
        json={"stock_quantity": 7},
    )
    assert resp.status_code == 200, resp.text

    assert _count_events("inventory.restocked") == 1

    with SessionLocal() as db:
        processed = process_pending(db)
    assert processed == 2  # stock.low (create) + inventory.restocked

    with SessionLocal() as db:
        request = db.execute(
            select(BackInStockRequest).where(
                BackInStockRequest.email == "subscriber@x.io"
            )
        ).scalar_one()
    assert request.notified_at is not None
