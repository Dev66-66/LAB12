from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem
from app.repositories.menu_repository import menu_repository
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate


class MenuService:
    """Business logic for menu item management."""

    async def create_item(self, db: AsyncSession, data: MenuItemCreate) -> MenuItem:
        """Add a new item to the menu."""
        return await menu_repository.create(db, data.model_dump())

    async def update_item(
        self, db: AsyncSession, item_id: int, data: MenuItemUpdate
    ) -> MenuItem:
        """Update an existing menu item; raises 404 if not found."""
        item = await menu_repository.get(db, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item {item_id} not found",
            )
        updates = data.model_dump(exclude_unset=True)
        return await menu_repository.update(db, item, updates)

    async def toggle_availability(self, db: AsyncSession, item_id: int) -> MenuItem:
        """Flip the is_available flag of a menu item."""
        item = await menu_repository.get(db, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item {item_id} not found",
            )
        return await menu_repository.update(
            db, item, {"is_available": not item.is_available}
        )

    async def search_items(
        self,
        db: AsyncSession,
        query: str | None,
        category: str | None,
        available_only: bool,
    ) -> list[MenuItem]:
        """Return menu items filtered by query text, category, and availability."""
        if query:
            items = await menu_repository.search(db, query)
        elif category:
            items = await menu_repository.get_by_category(db, category)
        elif available_only:
            items = await menu_repository.get_available(db)
        else:
            items = await menu_repository.get_all(db)

        if category and query:
            items = [i for i in items if i.category == category]
        if available_only:
            items = [i for i in items if i.is_available]
        return items


menu_service = MenuService()
