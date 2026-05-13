from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_role
from app.models.order import Order
from app.models.user import User
from app.repositories.order_repository import order_repository
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get(
    "/",
    response_model=list[OrderResponse],
    summary="List orders",
)
async def list_orders(
    status: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[Order]:
    """Return orders visible to the current user.

    Admins and managers see all orders; waiters see only their own.
    Optionally filter by *status*.
    """
    if current_user.role in ("admin", "manager"):
        orders = (
            await order_repository.get_by_status(db, status)
            if status
            else await order_repository.get_all(db)
        )
    else:
        orders = await order_repository.get_by_waiter(db, current_user.id)
        if status:
            orders = [o for o in orders if o.status == status]
    return orders


@router.get(
    "/active",
    response_model=list[OrderResponse],
    summary="List active orders",
)
async def list_active_orders(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Order]:
    """Return all orders that have not yet been paid or cancelled."""
    return await order_repository.get_active_orders(db)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get a single order",
)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Order:
    """Return a specific order by its primary key, or 404 if not found."""
    order = await order_repository.get(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found")
    return order


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new order",
)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(require_role("admin", "manager", "waiter")),
    db: AsyncSession = Depends(get_db),
) -> Order:
    """Create an order at a table, validating availability and item stock.

    The waiter who places the order is recorded automatically.
    The table status is set to 'occupied' upon success.
    """
    return await order_service.create_order(db, data.table_id, current_user.id, data)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Advance order status",
)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Order:
    """Transition an order to the next lifecycle status.

    Allowed transitions are enforced by the state machine.
    Waiters may only update their own orders.
    """
    return await order_service.update_order_status(db, order_id, data.status, current_user)


@router.post(
    "/{order_id}/close",
    response_model=OrderResponse,
    summary="Close (pay) an order",
)
async def close_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager", "waiter")),
) -> Order:
    """Mark the order as paid and release the table back to 'free'."""
    return await order_service.close_order(db, order_id)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an order",
)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Cancel a pending or confirmed order and free the table.

    Orders in preparing/ready/served/paid state cannot be cancelled.
    """
    await order_service.cancel_order(db, order_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
