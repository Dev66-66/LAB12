from __future__ import annotations

from decimal import Decimal

from conftest import get_auth_headers, make_user
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import Table

fake = Faker()

_ORDERS = "/api/v1/orders"


def _table_num() -> int:
    return fake.unique.random_int(min=200, max=999)


async def _free_table(session: AsyncSession) -> Table:
    t = Table(number=_table_num(), capacity=4, status="free")
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return t


def _order_payload(table_id: int, menu_item_id: int, qty: int = 1) -> dict:
    return {
        "table_id": table_id,
        "items": [{"menu_item_id": menu_item_id, "quantity": qty}],
    }


# ---------------------------------------------------------------------------
# Create order
# ---------------------------------------------------------------------------

async def test_create_order_with_valid_data_returns_201(
    client, test_table, test_menu_item, waiter_user
):
    response = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(test_table.id, test_menu_item.id, qty=2),
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["table_id"] == test_table.id
    assert body["status"] == "pending"
    # 2 × 12.50 = 25.00
    assert Decimal(str(body["total_amount"])) == test_menu_item.price * 2


async def test_create_order_sets_table_status_to_occupied(
    client, test_table, test_menu_item, waiter_user, async_session: AsyncSession
):
    await client.post(
        f"{_ORDERS}/",
        json=_order_payload(test_table.id, test_menu_item.id),
        headers=get_auth_headers(waiter_user),
    )

    await async_session.refresh(test_table)
    assert test_table.status == "occupied"


async def test_create_order_with_empty_items_returns_422(
    client, test_table, waiter_user
):
    response = await client.post(
        f"{_ORDERS}/",
        json={"table_id": test_table.id, "items": []},
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 422


async def test_create_order_with_unavailable_item_returns_400(
    client, async_session: AsyncSession, test_table, waiter_user
):
    from app.models.menu_item import MenuItem

    unavailable = MenuItem(
        name="Sold Out",
        category="beverage",
        price="5.00",
        preparation_time_minutes=1,
        is_available=False,
    )
    async_session.add(unavailable)
    await async_session.commit()
    await async_session.refresh(unavailable)

    response = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(test_table.id, unavailable.id),
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 400


async def test_create_order_with_nonexistent_table_returns_404(
    client, test_menu_item, waiter_user
):
    response = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(99999, test_menu_item.id),
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 404


async def test_create_order_with_occupied_table_returns_409(
    client, test_order, test_table, test_menu_item, waiter_user
):
    # test_order already set test_table to "occupied"
    response = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(test_table.id, test_menu_item.id),
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# List / get orders
# ---------------------------------------------------------------------------

async def test_get_orders_as_waiter_returns_only_own_orders(
    client, async_session: AsyncSession, test_menu_item
):
    n1 = fake.unique.random_int(min=10_000, max=99_999)
    n2 = fake.unique.random_int(min=10_000, max=99_999)
    w1 = await make_user(async_session, f"w{n1}", f"w{n1}@test.example", "waiter")
    w2 = await make_user(async_session, f"w{n2}", f"w{n2}@test.example", "waiter")

    t1 = await _free_table(async_session)
    t2 = await _free_table(async_session)

    r1 = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(t1.id, test_menu_item.id),
        headers=get_auth_headers(w1),
    )
    r2 = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(t2.id, test_menu_item.id),
        headers=get_auth_headers(w2),
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    response = await client.get(f"{_ORDERS}/", headers=get_auth_headers(w1))

    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 1
    assert orders[0]["waiter_id"] == w1.id


async def test_get_orders_as_admin_returns_all_orders(
    client, async_session: AsyncSession, test_menu_item, admin_user
):
    n1 = fake.unique.random_int(min=10_000, max=99_999)
    n2 = fake.unique.random_int(min=10_000, max=99_999)
    w1 = await make_user(async_session, f"w{n1}", f"w{n1}@test.example", "waiter")
    w2 = await make_user(async_session, f"w{n2}", f"w{n2}@test.example", "waiter")

    t1 = await _free_table(async_session)
    t2 = await _free_table(async_session)

    resp1 = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(t1.id, test_menu_item.id),
        headers=get_auth_headers(w1),
    )
    resp2 = await client.post(
        f"{_ORDERS}/",
        json=_order_payload(t2.id, test_menu_item.id),
        headers=get_auth_headers(w2),
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201

    response = await client.get(f"{_ORDERS}/", headers=get_auth_headers(admin_user))

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_order_by_id_returns_order(client, test_order, waiter_user):
    response = await client.get(
        f"{_ORDERS}/{test_order.id}",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    assert response.json()["id"] == test_order.id


async def test_list_active_orders_excludes_closed_orders(
    client, test_order, waiter_user
):
    # Close the order (paid → not active)
    await client.post(
        f"{_ORDERS}/{test_order.id}/close",
        headers=get_auth_headers(waiter_user),
    )

    response = await client.get(
        f"{_ORDERS}/active", headers=get_auth_headers(waiter_user)
    )

    assert response.status_code == 200
    ids = [o["id"] for o in response.json()]
    assert test_order.id not in ids


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

async def test_order_status_transition_pending_to_confirmed(
    client, test_order, waiter_user
):
    response = await client.patch(
        f"{_ORDERS}/{test_order.id}/status",
        json={"status": "confirmed"},
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


async def test_order_status_invalid_transition_returns_400(
    client, test_order, waiter_user
):
    # pending → paid is not in _TRANSITIONS["pending"]
    response = await client.patch(
        f"{_ORDERS}/{test_order.id}/status",
        json={"status": "paid"},
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Close / cancel
# ---------------------------------------------------------------------------

async def test_close_order_sets_table_status_to_free(
    client, test_order, test_table, waiter_user, async_session: AsyncSession
):
    await async_session.refresh(test_table)
    assert test_table.status == "occupied"

    response = await client.post(
        f"{_ORDERS}/{test_order.id}/close",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    await async_session.refresh(test_table)
    assert test_table.status == "free"


async def test_cancel_order_in_pending_status_succeeds(
    client, test_order, waiter_user
):
    response = await client.delete(
        f"{_ORDERS}/{test_order.id}",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 204
