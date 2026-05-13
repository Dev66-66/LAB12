from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):  # noqa: UP046
    """Generic async repository providing basic CRUD over a SQLAlchemy model."""

    def __init__(self, model: type[ModelType]) -> None:
        self._model = model

    async def get(self, db: AsyncSession, id: int) -> ModelType | None:
        """Return a single record by primary key, or None if not found."""
        result = await db.execute(select(self._model).where(self._model.id == id))  # type: ignore[attr-defined]
        return result.scalars().first()

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Return a paginated list of all records."""
        result = await db.execute(select(self._model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_data: dict) -> ModelType:
        """Insert a new record from a plain dict and return the persisted instance."""
        db_obj = self._model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_data: dict
    ) -> ModelType:
        """Apply obj_data fields to an existing instance and persist changes."""
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Delete by primary key. Return True if deleted, False if not found."""
        db_obj = await self.get(db, id)
        if db_obj is None:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True
