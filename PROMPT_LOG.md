# Prompt Log — Лабораторная работа №12

Журнал выполненных промптов.

---

## Промпт 0.1 — Git и структура папок

**Дата:** 2026-05-13

**Промпт:** Инициализируй git-репозиторий для проекта «Система управления рестораном» и создай файловую структуру. Выполни: 1) git init, 2) git remote add origin https://github.com/Dev66-66/LAB12.git. Создай файловую структуру проекта restaurant_management/ со всеми указанными директориями и файлами (__init__.py пустые, остальные — заглушки). Создай README.md с данными студента и PROMPT_LOG.md с первой записью. Коммит: «chore: initialize git repository and project directory structure».

**Результат:** Инициализирован git-репозиторий, добавлен remote origin. Создана полная файловая структура проекта: директории app/, alembic/, tests/, docs/, scripts/, .github/workflows/; все __init__.py файлы (пустые); заглушки для всех модулей API, core, models, schemas, services, repositories, тестов, конфигурационных файлов (Dockerfile, docker-compose.yml, alembic.ini, ci.yml, ai_review.yml). Созданы README.md с данными студента и PROMPT_LOG.md.

---

## Промпт 0.2 — Конфигурация окружения

**Дата:** 2026-05-13

**Промпт:** Создай .gitignore для Python/FastAPI проекта. Обязательно исключи: __pycache__/, *.pyc, *.pyo, .env, .venv/, venv/, dist/, build/, *.egg-info/, .pytest_cache/, htmlcov/, .coverage, coverage.xml, .mypy_cache/, .ruff_cache/, *.log, *.sqlite3, alembic/versions/*.py (кроме файла alembic/versions/README). НЕ исключай: alembic/versions/README, pyproject.toml, .env.example. Создай .env.example с переменными окружения для PostgreSQL и JWT. Обнови PROMPT_LOG.md. Коммит: «chore: add .gitignore and .env.example».

**Результат:** Создан .gitignore с исключениями для Python, виртуальных окружений, артефактов сборки, тестовых кешей, логов, .env и alembic-миграций (с сохранением README). Создан .env.example с переменными DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB. Обновлён PROMPT_LOG.md.

---

## Промпт 0.3 — pyproject.toml

**Дата:** 2026-05-13

**Промпт:** Создай pyproject.toml для проекта restaurant_management. Формат: PEP 517, build-system = hatchling. name = "restaurant-management", version = "1.0.0". [project.dependencies]: fastapi>=0.111.0, uvicorn[standard]>=0.29.0, sqlalchemy[asyncio]>=2.0.0, asyncpg>=0.29.0, alembic>=1.13.0, python-jose[cryptography]>=3.3.0, passlib[bcrypt]>=1.7.4, pydantic-settings>=2.2.0, pydantic[email]>=2.7.0, python-multipart>=0.0.9. [project.optional-dependencies] dev: pytest>=8.2.0, pytest-asyncio>=0.23.0, pytest-cov>=5.0.0, httpx>=0.27.0, aiosqlite>=0.20.0, faker>=25.0.0, ruff>=0.4.0, mypy>=1.10.0, bandit>=1.7.0. Настройки инструментов: pytest (asyncio_mode=auto), ruff (line-length=88, select E/F/I/N/UP), coverage, mypy (python_version=3.12). После создания выполни pip install -e ".[dev]". Коммит: «chore: add pyproject.toml with all dependencies».

**Результат:** Создан pyproject.toml с hatchling в качестве build-backend, 10 production-зависимостями и 9 dev-зависимостями, секциями tool.pytest.ini_options, tool.ruff, tool.ruff.lint, tool.coverage.run, tool.mypy, tool.hatch.build.targets.wheel. Выполнен pip install -e ".[dev]" — все зависимости установлены успешно (restaurant-management 1.0.0). Обновлён PROMPT_LOG.md.

---

## Промпт 1.1 — SQLAlchemy ORM-модели

**Дата:** 2026-05-13

**Промпт:** Реализуй SQLAlchemy 2.0 async ORM-модели для системы управления рестораном. app/models/base.py: Base = DeclarativeBase(), TimestampMixin с created_at/updated_at через Mapped[datetime]. app/models/user.py — модель User(Base, TimestampMixin): id, username (String(50), unique, index), email (String(255), unique, index), hashed_password, full_name (String(100)), role (Enum admin/manager/waiter/chef), is_active (bool), relationship orders→Order. app/models/table.py — Table: id, number (unique), capacity, status (Enum free/occupied/reserved/maintenance), location (Optional[str]), relationship orders→Order. app/models/menu_item.py — MenuItem: id, name, description (Optional[Text]), category (Enum 6 значений, index), price (Numeric(10,2)), preparation_time_minutes, is_available (bool, index), calories (Optional[int]). app/models/order.py — Order: id, table_id (FK), waiter_id (FK), status (Enum 7 значений, index), total_amount (Numeric(10,2)), notes (Optional[Text]), relationships table/waiter/items. app/models/order_item.py — OrderItem: id, order_id (FK), menu_item_id (FK), quantity, unit_price (Numeric(10,2)), status (Enum 5 значений), notes (Optional[String(255)]), relationships order/menu_item. Все модели с Mapped[], docstring, lazy="selectin", back_populates. Импорт через models/__init__.py. Коммит: «feat(models): add SQLAlchemy ORM models for all restaurant entities».

**Результат:** Реализованы 5 ORM-моделей: User (таблица users), Table (tables), MenuItem (menu_items), Order (orders), OrderItem (order_items). Создан TimestampMixin с Mapped[datetime]. Настроены все FK-связи и back_populates. Все модели экспортируются через app/models/__init__.py. Импорт проверен — ошибок нет (все 5 таблиц: users, tables, menu_items, orders, order_items).

---

## Промпт 1.2 — Core-слой (config, security, dependencies, main)

**Дата:** 2026-05-13

**Промпт:** Реализуй core-слой для restaurant_management. app/core/config.py: Settings(BaseSettings) с полями DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, APP_NAME, APP_VERSION, DEBUG; синглтон settings. app/core/security.py: PWD_CONTEXT=CryptContext(bcrypt), hash_password, verify_password, create_access_token (с exp-клеймом), decode_token (None при ошибке). app/core/dependencies.py: get_db() — AsyncGenerator с async_sessionmaker; oauth2_scheme=OAuth2PasswordBearer; get_current_user() — декодирует токен, ищет по username, 401; get_current_active_user() — 403 если деактивирован; require_role(*roles) — фабрика dependency, 403 если роль не подходит. app/main.py: FastAPI с lifespan (create_all), CORSMiddleware (origins=["*"]), 6 роутеров с prefix="/api/v1", handler для RequestValidationError→422, GET /health. Коммит: «feat(core): add config, JWT security, and dependency injection».

**Результат:** Реализованы app/core/config.py (Settings + синглтон), app/core/security.py (bcrypt + JWT), app/core/dependencies.py (get_db, get_current_user, get_current_active_user, require_role), app/main.py (FastAPI + lifespan + CORS + роутеры + /health). Заглушки роутеров api/v1/ заполнены минимальными APIRouter. Добавлено ограничение bcrypt<5.0.0 в pyproject.toml для совместимости с passlib. Все функции проверены: hash/verify пароля, JWT encode/decode, None при невалидном токене, маршруты FastAPI зарегистрированы.

---

## Промпт 1.3 — Repository-слой

**Дата:** 2026-05-13

**Промпт:** Реализуй Repository-слой для restaurant_management. base_repository.py — Generic[ModelType]: get, get_all (skip/limit), create, update, delete (bool). user_repository.py — UserRepository: get_by_email, get_by_username, get_active_staff. table_repository.py — TableRepository: get_by_number, get_by_status, get_available (status=free + capacity>=min_capacity). menu_repository.py — MenuRepository: get_by_category, get_available (is_available=True), search (ilike по name OR description). order_repository.py — OrderRepository: get_by_table, get_by_waiter, get_by_status, get_active_orders (pending/confirmed/preparing/ready/served), get_kitchen_queue (OrderItem pending/preparing, order_by created_at asc, eager load menu_item + order.table). Все методы async, type hints, без бизнес-логики. Коммит: «feat(repositories): add data access layer with generic base repository».

**Результат:** Реализованы 5 файлов: base_repository.py (Generic BaseRepository с 5 методами CRUD), user_repository.py (3 метода + синглтон user_repository), table_repository.py (3 метода + синглтон), menu_repository.py (3 метода + ilike-поиск + синглтон), order_repository.py (5 методов + get_kitchen_queue с selectinload + синглтон). Обновлён repositories/__init__.py. Импорт проверен: все 5+3+3+3+5 методов зарегистрированы корректно.

---

## Промпт 1.4 — Pydantic v2 схемы

**Дата:** 2026-05-13

**Промпт:** Создай Pydantic v2 схемы для restaurant_management. auth.py: UserRegister (username, email, password, full_name, role; @field_validator password — буква+цифра), UserLogin, Token, UserResponse (from_attributes, без пароля). table.py: TableCreate (number>0, capacity 1-20), TableUpdate (все Optional), TableStatusUpdate (Literal статусов), TableResponse (from_attributes + created_at). menu_item.py: MenuItemCreate (price Decimal ge=0 decimal_places=2, prep_time 1-300), MenuItemUpdate (все Optional), MenuItemResponse (from_attributes + is_available). order.py: OrderItemCreate (quantity 1-99), OrderCreate (items min_length=1), OrderItemResponse (computed menu_item_name через @computed_field + _MenuItemMinimal exclude=True), OrderResponse (computed table_number + waiter_name), OrderStatusUpdate, KitchenQueueItem. staff.py: StaffResponse, WaiterStats, KitchenStats. schemas/__init__.py экспортирует все 19 классов. Коммит: «feat(schemas): add Pydantic v2 schemas with validators and computed fields».

**Результат:** Реализованы 5 файлов схем + __init__.py. Ключевые решения: @field_validator на password (буква + цифра), computed_field + @property для menu_item_name/table_number/waiter_name через вспомогательные _*Minimal модели с exclude=True. Все валидаторы проверены: password без цифры → ошибка, password без буквы → ошибка, capacity>20 → ошибка, пустой items → ошибка. Все 19 классов экспортируются через schemas/__init__.py.

---

## Промпт 1.5 — Сервисный слой

**Дата:** 2026-05-13

**Промпт:** Реализуй сервисный слой для restaurant_management. auth_service.py — AuthService: register (уникальность username/email → 409, hash_password, create), authenticate (get_by_username → 401, verify_password → 401, is_active → 403), create_token (JWT с sub+role). table_service.py — TableService: create_table (уникальность number → 409), update_status (404), get_available. menu_service.py — MenuService: create_item, update_item (404), toggle_availability (NOT is_available), search_items (query/category/available_only фильтры). order_service.py — OrderService: create_order (404 стол, 409 occupied, 404/400 items, snapshot unit_price, total_amount, статус стола→occupied), update_order_status (конечный автомат: pending→confirmed/cancelled, confirmed→preparing/cancelled, preparing→ready, ready→served, served→paid; 403 для чужих заказов у waiter), close_order (paid + стол→free), cancel_order (только pending/confirmed, стол→free). kitchen_service.py — KitchenService: get_queue, mark_preparing (pending→preparing + Order→preparing если первый), mark_ready (preparing→ready + Order→ready если все items готовы), get_stats (counts по статусам + avg_prep_time через updated_at-created_at для ready за сегодня). Коммит: «feat(services): add business logic layer with state machine for orders».

**Результат:** Реализованы 5 сервисных файлов + __init__.py. Конечный автомат заказов: pending→{confirmed,cancelled}, confirmed→{preparing,cancelled}, preparing→{ready}, ready→{served}, served→{paid}. KitchenService.mark_ready автоматически переводит Order→ready когда все items готовы. KitchenStats.avg_prep_time вычисляется через updated_at-created_at для ready-items за текущий день. Все импорты и методы проверены.

---
