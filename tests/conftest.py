from __future__ import annotations

import os

# Set test env vars before any app module is imported so Settings loads correctly.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-32chars")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.menu_item import MenuItem
from app.models.table import Table
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_order_service = OrderService()


# ---------------------------------------------------------------------------
# 1. Engine & schema (function-scoped — each test gets a fresh in-memory DB)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(
        _TEST_DB_URL,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# 2. Session (function-scoped, bound to the fresh engine above)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        yield session


# ---------------------------------------------------------------------------
# 3. HTTP client with get_db override (function-scoped)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def client(async_session: AsyncSession):
    async def _override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 4. User factory (plain async function, not a fixture)
# ---------------------------------------------------------------------------

async def make_user(
    db: AsyncSession,
    username: str,
    email: str,
    role: str,
    password: str = "Test1234",
    full_name: str = "Test User",
) -> User:
    return await user_repository.create(
        db,
        {
            "username": username,
            "email": email,
            "hashed_password": hash_password(password),
            "full_name": full_name,
            "role": role,
            "is_active": True,
        },
    )


# ---------------------------------------------------------------------------
# 5. Ready-made user fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def admin_user(async_session: AsyncSession) -> User:
    return await make_user(async_session, "admin_test", "admin@test.com", "admin")


@pytest_asyncio.fixture(scope="function")
async def waiter_user(async_session: AsyncSession) -> User:
    return await make_user(async_session, "waiter_test", "waiter@test.com", "waiter")


@pytest_asyncio.fixture(scope="function")
async def chef_user(async_session: AsyncSession) -> User:
    return await make_user(async_session, "chef_test", "chef@test.com", "chef")


# ---------------------------------------------------------------------------
# 6. Auth helper (plain sync function, not a fixture)
# ---------------------------------------------------------------------------

def get_auth_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": user.username})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 7. Data fixtures: table, menu item, order
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def test_table(async_session: AsyncSession) -> Table:
    table = Table(number=1, capacity=4, status="free", location="Main hall")
    async_session.add(table)
    await async_session.commit()
    await async_session.refresh(table)
    return table


@pytest_asyncio.fixture(scope="function")
async def test_menu_item(async_session: AsyncSession) -> MenuItem:
    item = MenuItem(
        name="Test Burger",
        description="A juicy test burger",
        category="main_course",
        price="12.50",
        preparation_time_minutes=15,
        is_available=True,
        calories=650,
    )
    async_session.add(item)
    await async_session.commit()
    await async_session.refresh(item)
    return item


@pytest_asyncio.fixture(scope="function")
async def test_order(
    async_session: AsyncSession,
    test_table: Table,
    waiter_user: User,
    test_menu_item: MenuItem,
):
    data = OrderCreate(
        table_id=test_table.id,
        items=[OrderItemCreate(menu_item_id=test_menu_item.id, quantity=1)],
        notes="Test order",
    )
    return await _order_service.create_order(
        db=async_session,
        table_id=test_table.id,
        waiter_id=waiter_user.id,
        data=data,
    )
