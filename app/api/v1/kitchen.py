from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.order_item import OrderItem
from app.models.user import User
from app.schemas.order import KitchenQueueItem, OrderItemResponse
from app.schemas.staff import KitchenStats
from app.services.kitchen_service import kitchen_service

router = APIRouter(prefix="/kitchen", tags=["Kitchen"])


def _to_queue_item(item: OrderItem) -> KitchenQueueItem:
    """Map an ORM OrderItem (with loaded relationships) to the kitchen display schema."""
    return KitchenQueueItem(
        order_id=item.order_id,
        table_number=item.order.table.number if (item.order and item.order.table) else 0,
        item_id=item.id,
        dish_name=item.menu_item.name if item.menu_item else "",
        quantity=item.quantity,
        notes=item.notes,
        status=item.status,
        created_at=item.created_at,
    )


@router.get(
    "/queue",
    response_model=list[KitchenQueueItem],
    summary="Get kitchen order queue",
)
async def get_queue(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager", "chef")),
) -> list[KitchenQueueItem]:
    """Return all pending and preparing order items, oldest first.

    Each entry includes the table number and dish name for kitchen display.
    """
    items = await kitchen_service.get_queue(db)
    return [_to_queue_item(item) for item in items]


@router.patch(
    "/items/{item_id}/preparing",
    response_model=OrderItemResponse,
    summary="Mark item as preparing",
)
async def mark_preparing(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("chef", "admin")),
) -> OrderItem:
    """Advance a pending order item to 'preparing'.

    Automatically sets the parent order to 'preparing' when the first item starts.
    """
    return await kitchen_service.mark_preparing(db, item_id)


@router.patch(
    "/items/{item_id}/ready",
    response_model=OrderItemResponse,
    summary="Mark item as ready",
)
async def mark_ready(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("chef", "admin")),
) -> OrderItem:
    """Advance a preparing order item to 'ready'.

    When every non-cancelled item in the order is ready, the order itself
    is also promoted to 'ready'.
    """
    return await kitchen_service.mark_ready(db, item_id)


@router.get(
    "/stats",
    response_model=KitchenStats,
    summary="Get kitchen statistics",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager", "chef")),
) -> KitchenStats:
    """Return a live snapshot of kitchen workload and average preparation time."""
    return await kitchen_service.get_stats(db)
