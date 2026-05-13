from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import User
from app.repositories.order_repository import order_repository
from app.repositories.user_repository import user_repository
from app.schemas.staff import StaffResponse, WaiterStats

router = APIRouter(
    prefix="/staff",
    tags=["Staff"],
    dependencies=[Depends(require_role("admin", "manager"))],
)


@router.get(
    "/",
    response_model=list[StaffResponse],
    summary="List all staff",
)
async def list_staff(
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    """Return all active restaurant staff members."""
    return await user_repository.get_active_staff(db)


@router.get(
    "/stats",
    response_model=list[WaiterStats],
    summary="Waiter performance statistics",
)
async def waiter_stats(
    db: AsyncSession = Depends(get_db),
) -> list[WaiterStats]:
    """Return order count and total revenue for every waiter.

    Only paid orders are counted towards revenue.
    """
    staff = await user_repository.get_active_staff(db)
    result: list[WaiterStats] = []
    for member in staff:
        if member.role not in ("waiter", "manager", "admin"):
            continue
        orders = await order_repository.get_by_waiter(db, member.id)
        paid = [o for o in orders if o.status == "paid"]
        revenue = sum((o.total_amount for o in paid), Decimal("0"))
        result.append(
            WaiterStats(
                waiter_id=member.id,
                full_name=member.full_name,
                orders_count=len(paid),
                total_revenue=revenue,
            )
        )
    return result


@router.get(
    "/{user_id}",
    response_model=StaffResponse,
    summary="Get a staff member",
)
async def get_staff_member(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return a staff member by their primary key, or 404 if not found."""
    user = await user_repository.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return user


@router.patch(
    "/{user_id}/deactivate",
    response_model=StaffResponse,
    summary="Deactivate a staff account",
)
async def deactivate_staff(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Set is_active=False on a staff account, preventing further logins."""
    user = await user_repository.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return await user_repository.update(db, user, {"is_active": False})
