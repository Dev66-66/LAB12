"""Seed the database with realistic test data.

Usage:
    python -m scripts.seed_db
"""
import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path

# Allow running from the project root.
sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.models.base import Base
from app.models.menu_item import MenuItem
from app.models.table import Table
from app.models.user import User

fake = Faker("ru_RU")

# ---------------------------------------------------------------------------
# Fixed seed data
# ---------------------------------------------------------------------------

TABLES = [
    {"number": 1,  "capacity": 2,  "location": "Терраса"},
    {"number": 2,  "capacity": 2,  "location": "Терраса"},
    {"number": 3,  "capacity": 4,  "location": "Основной зал"},
    {"number": 4,  "capacity": 4,  "location": "Основной зал"},
    {"number": 5,  "capacity": 4,  "location": "Основной зал"},
    {"number": 6,  "capacity": 6,  "location": "Основной зал"},
    {"number": 7,  "capacity": 6,  "location": "VIP-зал"},
    {"number": 8,  "capacity": 8,  "location": "VIP-зал"},
    {"number": 9,  "capacity": 10, "location": "Банкетный зал"},
    {"number": 10, "capacity": 12, "location": "Банкетный зал"},
]

MENU_ITEMS = [
    # appetizers
    {"name": "Брускетта с томатами",     "category": "appetizer",   "price": Decimal("350.00"),  "preparation_time_minutes": 10, "calories": 220},
    {"name": "Карпаччо из говядины",     "category": "appetizer",   "price": Decimal("680.00"),  "preparation_time_minutes": 15, "calories": 310},
    {"name": "Тартар из лосося",         "category": "appetizer",   "price": Decimal("720.00"),  "preparation_time_minutes": 12, "calories": 280},
    # soups
    {"name": "Борщ классический",        "category": "soup",        "price": Decimal("390.00"),  "preparation_time_minutes": 20, "calories": 350},
    {"name": "Крем-суп из тыквы",        "category": "soup",        "price": Decimal("420.00"),  "preparation_time_minutes": 18, "calories": 290},
    {"name": "Уха из судака",            "category": "soup",        "price": Decimal("490.00"),  "preparation_time_minutes": 25, "calories": 320},
    # main courses
    {"name": "Стейк рибай 300г",         "category": "main_course", "price": Decimal("1850.00"), "preparation_time_minutes": 25, "calories": 750},
    {"name": "Утиная грудка с вишней",   "category": "main_course", "price": Decimal("1290.00"), "preparation_time_minutes": 30, "calories": 620},
    {"name": "Лосось на гриле",          "category": "main_course", "price": Decimal("1150.00"), "preparation_time_minutes": 20, "calories": 540},
    {"name": "Паста карбонара",          "category": "main_course", "price": Decimal("690.00"),  "preparation_time_minutes": 15, "calories": 680},
    {"name": "Ризотто с грибами",        "category": "main_course", "price": Decimal("750.00"),  "preparation_time_minutes": 20, "calories": 590},
    # desserts
    {"name": "Тирамису",                 "category": "dessert",     "price": Decimal("420.00"),  "preparation_time_minutes": 5,  "calories": 480},
    {"name": "Чизкейк Нью-Йорк",        "category": "dessert",     "price": Decimal("390.00"),  "preparation_time_minutes": 5,  "calories": 420},
    {"name": "Шоколадный фондан",        "category": "dessert",     "price": Decimal("450.00"),  "preparation_time_minutes": 12, "calories": 510},
    # beverages
    {"name": "Свежевыжатый апельсиновый", "category": "beverage",  "price": Decimal("290.00"),  "preparation_time_minutes": 5,  "calories": 110},
    {"name": "Лимонад домашний",         "category": "beverage",    "price": Decimal("250.00"),  "preparation_time_minutes": 5,  "calories": 95},
    {"name": "Американо",                "category": "beverage",    "price": Decimal("180.00"),  "preparation_time_minutes": 4,  "calories": 10},
    # alcohol
    {"name": "Бокал Шардоне (150мл)",    "category": "alcohol",     "price": Decimal("490.00"),  "preparation_time_minutes": 2,  "calories": 120},
    {"name": "Крафтовое пиво (0.5л)",    "category": "alcohol",     "price": Decimal("380.00"),  "preparation_time_minutes": 2,  "calories": 210},
    {"name": "Джин-тоник",              "category": "alcohol",     "price": Decimal("550.00"),  "preparation_time_minutes": 3,  "calories": 175},
]


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

async def _ensure_admin(session: AsyncSession) -> None:
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.username == "admin"))
    if result.scalars().first():
        print("  [skip] admin already exists")
        return
    session.add(User(
        username="admin",
        email="admin@restaurant.com",
        hashed_password=hash_password("Admin123"),
        full_name="Главный администратор",
        role="admin",
        is_active=True,
    ))
    await session.commit()
    print("  [ok]   admin created")


async def _ensure_staff(session: AsyncSession) -> None:
    from sqlalchemy import select, func
    count = (await session.execute(
        select(func.count(User.id)).where(User.role != "admin")
    )).scalar_one()
    if count >= 7:
        print("  [skip] staff already seeded")
        return

    roles = ["waiter", "waiter", "waiter", "chef", "chef", "manager"]
    for role in roles:
        first = fake.first_name()
        last = fake.last_name()
        uname = f"{first.lower()}.{last.lower()}{fake.random_int(10, 99)}"
        session.add(User(
            username=uname,
            email=fake.email(),
            hashed_password=hash_password("Staff123"),
            full_name=f"{first} {last}",
            role=role,
            is_active=True,
        ))
    await session.commit()
    print(f"  [ok]   {len(roles)} staff members created")


async def _ensure_tables(session: AsyncSession) -> None:
    from sqlalchemy import select
    existing = (await session.execute(
        select(Table.number)
    )).scalars().all()
    existing_set = set(existing)
    added = 0
    for t in TABLES:
        if t["number"] not in existing_set:
            session.add(Table(**t))
            added += 1
    await session.commit()
    if added:
        print(f"  [ok]   {added} tables created")
    else:
        print("  [skip] tables already seeded")


async def _ensure_menu(session: AsyncSession) -> None:
    from sqlalchemy import select
    existing_names = set(
        (await session.execute(select(MenuItem.name))).scalars().all()
    )
    added = 0
    for item in MENU_ITEMS:
        if item["name"] not in existing_names:
            session.add(MenuItem(**item, description=None, is_available=True))
            added += 1
    await session.commit()
    if added:
        print(f"  [ok]   {added} menu items created")
    else:
        print("  [skip] menu already seeded")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            url = os.environ.get("DATABASE_URL")
        except ImportError:
            pass
    if not url:
        raise SystemExit("DATABASE_URL is not set. Copy .env.example to .env first.")

    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        print("Seeding database …")
        await _ensure_admin(session)
        await _ensure_staff(session)
        await _ensure_tables(session)
        await _ensure_menu(session)
        print("Done.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
