from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import Token, UserRegister, UserResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new staff account",
)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Create a new restaurant staff account.

    Validates username/email uniqueness and hashes the password before persisting.
    Returns the created user profile without the password field.
    """
    return await auth_service.register(db, data)


@router.post(
    "/login",
    response_model=Token,
    summary="Obtain a JWT access token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate with username and password, receive a Bearer token.

    The token encodes the user's identity and role and is required for all
    protected endpoints.
    """
    user = await auth_service.authenticate(db, form_data.username, form_data.password)
    return auth_service.create_token(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user
