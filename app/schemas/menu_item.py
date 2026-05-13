from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

MenuCategory = Literal[
    "appetizer", "soup", "main_course", "dessert", "beverage", "alcohol"
]


class MenuItemCreate(BaseModel):
    """Payload for adding a new item to the menu."""

    name: str
    description: str | None = None
    category: MenuCategory
    price: Annotated[Decimal, Field(ge=Decimal("0"), decimal_places=2)]
    preparation_time_minutes: Annotated[int, Field(ge=1, le=300)]
    is_available: bool = True
    calories: int | None = None


class MenuItemUpdate(BaseModel):
    """Partial update for an existing menu item — all fields optional."""

    name: str | None = None
    description: str | None = None
    category: MenuCategory | None = None
    price: Annotated[Decimal, Field(ge=Decimal("0"), decimal_places=2)] | None = None
    preparation_time_minutes: Annotated[int, Field(ge=1, le=300)] | None = None
    is_available: bool | None = None
    calories: int | None = None


class MenuItemResponse(BaseModel):
    """Full menu item record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    category: str
    price: Decimal
    preparation_time_minutes: int
    is_available: bool
    calories: int | None
