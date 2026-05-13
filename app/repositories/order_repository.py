from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.order_item import OrderItem
from app.repositories.base_repository import BaseRepository

_ACTIVE_STATUSES = ("pending", "confirmed", "preparing", "ready", "served")
_KITCHEN_STATUSES = ("pending", "preparing")


class OrderRepository(BaseRepository[Order]):
    """Data-access methods for the Order model."""

    def __init__(self) -> None:
        super().__init__(Order)

    async def get_by_table(self, db: AsyncSession, table_id: int) -> list[Order]:
        """Return all orders placed at the given table."""
        result = await db.execute(
            select(Order).where(Order.table_id == table_id)
        )
        return list(result.scalars().all())

    async def get_by_waiter(self, db: AsyncSession, waiter_id: int) -> list[Order]:
        """Return all orders assigned to the given waiter."""
        result = await db.execute(
            select(Order).where(Order.waiter_id == waiter_id)
        )
        return list(result.scalars().all())

    async def get_by_status(self, db: AsyncSession, status: str) -> list[Order]:
        """Return all orders with the given lifecycle status."""
        result = await db.execute(
            select(Order).where(Order.status == status)
        )
        return list(result.scalars().all())

    async def get_active_orders(self, db: AsyncSession) -> list[Order]:
        """Return all orders that have not yet been paid or cancelled."""
        result = await db.execute(
            select(Order).where(Order.status.in_(_ACTIVE_STATUSES))
        )
        return list(result.scalars().all())

    async def get_kitchen_queue(self, db: AsyncSession) -> list[OrderItem]:
        """Return pending/preparing order items sorted by creation time ascending.

        Eagerly loads menu_item and order.table for kitchen display.
        """
        result = await db.execute(
            select(OrderItem)
            .where(OrderItem.status.in_(_KITCHEN_STATUSES))
            .options(
                selectinload(OrderItem.menu_item),
                selectinload(OrderItem.order).selectinload(Order.table),
            )
            .order_by(OrderItem.created_at.asc())
        )
        return list(result.scalars().all())


order_repository = OrderRepository()
