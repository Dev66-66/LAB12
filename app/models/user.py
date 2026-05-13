from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class User(Base, TimestampMixin):
    """Restaurant staff member account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Primary key."""

    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    """Unique login name."""

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    """Unique e-mail address."""

    hashed_password: Mapped[str] = mapped_column(nullable=False)
    """Bcrypt-hashed password."""

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    """Display name."""

    role: Mapped[str] = mapped_column(
        Enum("admin", "manager", "waiter", "chef", name="user_role"),
        default="waiter",
        nullable=False,
    )
    """Staff role that controls permissions."""

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    """Soft-disable flag."""

    orders: Mapped[List[Order]] = relationship(
        "Order", back_populates="waiter", lazy="selectin"
    )
    """Orders served by this waiter."""
