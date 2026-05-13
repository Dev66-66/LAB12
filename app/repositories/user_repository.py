from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data-access methods for the User model."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Return the user with the given e-mail, or None."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        """Return the user with the given username, or None."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_active_staff(self, db: AsyncSession) -> list[User]:
        """Return all users whose is_active flag is True."""
        result = await db.execute(select(User).where(User.is_active.is_(True)))
        return list(result.scalars().all())


user_repository = UserRepository()
