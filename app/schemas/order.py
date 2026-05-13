from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

OrderStatus = Literal[
    "pending", "confirmed", "preparing", "ready", "served", "paid", "cancelled"
]


class OrderItemCreate(BaseModel):
    """Single dish line within a new order request."""

    menu_item_id: int
    quantity: Annotated[int, Field(ge=1, le=99)]
    notes: str | None = None


class OrderCreate(BaseModel):
    """Payload for placing a new order at a table."""

    table_id: int
    items: Annotated[list[OrderItemCreate], Field(min_length=1)]
    notes: str | None = None


# ---------------------------------------------------------------------------
# Internal minimal models for relationship-backed computed fields.
# Populated via from_attributes=True; excluded from serialised output.
# ---------------------------------------------------------------------------

class _MenuItemMinimal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class _TableMinimal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    number: int


class _UserMinimal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: str


class OrderItemResponse(BaseModel):
    """Order line item returned by the API, with dish name resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    menu_item_id: int
    quantity: int
    unit_price: Decimal
    status: str
    notes: str | None = None

    # Loaded via selectin; excluded so it does not appear in the JSON output.
    menu_item: _MenuItemMinimal | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def menu_item_name(self) -> str:
        """Dish name resolved from the menu_item relationship."""
        return self.menu_item.name if self.menu_item else ""


class OrderResponse(BaseModel):
    """Full order record returned by the API, with denormalised table/waiter info."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    table_id: int
    waiter_id: int
    status: str
    total_amount: Decimal
    notes: str | None = None
    items: list[OrderItemResponse] = []
    created_at: datetime

    # Relationship objects — excluded from the serialised output.
    table: _TableMinimal | None = Field(default=None, exclude=True)
    waiter: _UserMinimal | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def table_number(self) -> int | None:
        """Physical table number resolved from the table relationship."""
        return self.table.number if self.table else None

    @computed_field
    @property
    def waiter_name(self) -> str | None:
        """Waiter's full name resolved from the user relationship."""
        return self.waiter.full_name if self.waiter else None


class OrderStatusUpdate(BaseModel):
    """Change only the lifecycle status of an existing order."""

    status: OrderStatus


class KitchenQueueItem(BaseModel):
    """Flat projection of an order item for the kitchen display board."""

    order_id: int
    table_number: int
    item_id: int
    dish_name: str
    quantity: int
    notes: str | None
    status: str
    created_at: datetime
