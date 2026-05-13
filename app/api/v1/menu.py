from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_role
from app.models.menu_item import MenuItem
from app.models.user import User
from app.repositories.menu_repository import menu_repository
from app.schemas.menu_item import MenuItemCreate, MenuItemResponse, MenuItemUpdate
from app.services.menu_service import menu_service

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get(
    "/",
    response_model=list[MenuItemResponse],
    summary="List menu items",
)
async def list_menu(
    category: str | None = None,
    available_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[MenuItem]:
    """Return menu items optionally filtered by category and/or availability."""
    return await menu_service.search_items(db, query=None, category=category, available_only=available_only)


@router.get(
    "/search",
    response_model=list[MenuItemResponse],
    summary="Search menu items",
)
async def search_menu(
    q: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[MenuItem]:
    """Full-text search across item name and description (case-insensitive)."""
    return await menu_service.search_items(db, query=q, category=None, available_only=False)


@router.get(
    "/{item_id}",
    response_model=MenuItemResponse,
    summary="Get a single menu item",
)
async def get_menu_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> MenuItem:
    """Return a menu item by its primary key, or 404 if not found."""
    item = await menu_repository.get(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item {item_id} not found")
    return item


@router.post(
    "/",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a menu item",
)
async def create_menu_item(
    data: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
) -> MenuItem:
    """Add a new dish or drink to the menu."""
    return await menu_service.create_item(db, data)


@router.put(
    "/{item_id}",
    response_model=MenuItemResponse,
    summary="Update a menu item",
)
async def update_menu_item(
    item_id: int,
    data: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
) -> MenuItem:
    """Replace the editable fields of an existing menu item."""
    return await menu_service.update_item(db, item_id, data)


@router.patch(
    "/{item_id}/availability",
    response_model=MenuItemResponse,
    summary="Toggle item availability",
)
async def toggle_availability(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
) -> MenuItem:
    """Flip the is_available flag — hide or expose an item without deleting it."""
    return await menu_service.toggle_availability(db, item_id)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a menu item",
)
async def delete_menu_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> Response:
    """Permanently remove a menu item. Requires admin role."""
    deleted = await menu_repository.delete(db, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item {item_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
