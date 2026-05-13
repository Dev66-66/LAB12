from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

TableStatus = Literal["free", "occupied", "reserved", "maintenance"]


class TableCreate(BaseModel):
    """Payload for registering a new dining table."""

    number: Annotated[int, Field(gt=0)]
    capacity: Annotated[int, Field(ge=1, le=20)]
    location: str | None = None


class TableUpdate(BaseModel):
    """Partial update for an existing table — all fields optional."""

    number: Annotated[int, Field(gt=0)] | None = None
    capacity: Annotated[int, Field(ge=1, le=20)] | None = None
    location: str | None = None
    status: TableStatus | None = None


class TableStatusUpdate(BaseModel):
    """Change only the availability status of a table."""

    status: TableStatus


class TableResponse(BaseModel):
    """Full table record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    capacity: int
    status: str
    location: str | None
    created_at: datetime
