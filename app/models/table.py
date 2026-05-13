from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class Table(Base, TimestampMixin):
    """Physical dining table in the restaurant."""

    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Primary key."""

    number: Mapped[int] = mapped_column(unique=True, nullable=False)
    """Human-visible table number."""

    capacity: Mapped[int] = mapped_column(nullable=False)
    """Maximum number of guests (1–20)."""

    status: Mapped[str] = mapped_column(
        Enum("free", "occupied", "reserved", "maintenance", name="table_status"),
        default="free",
    )
    """Current availability status."""

    location: Mapped[Optional[str]] = mapped_column(String(100))
    """Optional description of the table's physical location."""

    orders: Mapped[List[Order]] = relationship(
        "Order", back_populates="table", lazy="selectin"
    )
    """All orders placed at this table."""
