from app.repositories.menu_repository import MenuRepository, menu_repository
from app.repositories.order_repository import OrderRepository, order_repository
from app.repositories.table_repository import TableRepository, table_repository
from app.repositories.user_repository import UserRepository, user_repository

__all__ = [
    "UserRepository",
    "user_repository",
    "TableRepository",
    "table_repository",
    "MenuRepository",
    "menu_repository",
    "OrderRepository",
    "order_repository",
]
