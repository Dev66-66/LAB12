from __future__ import annotations

from conftest import get_auth_headers
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import Table

fake = Faker()

_TABLES = "/api/v1/tables"


def _number() -> int:
    """Return a unique table number in the 100-999 range per test run."""
    return fake.unique.random_int(min=100, max=999)


# ---------------------------------------------------------------------------
# Read / list
# ---------------------------------------------------------------------------

async def test_get_all_tables_returns_list(client, waiter_user):
    response = await client.get(f"{_TABLES}/", headers=get_auth_headers(waiter_user))

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_table_by_id_returns_table(client, test_table, waiter_user):
    response = await client.get(
        f"{_TABLES}/{test_table.id}",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == test_table.id
    assert body["number"] == test_table.number


async def test_get_table_with_nonexistent_id_returns_404(client, waiter_user):
    response = await client.get(
        f"{_TABLES}/99999", headers=get_auth_headers(waiter_user)
    )

    assert response.status_code == 404


async def test_get_available_tables_excludes_occupied(
    client, async_session: AsyncSession, waiter_user
):
    free = Table(number=_number(), capacity=4, status="free")
    occupied = Table(number=_number(), capacity=4, status="occupied")
    async_session.add_all([free, occupied])
    await async_session.commit()
    await async_session.refresh(free)
    await async_session.refresh(occupied)

    response = await client.get(
        f"{_TABLES}/available", headers=get_auth_headers(waiter_user)
    )

    assert response.status_code == 200
    returned_ids = {t["id"] for t in response.json()}
    assert free.id in returned_ids
    assert occupied.id not in returned_ids


# ---------------------------------------------------------------------------
# Create — role restrictions
# ---------------------------------------------------------------------------

async def test_create_table_as_admin_returns_201(client, admin_user):
    response = await client.post(
        f"{_TABLES}/",
        json={"number": _number(), "capacity": 4},
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["capacity"] == 4


async def test_create_table_as_waiter_returns_403(client, waiter_user):
    response = await client.post(
        f"{_TABLES}/",
        json={"number": _number(), "capacity": 4},
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 403


async def test_create_table_with_duplicate_number_returns_409(client, admin_user):
    number = _number()
    headers = get_auth_headers(admin_user)
    await client.post(
        f"{_TABLES}/", json={"number": number, "capacity": 4}, headers=headers
    )

    response = await client.post(
        f"{_TABLES}/", json={"number": number, "capacity": 6}, headers=headers
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Create — payload validation
# ---------------------------------------------------------------------------

async def test_create_table_with_zero_capacity_returns_422(client, admin_user):
    # Schema: capacity=Field(ge=1, le=20) — 0 violates ge=1.
    response = await client.post(
        f"{_TABLES}/",
        json={"number": _number(), "capacity": 0},
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 422


async def test_create_table_with_capacity_over_20_returns_422(client, admin_user):
    # Schema: capacity=Field(ge=1, le=20) — 21 violates le=20.
    response = await client.post(
        f"{_TABLES}/",
        json={"number": _number(), "capacity": 21},
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def test_update_table_status_returns_updated_table(
    client, test_table, waiter_user
):
    response = await client.patch(
        f"{_TABLES}/{test_table.id}/status",
        json={"status": "occupied"},
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "occupied"


# ---------------------------------------------------------------------------
# Delete — role restrictions
# ---------------------------------------------------------------------------

async def test_delete_table_as_admin_returns_204(client, test_table, admin_user):
    response = await client.delete(
        f"{_TABLES}/{test_table.id}",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 204


async def test_delete_table_as_waiter_returns_403(client, test_table, waiter_user):
    response = await client.delete(
        f"{_TABLES}/{test_table.id}",
        headers=get_auth_headers(waiter_user),
    )

    assert response.status_code == 403
