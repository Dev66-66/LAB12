from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Enum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MenuItem(Base, TimestampMixin):
    """A single dish or drink available on the menu."""

    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    """Display name shown to guests."""

    description: Mapped[str | None] = mapped_column(Text)
    """Optional longer description."""

    category: Mapped[str] = mapped_column(
        Enum(
            "appetizer",
            "soup",
            "main_course",
            "dessert",
            "beverage",
            "alcohol",
            name="menu_category",
        ),
        index=True,
    )
    """Menu section this item belongs to."""

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    """Price in local currency."""

    preparation_time_minutes: Mapped[int] = mapped_column(nullable=False)
    """Expected kitchen preparation time in minutes."""

    is_available: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    """Whether this item can currently be ordered."""

    calories: Mapped[int | None]
    """Optional caloric value for nutritional display."""
