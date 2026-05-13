from __future__ import annotations

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import get_auth_headers, make_user

fake = Faker()

_MENU = "/api/v1/menu"
_STAFF = "/api/v1/staff"


def _item(**overrides: object) -> dict:
    """Build a valid menu item payload."""
    n = fake.unique.random_int(min=1_000, max=9_999)
    return {
        "name": f"Dish {n}",
        "description": "A test dish",
        "category": "main_course",
        "price": "14.99",
        "preparation_time_minutes": 20,
        "is_available": True,
        "calories": 500,
        **overrides,
    }


# ---------------------------------------------------------------------------
# Menu — list / search / get
# ---------------------------------------------------------------------------

async def test_list_menu_returns_available_items_by_default(
    client, test_menu_item, waiter_user
):
    response = await client.get(f"{_MENU}/", headers=get_auth_headers(waiter_user))

    assert response.status_code == 200
    ids = [i["id"] for i in response.json()]
    assert test_menu_item.id in ids


async def test_list_menu_with_available_false_returns_all_items(
    client, async_session: AsyncSession, admin_user, waiter_user
):
    # Create a hidden item
    hidden = await client.post(
        f"{_MENU}/",
        json=_item(is_available=False),
        headers=get_auth_headers(admin_user),
    )
    hidden_id = hidden.json()["id"]

    response = await client.get(
        f"{_MENU}/?available_only=false",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    ids = [i["id"] for i in response.json()]
    assert hidden_id in ids


async def test_list_menu_with_category_filter(
    client, admin_user, waiter_user
):
    resp = await client.post(
        f"{_MENU}/",
        json=_item(category="dessert"),
        headers=get_auth_headers(admin_user),
    )
    assert resp.status_code == 201
    dessert_id = resp.json()["id"]

    response = await client.get(
        f"{_MENU}/?category=dessert&available_only=false",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    ids = [i["id"] for i in response.json()]
    assert dessert_id in ids


async def test_search_menu_returns_matching_items(client, admin_user, waiter_user):
    unique_name = f"UniqueSearchDish{fake.unique.random_int(min=1000, max=9999)}"
    resp = await client.post(
        f"{_MENU}/",
        json=_item(name=unique_name),
        headers=get_auth_headers(admin_user),
    )
    assert resp.status_code == 201

    response = await client.get(
        f"{_MENU}/search?q={unique_name}",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    names = [i["name"] for i in response.json()]
    assert unique_name in names


async def test_get_menu_item_by_id_returns_item(client, test_menu_item, waiter_user):
    response = await client.get(
        f"{_MENU}/{test_menu_item.id}",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    assert response.json()["id"] == test_menu_item.id


async def test_get_menu_item_nonexistent_returns_404(client, waiter_user):
    response = await client.get(f"{_MENU}/99999", headers=get_auth_headers(waiter_user))

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Menu — create
# ---------------------------------------------------------------------------

async def test_create_menu_item_as_admin_returns_201(client, admin_user):
    response = await client.post(
        f"{_MENU}/",
        json=_item(),
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["is_available"] is True


async def test_create_menu_item_as_waiter_returns_403(client, waiter_user):
    response = await client.post(
        f"{_MENU}/",
        json=_item(),
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Menu — update / toggle / delete
# ---------------------------------------------------------------------------

async def test_update_menu_item_as_admin_returns_updated_item(
    client, test_menu_item, admin_user
):
    response = await client.put(
        f"{_MENU}/{test_menu_item.id}",
        json={"name": "Updated Name", "price": "19.99", "preparation_time_minutes": 25, "category": "main_course"},
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


async def test_toggle_availability_disables_available_item(
    client, test_menu_item, admin_user
):
    # test_menu_item is available — toggle should make it unavailable
    response = await client.patch(
        f"{_MENU}/{test_menu_item.id}/availability",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["is_available"] is False


async def test_delete_menu_item_as_admin_returns_204(client, test_menu_item, admin_user):
    response = await client.delete(
        f"{_MENU}/{test_menu_item.id}",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 204


async def test_delete_menu_item_nonexistent_returns_404(client, admin_user):
    response = await client.delete(
        f"{_MENU}/99999",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Staff endpoints (require admin / manager)
# ---------------------------------------------------------------------------

async def test_list_staff_as_admin_returns_active_members(
    client, admin_user, waiter_user
):
    # admin_user and waiter_user are both active
    response = await client.get(f"{_STAFF}/", headers=get_auth_headers(admin_user))

    assert response.status_code == 200
    ids = [u["id"] for u in response.json()]
    assert admin_user.id in ids
    assert waiter_user.id in ids


async def test_list_staff_as_waiter_returns_403(client, waiter_user):
    response = await client.get(f"{_STAFF}/", headers=get_auth_headers(waiter_user))

    assert response.status_code == 403


async def test_get_staff_member_by_id(client, admin_user, waiter_user):
    response = await client.get(
        f"{_STAFF}/{waiter_user.id}",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["id"] == waiter_user.id


async def test_get_staff_member_nonexistent_returns_404(client, admin_user):
    response = await client.get(
        f"{_STAFF}/99999",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 404


async def test_deactivate_staff_member_sets_is_active_false(
    client, async_session: AsyncSession, admin_user
):
    n = fake.unique.random_int(min=10_000, max=99_999)
    target = await make_user(async_session, f"staff{n}", f"staff{n}@test.example", "waiter")

    response = await client.patch(
        f"{_STAFF}/{target.id}/deactivate",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_waiter_stats_returns_aggregated_list(
    client, admin_user, waiter_user
):
    response = await client.get(f"{_STAFF}/stats", headers=get_auth_headers(admin_user))

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# Health check (covers app/main.py route)
# ---------------------------------------------------------------------------

async def test_health_check_returns_ok(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
