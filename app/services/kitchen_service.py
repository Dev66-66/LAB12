from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order_item import OrderItem
from app.repositories.base_repository import BaseRepository
from app.repositories.order_repository import order_repository
from app.schemas.staff import KitchenStats

_item_repo: BaseRepository[OrderItem] = BaseRepository(OrderItem)


class KitchenService:
    """Business logic for the kitchen order queue."""

    async def get_queue(self, db: AsyncSession) -> list[OrderItem]:
        """Return pending/preparing items ordered oldest-first."""
        return await order_repository.get_kitchen_queue(db)

    async def mark_preparing(self, db: AsyncSession, item_id: int) -> OrderItem:
        """Transition an item from pending → preparing.

        When the first item of an order becomes preparing,
        the parent order is also advanced to 'preparing'.
        """
        item = await _item_repo.get(db, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order item {item_id} not found",
            )
        if item.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {item_id} is '{item.status}', expected 'pending'",
            )
        item = await _item_repo.update(db, item, {"status": "preparing"})

        # Advance the parent order to "preparing" if it is confirmed.
        # Orders in other states (pending, already preparing, etc.) are left as-is.
        order = await order_repository.get(db, item.order_id)
        if order is not None and order.status in ("confirmed", "pending"):
            await order_repository.update(db, order, {"status": "preparing"})

        return item

    async def mark_ready(self, db: AsyncSession, item_id: int) -> OrderItem:
        """Transition an item from preparing → ready.

        When all items in the order are ready, the order status
        is advanced to 'ready' as well.
        """
        item = await _item_repo.get(db, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order item {item_id} not found",
            )
        if item.status != "preparing":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {item_id} is '{item.status}', expected 'preparing'",
            )
        item = await _item_repo.update(db, item, {"status": "ready"})

        # Check whether every non-cancelled item in this order is now ready.
        result = await db.execute(
            select(OrderItem).where(
                OrderItem.order_id == item.order_id,
                OrderItem.status.notin_(["cancelled", "ready"]),
            )
        )
        remaining = result.scalars().all()
        if not remaining:
            order = await order_repository.get(db, item.order_id)
            if order is not None and order.status == "preparing":
                await order_repository.update(db, order, {"status": "ready"})

        return item

    async def get_stats(self, db: AsyncSession) -> KitchenStats:
        """Aggregate kitchen workload: counts by status and avg prep time today."""
        counts_result = await db.execute(
            select(OrderItem.status, func.count(OrderItem.id))
            .where(OrderItem.status.in_(["pending", "preparing", "ready"]))
            .group_by(OrderItem.status)
        )
        counts: dict[str, int] = {row[0]: row[1] for row in counts_result.all()}

        # Average preparation time: for items marked ready today,
        # measure elapsed seconds between created_at and updated_at.
        today_start = datetime.combine(date.today(), datetime.min.time())
        ready_result = await db.execute(
            select(OrderItem.created_at, OrderItem.updated_at).where(
                OrderItem.status == "ready",
                OrderItem.updated_at >= today_start,
            )
        )
        rows = ready_result.all()
        avg_minutes: float | None = None
        if rows:
            total_seconds = sum(
                (r.updated_at - r.created_at).total_seconds() for r in rows
            )
            avg_minutes = round(total_seconds / len(rows) / 60, 2)

        return KitchenStats(
            items_pending=counts.get("pending", 0),
            items_preparing=counts.get("preparing", 0),
            items_ready=counts.get("ready", 0),
            avg_prep_time_minutes=avg_minutes,
        )


kitchen_service = KitchenService()
