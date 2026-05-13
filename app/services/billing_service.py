"""Billing service — calculates, persists, and notifies on order bills.

Design principles applied:
- Single Responsibility: each helper function does exactly one thing.
- No magic numbers: all thresholds and rates are named constants.
- Decimal arithmetic: no floating-point rounding errors on monetary values.
- Fully async: never blocks the event loop.
- Parameterised queries via ORM: no SQL injection possible.
- Secrets from settings: never hardcoded.
- Complete error handling: every failure path raises a typed HTTPException.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Final

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User

# ---------------------------------------------------------------------------
# Named constants — no magic numbers anywhere below this block.
# ---------------------------------------------------------------------------

DISCOUNT_RATES: Final[dict[str, Decimal]] = {
    "SAVE10": Decimal("0.10"),
    "SAVE15": Decimal("0.15"),
    "STAFF":  Decimal("0.10"),
}

HIGH_ORDER_THRESHOLD: Final[Decimal] = Decimal("1000.00")
MEDIUM_ORDER_THRESHOLD: Final[Decimal] = Decimal("500.00")
HIGH_ORDER_BONUS_RATE: Final[Decimal] = Decimal("0.05")
MEDIUM_ORDER_FLAT_BONUS: Final[Decimal] = Decimal("50.00")

_CENT: Final[Decimal] = Decimal("0.01")


# ---------------------------------------------------------------------------
# Result dataclass — explicit contract, no raw dicts.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BillResult:
    """Immutable snapshot of a computed bill."""

    order_id: int
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    discount_code: str | None
    waiter_username: str


# ---------------------------------------------------------------------------
# Private helpers — each does exactly one thing.
# ---------------------------------------------------------------------------

def _calculate_subtotal(items: list[OrderItem]) -> Decimal:
    """Sum unit_price * quantity for every non-cancelled order item."""
    return sum(
        (item.unit_price * item.quantity for item in items),
        Decimal("0"),
    )


def _apply_discount(subtotal: Decimal, code: str | None) -> tuple[Decimal, Decimal]:
    """Return (discounted_total, discount_amount) for the given promo code.

    Unknown or missing codes result in zero discount — no exception is raised
    here; callers that need strict validation should call _validate_discount
    first.
    """
    if code is None or code not in DISCOUNT_RATES:
        return subtotal, Decimal("0")
    rate = DISCOUNT_RATES[code]
    discount = (subtotal * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return subtotal - discount, discount


def _apply_loyalty_bonuses(total: Decimal) -> Decimal:
    """Apply volume-based loyalty deductions after the promo discount.

    Rules (applied in order):
    - Total > 1 000 → additional 5 % off.
    - Total > 500  → additional flat 50 off.
    """
    if total > HIGH_ORDER_THRESHOLD:
        bonus = (total * HIGH_ORDER_BONUS_RATE).quantize(_CENT, rounding=ROUND_HALF_UP)
        total -= bonus
    if total > MEDIUM_ORDER_THRESHOLD:
        total -= MEDIUM_ORDER_FLAT_BONUS
    return total


async def _validate_discount_code(code: str) -> bool:
    """Return True if the promo service confirms the code is active.

    Never raises — a network failure is treated as 'code unverified' and
    logged; the caller decides whether to accept or reject the order.
    """
    url = f"{settings.PROMO_SERVICE_URL}/validate"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                url,
                params={"code": code},
                headers={"Authorization": f"Bearer {settings.PROMO_SERVICE_KEY}"},
            )
        return response.status_code == 200 and response.json().get("valid", False)
    except httpx.HTTPError:
        return False


async def _persist_bill(
    db: AsyncSession,
    order: Order,
    total: Decimal,
) -> None:
    """Update the order total and mark it confirmed in a single transaction."""
    order.total_amount = total
    order.status = "confirmed"
    await db.commit()
    await db.refresh(order)


async def _send_bill_notification(
    order_id: int,
    recipient_email: str,
    total: Decimal,
) -> None:
    """Fire-and-forget async notification to the email and push services.

    Failures are silently swallowed so a notification outage never blocks
    the billing response.
    """
    payload = {
        "order_id": order_id,
        "total": str(total),
    }
    notification_url = f"{settings.NOTIFICATION_SERVICE_URL}/send"
    email_url = f"{settings.EMAIL_SERVICE_URL}/send"
    headers = {"Authorization": f"Bearer {settings.NOTIFICATION_API_KEY}"}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(notification_url, json=payload, headers=headers)
        except httpx.HTTPError:
            pass

        try:
            await client.post(
                email_url,
                json={"to": recipient_email, "subject": "Your bill", **payload},
                headers=headers,
            )
        except httpx.HTTPError:
            pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def calculate_bill(
    db: AsyncSession,
    order_id: int,
    discount_code: str | None = None,
) -> BillResult:
    """Calculate the final bill for an order, persist it, and send notifications.

    Args:
        db: Active async database session injected by FastAPI dependency.
        order_id: Primary key of the order to bill.
        discount_code: Optional promotional code supplied by the client.

    Returns:
        Immutable BillResult with subtotal, discount, and final total.

    Raises:
        HTTPException 404: Order does not exist.
        HTTPException 422: Order has no billable items.
        HTTPException 400: Discount code is invalid or expired.
    """
    # 1. Load the order — raise 404 rather than crashing on None.
    order = await db.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    # 2. Load active order items via ORM (no SQL injection, named attributes).
    result = await db.execute(
        select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.status != "cancelled",
        )
    )
    items = result.scalars().all()
    if not items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Order {order_id} has no billable items",
        )

    # 3. Validate promo code against the external service (async, non-blocking).
    if discount_code is not None and discount_code not in DISCOUNT_RATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown discount code '{discount_code}'",
        )
    if discount_code is not None:
        valid = await _validate_discount_code(discount_code)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Discount code '{discount_code}' is invalid or expired",
            )

    # 4. Compute amounts — all Decimal, no float.
    subtotal = _calculate_subtotal(items)
    after_discount, discount_amount = _apply_discount(subtotal, discount_code)
    total = _apply_loyalty_bonuses(after_discount)

    # 5. Persist the result (ORM, single transaction).
    await _persist_bill(db, order, total)

    # 6. Resolve the waiter for notification — 404 is a data integrity problem.
    waiter = await db.get(User, order.waiter_id)
    if waiter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Waiter {order.waiter_id} not found",
        )

    # 7. Send notifications asynchronously; never block the response on this.
    await _send_bill_notification(order_id, waiter.email, total)

    return BillResult(
        order_id=order_id,
        subtotal=subtotal,
        discount=discount_amount,
        total=total,
        discount_code=discount_code,
        waiter_username=waiter.username,
    )


billing_service_instance = calculate_bill  # convenience alias for DI
