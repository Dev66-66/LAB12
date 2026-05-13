from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.auth import Token, UserRegister


class AuthService:
    """Business logic for authentication and user registration."""

    async def register(self, db: AsyncSession, data: UserRegister) -> User:
        """Create a new staff account after uniqueness checks."""
        if await user_repository.get_by_username(db, data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        if await user_repository.get_by_email(db, data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        return await user_repository.create(
            db,
            {
                "username": data.username,
                "email": data.email,
                "hashed_password": security.hash_password(data.password),
                "full_name": data.full_name,
                "role": data.role,
            },
        )

    async def authenticate(
        self, db: AsyncSession, username: str, password: str
    ) -> User:
        """Verify credentials and return the authenticated user."""
        user = await user_repository.get_by_username(db, username)
        if user is None or not security.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        return user

    def create_token(self, user: User) -> Token:
        """Issue a JWT access token encoding the user's identity and role."""
        access_token = security.create_access_token(
            {"sub": user.username, "role": user.role}
        )
        return Token(access_token=access_token)


auth_service = AuthService()
