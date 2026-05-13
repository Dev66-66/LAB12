from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem
    from app.models.order import Order


class OrderItem(Base, TimestampMixin):
    """A single line item within an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Primary key."""

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    """Reference to the parent order."""

    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id"), nullable=False
    )
    """Reference to the ordered menu item."""

    quantity: Mapped[int] = mapped_column(nullable=False)
    """Number of portions ordered (>= 1)."""

    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    """Price per unit captured at the moment of ordering."""

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "preparing",
            "ready",
            "served",
            "cancelled",
            name="item_status",
        ),
        default="pending",
    )
    """Kitchen preparation state for this line item."""

    notes: Mapped[Optional[str]] = mapped_column(String(255))
    """Optional per-item instructions (e.g. allergen requests)."""

    order: Mapped[Order] = relationship(
        "Order", back_populates="items", lazy="selectin"
    )
    """Parent order this item belongs to."""

    menu_item: Mapped[MenuItem] = relationship(
        "MenuItem", lazy="selectin"
    )
    """Menu item that was ordered."""
