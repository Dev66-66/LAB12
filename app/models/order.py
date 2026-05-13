from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order_item import OrderItem
    from app.models.table import Table
    from app.models.user import User


class Order(Base, TimestampMixin):
    """A customer order tied to a table and a waiter."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Primary key."""

    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"), nullable=False)
    """Reference to the table where the order was placed."""

    waiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    """Reference to the waiter who took the order."""

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "confirmed",
            "preparing",
            "ready",
            "served",
            "paid",
            "cancelled",
            name="order_status",
        ),
        default="pending",
        index=True,
    )
    """Lifecycle state of the order."""

    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    """Running total recalculated on item changes."""

    notes: Mapped[Optional[str]] = mapped_column(Text)
    """Free-text instructions from the customer."""

    table: Mapped[Table] = relationship(
        "Table", back_populates="orders", lazy="selectin"
    )
    """Table this order belongs to."""

    waiter: Mapped[User] = relationship(
        "User", back_populates="orders", lazy="selectin"
    )
    """Waiter responsible for this order."""

    items: Mapped[List[OrderItem]] = relationship(
        "OrderItem", back_populates="order", lazy="selectin"
    )
    """Individual line items that make up this order."""
