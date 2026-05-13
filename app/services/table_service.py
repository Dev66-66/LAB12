from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import Table
from app.repositories.table_repository import table_repository
from app.schemas.table import TableCreate


class TableService:
    """Business logic for dining table management."""

    async def create_table(self, db: AsyncSession, data: TableCreate) -> Table:
        """Register a new table, ensuring the number is unique."""
        if await table_repository.get_by_number(db, data.number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Table number {data.number} already exists",
            )
        return await table_repository.create(db, data.model_dump())

    async def update_status(
        self, db: AsyncSession, table_id: int, new_status: str
    ) -> Table:
        """Change a table's availability status."""
        table = await table_repository.get(db, table_id)
        if table is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {table_id} not found",
            )
        return await table_repository.update(db, table, {"status": new_status})

    async def get_available(
        self, db: AsyncSession, min_capacity: int = 1
    ) -> list[Table]:
        """Return free tables with at least the requested capacity."""
        return await table_repository.get_available(db, min_capacity)


table_service = TableService()
