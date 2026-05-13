from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import Table
from app.repositories.base_repository import BaseRepository


class TableRepository(BaseRepository[Table]):
    """Data-access methods for the Table model."""

    def __init__(self) -> None:
        super().__init__(Table)

    async def get_by_number(self, db: AsyncSession, number: int) -> Table | None:
        """Return the table with the given number, or None."""
        result = await db.execute(select(Table).where(Table.number == number))
        return result.scalars().first()

    async def get_by_status(self, db: AsyncSession, status: str) -> list[Table]:
        """Return all tables matching the given status string."""
        result = await db.execute(select(Table).where(Table.status == status))
        return list(result.scalars().all())

    async def get_available(
        self, db: AsyncSession, min_capacity: int = 1
    ) -> list[Table]:
        """Return free tables whose capacity is at least min_capacity."""
        result = await db.execute(
            select(Table).where(
                Table.status == "free",
                Table.capacity >= min_capacity,
            )
        )
        return list(result.scalars().all())


table_repository = TableRepository()
