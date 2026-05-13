from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Payload for creating a new staff account."""

    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=100)]
    full_name: Annotated[str, Field(min_length=2, max_length=100)]
    role: Literal["admin", "manager", "waiter", "chef"] = "waiter"

    @field_validator("password")
    @classmethod
    def password_must_contain_letter_and_digit(cls, v: str) -> str:
        """Require at least one letter and one digit in the password."""
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Credentials for obtaining a JWT token."""

    username: str
    password: str


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public representation of a staff account (no password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
