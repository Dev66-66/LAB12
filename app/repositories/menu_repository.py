from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem
from app.repositories.base_repository import BaseRepository


class MenuRepository(BaseRepository[MenuItem]):
    """Data-access methods for the MenuItem model."""

    def __init__(self) -> None:
        super().__init__(MenuItem)

    async def get_by_category(
        self, db: AsyncSession, category: str
    ) -> list[MenuItem]:
        """Return all menu items belonging to the given category."""
        result = await db.execute(
            select(MenuItem).where(MenuItem.category == category)
        )
        return list(result.scalars().all())

    async def get_available(self, db: AsyncSession) -> list[MenuItem]:
        """Return all menu items that are currently available for ordering."""
        result = await db.execute(
            select(MenuItem).where(MenuItem.is_available.is_(True))
        )
        return list(result.scalars().all())

    async def search(self, db: AsyncSession, query: str) -> list[MenuItem]:
        """Return items whose name or description contains query (case-insensitive)."""
        pattern = f"%{query}%"
        result = await db.execute(
            select(MenuItem).where(
                or_(
                    MenuItem.name.ilike(pattern),
                    MenuItem.description.ilike(pattern),
                )
            )
        )
        return list(result.scalars().all())


menu_repository = MenuRepository()
