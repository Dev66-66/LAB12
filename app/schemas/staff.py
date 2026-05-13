from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StaffResponse(BaseModel):
    """Compact staff member record for listings and assignments."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    is_active: bool


class WaiterStats(BaseModel):
    """Aggregated performance metrics for a single waiter."""

    waiter_id: int
    full_name: str
    orders_count: int
    total_revenue: Decimal


class KitchenStats(BaseModel):
    """Snapshot of kitchen workload by item preparation state."""

    items_pending: int
    items_preparing: int
    items_ready: int
    avg_prep_time_minutes: float | None
