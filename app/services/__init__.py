from app.services.auth_service import AuthService, auth_service
from app.services.kitchen_service import KitchenService, kitchen_service
from app.services.menu_service import MenuService, menu_service
from app.services.order_service import OrderService, order_service
from app.services.table_service import TableService, table_service

__all__ = [
    "AuthService", "auth_service",
    "TableService", "table_service",
    "MenuService", "menu_service",
    "OrderService", "order_service",
    "KitchenService", "kitchen_service",
]
