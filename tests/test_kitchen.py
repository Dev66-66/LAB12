from __future__ import annotations

from conftest import get_auth_headers
from faker import Faker

fake = Faker()

_KITCHEN = "/api/v1/kitchen"
_ORDERS = "/api/v1/orders"


# ---------------------------------------------------------------------------
# Queue endpoint
# ---------------------------------------------------------------------------

async def test_get_kitchen_queue_as_chef_returns_queue(client, test_order, chef_user):
    # test_order items are in "pending" status → visible in queue
    response = await client.get(
        f"{_KITCHEN}/queue", headers=get_auth_headers(chef_user)
    )

    assert response.status_code == 200
    queue = response.json()
    assert isinstance(queue, list)
    assert len(queue) >= 1
    assert queue[0]["item_id"] == test_order.items[0].id


async def test_get_kitchen_queue_as_waiter_returns_403(client, test_order, waiter_user):
    response = await client.get(
        f"{_KITCHEN}/queue", headers=get_auth_headers(waiter_user)
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Mark preparing
# ---------------------------------------------------------------------------

async def test_mark_item_preparing_changes_status(client, test_order, chef_user):
    item_id = test_order.items[0].id

    response = await client.patch(
        f"{_KITCHEN}/items/{item_id}/preparing",
        headers=get_auth_headers(chef_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "preparing"


async def test_mark_item_preparing_when_not_pending_returns_400(
    client, test_order, chef_user
):
    item_id = test_order.items[0].id
    # First transition: pending → preparing
    await client.patch(
        f"{_KITCHEN}/items/{item_id}/preparing",
        headers=get_auth_headers(chef_user),
    )
    # Second call: item is now "preparing", expected "pending" → 400
    response = await client.patch(
        f"{_KITCHEN}/items/{item_id}/preparing",
        headers=get_auth_headers(chef_user),
    )

    assert response.status_code == 400


async def test_mark_item_preparing_nonexistent_returns_404(client, chef_user):
    response = await client.patch(
        f"{_KITCHEN}/items/99999/preparing",
        headers=get_auth_headers(chef_user),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Mark ready
# ---------------------------------------------------------------------------

async def test_mark_item_ready_changes_status(client, test_order, chef_user):
    item_id = test_order.items[0].id
    # pending → preparing first
    await client.patch(
        f"{_KITCHEN}/items/{item_id}/preparing",
        headers=get_auth_headers(chef_user),
    )

    response = await client.patch(
        f"{_KITCHEN}/items/{item_id}/ready",
        headers=get_auth_headers(chef_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_mark_item_ready_when_all_items_ready_updates_order_status(
    client, test_order, waiter_user, chef_user
):
    item_id = test_order.items[0].id

    # Advance order to "confirmed" so kitchen can progress it to "preparing"
    await client.patch(
        f"{_ORDERS}/{test_order.id}/status",
        json={"status": "confirmed"},
        headers=get_auth_headers(waiter_user),
    )

    # Mark item preparing → order becomes "preparing"
    await client.patch(
        f"{_KITCHEN}/items/{item_id}/preparing",
        headers=get_auth_headers(chef_user),
    )

    # Mark item ready → all items ready → order becomes "ready"
    await client.patch(
        f"{_KITCHEN}/items/{item_id}/ready",
        headers=get_auth_headers(chef_user),
    )

    order_resp = await client.get(
        f"{_ORDERS}/{test_order.id}",
        headers=get_auth_headers(waiter_user),
    )

    assert order_resp.status_code == 200
    assert order_resp.json()["status"] == "ready"


async def test_mark_item_ready_when_not_preparing_returns_400(
    client, test_order, chef_user
):
    # Item is still "pending" — cannot jump straight to "ready"
    item_id = test_order.items[0].id

    response = await client.patch(
        f"{_KITCHEN}/items/{item_id}/ready",
        headers=get_auth_headers(chef_user),
    )

    assert response.status_code == 400


async def test_mark_item_ready_nonexistent_returns_404(client, chef_user):
    response = await client.patch(
        f"{_KITCHEN}/items/99999/ready",
        headers=get_auth_headers(chef_user),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

async def test_kitchen_stats_returns_correct_counts(client, test_order, chef_user):
    # test_order has one item in "pending" status
    response = await client.get(
        f"{_KITCHEN}/stats", headers=get_auth_headers(chef_user)
    )

    assert response.status_code == 200
    body = response.json()
    assert "items_pending" in body
    assert "items_preparing" in body
    assert "items_ready" in body
    assert body["items_pending"] >= 1
