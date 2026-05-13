from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.repositories.menu_repository import menu_repository
from app.repositories.order_repository import order_repository
from app.repositories.table_repository import table_repository
from app.schemas.order import OrderCreate

# ---------------------------------------------------------------------------
# Valid status transitions for the order state machine.
# ---------------------------------------------------------------------------
_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"ready"},
    "ready": {"served"},
    "served": {"paid"},
}


class OrderService:
    """Business logic for order lifecycle management."""

    async def create_order(
        self,
        db: AsyncSession,
        table_id: int,
        waiter_id: int,
        data: OrderCreate,
    ) -> Order:
        """Place a new order: validate table & items, persist, update table status."""
        table = await table_repository.get(db, table_id)
        if table is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {table_id} not found",
            )
        if table.status == "occupied":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Table is already occupied",
            )

        # Validate every requested item upfront and snapshot the current price.
        item_rows: list[dict] = []
        total = Decimal("0.00")
        for oi in data.items:
            menu_item = await menu_repository.get(db, oi.menu_item_id)
            if menu_item is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Menu item {oi.menu_item_id} not found",
                )
            if not menu_item.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item '{menu_item.name}' is not available",
                )
            unit_price = menu_item.price
            total += unit_price * oi.quantity
            item_rows.append(
                {
                    "menu_item_id": oi.menu_item_id,
                    "quantity": oi.quantity,
                    "unit_price": unit_price,
                    "notes": oi.notes,
                }
            )

        # Persist the order and all its items in a single atomic transaction.
        order = Order(
            table_id=table_id,
            waiter_id=waiter_id,
            notes=data.notes,
            total_amount=total.quantize(Decimal("0.01")),
        )
        db.add(order)
        await db.flush()  # obtain order.id without committing yet

        for row in item_rows:
            db.add(OrderItem(order_id=order.id, **row))

        await db.commit()
        await db.refresh(order)
        await table_repository.update(db, table, {"status": "occupied"})
        return order

    async def update_order_status(
        self,
        db: AsyncSession,
        order_id: int,
        new_status: str,
        current_user: User,
    ) -> Order:
        """Advance or cancel an order according to the allowed state machine."""
        order = await order_repository.get(db, order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )

        # Waiters may only modify their own orders.
        is_own_order = order.waiter_id == current_user.id
        if current_user.role not in ("admin", "manager") and not is_own_order:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own orders",
            )

        allowed = _TRANSITIONS.get(order.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition: '{order.status}' → '{new_status}'. "
                    f"Allowed: {sorted(allowed) or 'none'}"
                ),
            )

        return await order_repository.update(db, order, {"status": new_status})

    async def close_order(self, db: AsyncSession, order_id: int) -> Order:
        """Mark an order as paid and free the table."""
        order = await order_repository.get(db, order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        order = await order_repository.update(db, order, {"status": "paid"})
        table = await table_repository.get(db, order.table_id)
        if table is not None:
            await table_repository.update(db, table, {"status": "free"})
        return order

    async def cancel_order(
        self, db: AsyncSession, order_id: int, current_user: User
    ) -> Order:
        """Cancel a pending or confirmed order and release the table."""
        order = await order_repository.get(db, order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        if order.status not in ("pending", "confirmed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel an order with status '{order.status}'",
            )
        is_own_order = order.waiter_id == current_user.id
        if current_user.role not in ("admin", "manager") and not is_own_order:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own orders",
            )

        order = await order_repository.update(db, order, {"status": "cancelled"})
        table = await table_repository.get(db, order.table_id)
        if table is not None and table.status == "occupied":
            await table_repository.update(db, table, {"status": "free"})
        return order


order_service = OrderService()
