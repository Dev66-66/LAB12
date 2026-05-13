from __future__ import annotations

from conftest import get_auth_headers, make_user
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

fake = Faker()

_REGISTER = "/api/v1/auth/register"
_LOGIN = "/api/v1/auth/login"
_ME = "/api/v1/auth/me"


def _reg(**overrides: object) -> dict:
    """Build a valid registration payload; override specific fields as needed."""
    n = fake.unique.random_int(min=10_000, max=99_999)
    return {
        "username": f"user{n}",
        "email": f"user{n}@test.example",
        "password": "Secret1234",
        "full_name": fake.name(),
        "role": "waiter",
        **overrides,
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

async def test_register_with_valid_data_returns_user_response(client):
    response = await client.post(_REGISTER, json=_reg())

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert "username" in body
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_with_duplicate_username_returns_409(
    client, async_session: AsyncSession
):
    username = f"user{fake.unique.random_int(min=10_000, max=99_999)}"
    await make_user(async_session, username, f"{username}@a.example", "waiter")

    response = await client.post(_REGISTER, json=_reg(username=username))

    assert response.status_code == 409


async def test_register_with_duplicate_email_returns_409(
    client, async_session: AsyncSession
):
    n = fake.unique.random_int(min=10_000, max=99_999)
    email = f"dup{n}@test.example"
    await make_user(async_session, f"orig{n}", email, "waiter")

    response = await client.post(
        _REGISTER,
        json=_reg(
            username=f"new{fake.unique.random_int(min=10_000, max=99_999)}",
            email=email,
        ),
    )

    assert response.status_code == 409


async def test_register_with_weak_password_returns_422(client):
    # "12345678" contains no letter — the field_validator rejects it.
    response = await client.post(_REGISTER, json=_reg(password="12345678"))

    assert response.status_code == 422


async def test_register_with_short_username_returns_422(client):
    # Schema requires min_length=3; "ab" is 2 characters.
    response = await client.post(_REGISTER, json=_reg(username="ab"))

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login  (OAuth2PasswordRequestForm → form data, not JSON)
# ---------------------------------------------------------------------------

async def test_login_with_valid_credentials_returns_token(
    client, async_session: AsyncSession
):
    n = fake.unique.random_int(min=10_000, max=99_999)
    username = f"user{n}"
    await make_user(
        async_session,
        username,
        f"{username}@test.example",
        "waiter",
        password="Secret1234",
    )

    response = await client.post(
        _LOGIN, data={"username": username, "password": "Secret1234"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


async def test_login_with_wrong_password_returns_401(
    client, async_session: AsyncSession
):
    n = fake.unique.random_int(min=10_000, max=99_999)
    username = f"user{n}"
    await make_user(async_session, username, f"{username}@test.example", "waiter")

    response = await client.post(
        _LOGIN, data={"username": username, "password": "WrongPass9"}
    )

    assert response.status_code == 401


async def test_login_with_nonexistent_user_returns_401(client):
    response = await client.post(
        _LOGIN, data={"username": "nobody_99999", "password": "Secret1234"}
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /me endpoint
# ---------------------------------------------------------------------------

async def test_get_me_with_valid_token_returns_user(
    client, async_session: AsyncSession
):
    n = fake.unique.random_int(min=10_000, max=99_999)
    user = await make_user(async_session, f"user{n}", f"me{n}@test.example", "waiter")

    response = await client.get(_ME, headers=get_auth_headers(user))

    assert response.status_code == 200
    assert response.json()["username"] == user.username


async def test_get_me_without_token_returns_401(client):
    response = await client.get(_ME)

    assert response.status_code == 401


async def test_get_me_with_invalid_token_returns_401(client):
    response = await client.get(_ME, headers={"Authorization": "Bearer invalid_token"})

    assert response.status_code == 401
