# 🍽️ Restaurant Management System

> Система управления рестораном | Лабораторная работа №12, Вариант 21

**Студент:** Фомичев Ярослав Николаевич  
**Группа:** 221131  
**Вариант:** 21 — Система управления рестораном  

![CI](https://github.com/Dev66-66/LAB12/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/Dev66-66/LAB12/branch/master/graph/badge.svg)

---

## 📋 О проекте

REST API для автоматизации работы ресторана: управление столами, меню, заказами, кухонной очередью и персоналом.

**Ключевые возможности:**

| Модуль | Что умеет |
|--------|-----------|
| Столы | Регистрация, статусы (free / occupied / reserved / maintenance), фильтр свободных |
| Меню | Каталог блюд по категориям, полнотекстовый поиск, переключение доступности |
| Заказы | Создание с автоматическим расчётом суммы, машина состояний жизненного цикла |
| Кухня | Очередь блюд к приготовлению, переходы pending → preparing → ready, статистика |
| Персонал | Управление аккаунтами, деактивация, выручка по официантам |
| Безопасность | JWT-аутентификация, ролевой доступ (admin / manager / waiter / chef) |

---

## 🏗️ Архитектура

Проект построен по классической слоистой архитектуре:

```
HTTP Request
     │
     ▼
┌─────────────────────────────┐
│   API Layer  (app/api/v1/)  │  FastAPI роутеры — валидация, авторизация, HTTP
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Service Layer (services/)  │  Бизнес-логика, машина состояний заказов
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Repository Layer (repos/)  │  Async CRUD, изолированные SQL-запросы
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Model Layer (models/)      │  SQLAlchemy 2.0 ORM — декларативные модели
└────────────┬────────────────┘
             │
             ▼
        PostgreSQL 16
```

Зависимости инжектируются через FastAPI DI (`Depends`): сессия БД, текущий пользователь, проверка роли.

---

## 🛠️ Стек технологий

| Технология | Версия | Назначение |
|---|---|---|
| **Python** | 3.12 | Язык разработки |
| **FastAPI** | ≥ 0.111 | Async REST-фреймворк, OpenAPI-документация |
| **SQLAlchemy** | ≥ 2.0 | ORM, async-сессии, `Mapped[]` / `mapped_column` |
| **PostgreSQL** | 16 | Основная база данных |
| **asyncpg** | ≥ 0.29 | Async-драйвер PostgreSQL |
| **Alembic** | ≥ 1.13 | Миграции схемы БД |
| **Pydantic v2** | ≥ 2.7 | Схемы запросов / ответов, валидация |
| **python-jose** | ≥ 3.3 | JWT-токены |
| **passlib + bcrypt** | 1.7 / 4.x | Хэширование паролей |
| **httpx** | ≥ 0.27 | Async HTTP-клиент (внешние сервисы) |
| **pytest + pytest-asyncio** | ≥ 8.2 / 0.23 | Тестовый фреймворк |
| **aiosqlite** | ≥ 0.20 | In-memory SQLite для тестов |
| **Docker** | — | Контейнеризация, multi-stage build |
| **GitHub Actions** | — | CI/CD, AI code review |

---

## 🚀 Запуск

### Вариант 1: Docker (рекомендуется)

Требования: Docker Desktop ≥ 24, docker compose v2.

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Dev66-66/LAB12.git
cd LAB12

# 2. Создать .env (настройки по умолчанию уже подходят для Docker)
cp .env.example .env

# 3. Запустить PostgreSQL + приложение
docker compose up -d

# 4. Дождаться готовности (≈ 10 секунд) и заполнить тестовыми данными
docker compose exec app python -m scripts.seed_db
```

| Адрес | Описание |
|-------|----------|
| http://localhost:8000 | API |
| http://localhost:8000/docs | Swagger UI (интерактивная документация) |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/health | Health-check |

**Остановка:**

```bash
docker compose down          # остановить контейнеры
docker compose down -v       # + удалить том PostgreSQL
```

---

### Вариант 2: Локальная разработка

Требования: Python 3.12+, PostgreSQL 16 (запущенный локально).

```bash
# 1. Клонировать и перейти в папку
git clone https://github.com/Dev66-66/LAB12.git
cd LAB12

# 2. Создать и активировать виртуальное окружение
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Установить проект со всеми зависимостями для разработки
pip install -e ".[dev]"

# 4. Настроить переменные окружения
cp .env.example .env
# Открыть .env и указать DATABASE_URL для своей БД:
#   DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/restaurant_db

# 5. Применить миграции
alembic upgrade head

# 6. Заполнить тестовыми данными
python -m scripts.seed_db

# 7. Запустить сервер разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Совет:** для hot-reload файл `.env` читается автоматически через `pydantic-settings`.

---

## 🔑 Переменные окружения

Все переменные описаны в `.env.example`. Скопируйте файл в `.env` и при необходимости измените значения.

| Переменная | Описание | Пример | Обязательная |
|---|---|---|---|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql+asyncpg://postgres:postgres@db:5432/restaurant_db` | ✅ |
| `SECRET_KEY` | Секрет для подписи JWT (мин. 32 символа) | `change-me-to-random-32-char-string` | ✅ |
| `ALGORITHM` | Алгоритм JWT | `HS256` | — (по умолчанию `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена (минуты) | `30` | — (по умолчанию `30`) |
| `POSTGRES_USER` | Пользователь PostgreSQL (для docker compose) | `postgres` | — |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL (для docker compose) | `postgres` | — |
| `POSTGRES_DB` | Имя базы данных (для docker compose) | `restaurant_db` | — |

> **Безопасность:** `SECRET_KEY` в production должен быть случайной строкой ≥ 32 символов.  
> Сгенерировать: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## 🔐 Тестовые учётные записи

После запуска `python -m scripts.seed_db` в базе появятся следующие аккаунты:

| Роль | Username | Password | Права |
|---|---|---|---|
| **admin** | `admin` | `Admin123` | Полный доступ ко всем ресурсам |
| **waiter** | генерируется (3 шт.) | `Staff123` | Создание заказов, просмотр своих заказов |
| **chef** | генерируется (2 шт.) | `Staff123` | Кухонная очередь, смена статуса блюд |
| **manager** | генерируется (1 шт.) | `Staff123` | Управление столами, меню; все заказы |

Чтобы найти имена сгенерированных аккаунтов — войдите под `admin` и вызовите `GET /api/v1/staff/`.

---

## 📡 API Эндпоинты

Полная интерактивная документация доступна в Swagger UI: http://localhost:8000/docs

Для авторизации нажмите **Authorize** и введите токен, полученный от `POST /api/v1/auth/login`.

### Аутентификация (`/api/v1/auth`)

| Метод | Путь | Описание | Роль |
|---|---|---|---|
| `POST` | `/auth/register` | Регистрация нового сотрудника | — |
| `POST` | `/auth/login` | Получение JWT-токена (`form-data`) | — |
| `GET` | `/auth/me` | Профиль текущего пользователя | любой |

### Столы (`/api/v1/tables`)

| Метод | Путь | Описание | Роль |
|---|---|---|---|
| `GET` | `/tables/` | Список всех столов | любой |
| `GET` | `/tables/available` | Список свободных столов (`?min_capacity=N`) | любой |
| `GET` | `/tables/{id}` | Данные стола | любой |
| `POST` | `/tables/` | Создать стол | admin, manager |
| `PUT` | `/tables/{id}` | Обновить стол | admin, manager |
| `PATCH` | `/tables/{id}/status` | Изменить статус стола | любой |
| `DELETE` | `/tables/{id}` | Удалить стол | admin |

### Меню (`/api/v1/menu`)

| Метод | Путь | Описание | Роль |
|---|---|---|---|
| `GET` | `/menu/` | Список блюд (`?category=…&available_only=true`) | любой |
| `GET` | `/menu/search?q=…` | Полнотекстовый поиск по названию/описанию | любой |
| `GET` | `/menu/{id}` | Данные блюда | любой |
| `POST` | `/menu/` | Добавить блюдо | admin, manager |
| `PUT` | `/menu/{id}` | Обновить блюдо | admin, manager |
| `PATCH` | `/menu/{id}/availability` | Переключить доступность | admin, manager |
| `DELETE` | `/menu/{id}` | Удалить блюдо | admin |

### Заказы (`/api/v1/orders`)

| Метод | Путь | Описание | Роль |
|---|---|---|---|
| `GET` | `/orders/` | Список заказов (официант — свои, admin/manager — все) | любой |
| `GET` | `/orders/active` | Активные заказы (не оплаченные / не отменённые) | любой |
| `GET` | `/orders/{id}` | Данные заказа | любой |
| `POST` | `/orders/` | Создать заказ | waiter, manager, admin |
| `PATCH` | `/orders/{id}/status` | Изменить статус заказа (машина состояний) | любой |
| `POST` | `/orders/{id}/close` | Закрыть заказ (оплата) | waiter, manager, admin |
| `DELETE` | `/orders/{id}` | Отменить заказ | любой |

**Машина состояний заказа:**

```
pending ──────┬──► confirmed ──► preparing ──► ready ──► served ──► paid
              │         │
              ▼         ▼
          cancelled  cancelled
```

**Пример: создание заказа**

```http
POST /api/v1/orders/
Authorization: Bearer <token>
Content-Type: application/json

{
  "table_id": 3,
  "items": [
    {"menu_item_id": 7, "quantity": 2},
    {"menu_item_id": 17, "quantity": 3}
  ],
  "notes": "Стейк medium rare"
}
```

```json
{
  "id": 42,
  "table_id": 3,
  "waiter_id": 5,
  "status": "pending",
  "total_amount": "4240.00",
  "notes": "Стейк medium rare",
  "table_number": 3,
  "waiter_name": "Иван Петров",
  "items": [
    {
      "id": 1,
      "menu_item_id": 7,
      "quantity": 2,
      "unit_price": "1850.00",
      "status": "pending",
      "menu_item_name": "Стейк рибай 300г"
    },
    {
      "id": 2,
      "menu_item_id": 17,
      "quantity": 3,
      "unit_price": "180.00",
      "status": "pending",
      "menu_item_name": "Американо"
    }
  ],
  "created_at": "2026-05-13T10:30:00"
}
```

### Кухня (`/api/v1/kitchen`)

| Метод | Путь | Описание | Роль |
|---|---|---|---|
| `GET` | `/kitchen/queue` | Очередь блюд (pending + preparing), по времени | chef, manager, admin |
| `PATCH` | `/kitchen/items/{id}/preparing` | Пометить блюдо «готовится» | chef, admin |
| `PATCH` | `/kitchen/items/{id}/ready` | Пометить блюдо «готово» | chef, admin |
| `GET` | `/kitchen/stats` | Статистика кухни (счётчики + среднее время готовки) | chef, manager, admin |

### Персонал (`/api/v1/staff`)

| Метод | Путь | Описание | Роль |
|---|---|---|---|
| `GET` | `/staff/` | Список активных сотрудников | admin, manager |
| `GET` | `/staff/stats` | Статистика официантов (заказы, выручка) | admin, manager |
| `GET` | `/staff/{id}` | Данные сотрудника | admin, manager |
| `PATCH` | `/staff/{id}/deactivate` | Деактивировать аккаунт | admin, manager |

---

## 🧪 Запуск тестов

```bash
# Все тесты
pytest

# С отчётом о покрытии (текст + HTML)
pytest --cov=app --cov-report=term-missing --cov-report=html
# HTML-отчёт открывается в браузере: htmlcov/index.html

# Один модуль
pytest tests/test_auth.py -v

# По ключевому слову
pytest -k "order" -v
```

**Конфигурация тестовой среды:** тесты используют SQLite in-memory (никакой PostgreSQL не нужен). Переменные `DATABASE_URL` и `SECRET_KEY` задаются автоматически в `tests/conftest.py`.

**Текущее покрытие:** 95% (66 тестов, 847 statements). Отчёт: [`docs/COVERAGE_REPORT.txt`](docs/COVERAGE_REPORT.txt).

---

## 📁 Структура проекта

```
restaurant_management/
│
├── app/                            # Исходный код приложения
│   ├── api/v1/                     # FastAPI роутеры (HTTP-слой)
│   │   ├── auth.py                 # Регистрация, логин, /me
│   │   ├── tables.py               # CRUD столов
│   │   ├── menu.py                 # CRUD меню
│   │   ├── orders.py               # Управление заказами
│   │   ├── kitchen.py              # Кухонная очередь
│   │   └── staff.py                # Управление персоналом
│   ├── core/
│   │   ├── config.py               # Настройки через pydantic-settings
│   │   ├── security.py             # JWT, bcrypt
│   │   └── dependencies.py         # FastAPI Depends: get_db, get_current_user, require_role
│   ├── models/                     # SQLAlchemy 2.0 ORM-модели
│   │   ├── base.py                 # DeclarativeBase + TimestampMixin
│   │   ├── user.py                 # User (сотрудники)
│   │   ├── table.py                # Table (столы)
│   │   ├── menu_item.py            # MenuItem (блюда)
│   │   ├── order.py                # Order (заказы)
│   │   └── order_item.py           # OrderItem (позиции заказа)
│   ├── repositories/               # Слой доступа к данным (async CRUD)
│   │   ├── base_repository.py      # Generic BaseRepository[ModelType]
│   │   ├── user_repository.py
│   │   ├── table_repository.py
│   │   ├── menu_repository.py
│   │   └── order_repository.py
│   ├── schemas/                    # Pydantic v2 схемы запросов и ответов
│   │   ├── auth.py
│   │   ├── table.py
│   │   ├── menu_item.py
│   │   ├── order.py
│   │   └── staff.py
│   ├── services/                   # Бизнес-логика
│   │   ├── auth_service.py         # Регистрация, аутентификация
│   │   ├── table_service.py        # Создание, статус столов
│   │   ├── menu_service.py         # CRUD меню, поиск
│   │   ├── order_service.py        # Машина состояний заказов
│   │   ├── kitchen_service.py      # Кухонная очередь, статистика
│   │   ├── billing_service.py      # Расчёт счёта (рефакторинг)
│   │   └── bad_billing.py          # Учебный пример плохого кода (Задание 2)
│   └── main.py                     # FastAPI app, lifespan, middleware
│
├── alembic/                        # Миграции базы данных
│   ├── env.py                      # Async-конфигурация Alembic
│   ├── script.py.mako              # Шаблон миграции
│   └── versions/                   # Файлы миграций
│
├── tests/                          # Pytest тесты (66 тестов, 95% покрытие)
│   ├── conftest.py                 # Фикстуры: engine, session, client, users, data
│   ├── test_auth.py                # 11 тестов аутентификации
│   ├── test_tables.py              # 12 тестов столов
│   ├── test_orders.py              # 14 тестов заказов
│   ├── test_kitchen.py             # 10 тестов кухни
│   └── test_menu.py                # 19 тестов меню и персонала
│
├── scripts/
│   └── seed_db.py                  # Заполнение БД тестовыми данными
│
├── docs/
│   ├── CODE_REVIEW_REPORT.md       # Отчёт ревью bad_billing.py
│   └── COVERAGE_REPORT.txt         # Отчёт покрытия тестами
│
├── .github/workflows/
│   ├── ci.yml                      # CI: lint, test, security, docker build
│   └── ai_review.yml               # AI code review через Gemini API
│
├── Dockerfile                      # Multi-stage сборка (builder + runtime, non-root user)
├── docker-compose.yml              # PostgreSQL 16 + app
├── alembic.ini                     # Конфигурация Alembic
├── pyproject.toml                  # Зависимости, ruff, mypy, pytest, coverage
└── .env.example                    # Шаблон переменных окружения
```

---

## 🎓 Лабораторные задания

### Задание 1 — Реализация приложения

Полная реализация REST API «Система управления рестораном»:

- **ORM-модели** (`app/models/`) — 5 моделей с `Mapped[]`, `TimestampMixin`, связями через `relationship(lazy="selectin")`
- **Repository pattern** (`app/repositories/`) — generic `BaseRepository[T]` + специализированные репозитории
- **Service layer** (`app/services/`) — бизнес-логика изолирована от HTTP; машина состояний заказов
- **Pydantic v2 схемы** (`app/schemas/`) — `@computed_field` для денормализованных полей из relationships
- **API роутеры** (`app/api/v1/`) — ролевой доступ через `require_role()`, DI-инъекция сессии
- **Миграции** (`alembic/`) — async Alembic с ENUM-типами PostgreSQL

### Задание 2 — Code Review

Анализ намеренно плохого кода (`app/services/bad_billing.py`) и создание рефакторенной версии:

- **Отчёт:** [`docs/CODE_REVIEW_REPORT.md`](docs/CODE_REVIEW_REPORT.md) — 10 проблем (3 Critical, 2 High, 3 Medium, 2 Low)
- **Исправленный код:** [`app/services/billing_service.py`](app/services/billing_service.py) — `Decimal`-арифметика, именованные константы, `dataclass(frozen=True)`, полностью async, ORM без SQL-инъекций

### Задание 4 — CI/CD

Автоматизация через GitHub Actions (`.github/workflows/`):

- **`ci.yml`** — 4 независимых job: lint (ruff + mypy), test (pytest + Codecov), security (bandit), docker-build
- **`ai_review.yml`** — AI code review через Gemini API при каждом PR (см. ниже)

### Задание 7 — Тесты

Pytest-suite с покрытием 95% (847 statements):

- **66 тестов** в 5 модулях, все атомарные и независимые
- **Изоляция:** каждый тест получает свежую in-memory SQLite БД (function-scope `async_engine`)
- **Фикстуры:** `conftest.py` — engine, session, client, factory `make_user()`, `get_auth_headers()`, data fixtures
- **Инструменты:** `pytest-asyncio` (asyncio_mode=auto), `httpx.AsyncClient` + `ASGITransport`, `Faker`

---

## ⚙️ CI/CD

### ci.yml — Continuous Integration

Запускается при каждом push в `main`/`master`/`develop` и при PR:

| Job | Что проверяет |
|-----|--------------|
| **Lint & Type Check** | `ruff check app/ tests/` — стиль и импорты; `mypy app/` — статическая типизация |
| **Tests & Coverage** | `pytest --cov=app --cov-fail-under=70` + отправка в Codecov |
| **Security Scan** | `bandit -r app/ -ll` — поиск уязвимостей HIGH и MEDIUM |
| **Docker Build** | `docker build -t restaurant-app:test .` — проверка сборки образа |

### ai_review.yml — AI Code Review

При создании или обновлении Pull Request:

1. Собирает `git diff` между веткой PR и базовой веткой
2. Отправляет diff в **Google Gemini API** (`gemini-1.5-flash`, до 6000 символов, бесплатный tier)
3. Публикует ответ-ревью прямо в комментарии Pull Request

**Пример структуры комментария:**
```
## 🤖 AI Code Review (Gemini)

### 🐛 Возможные баги
### 🔒 Безопасность
### ✅ Хорошие практики
### 📋 Итог
---
*Автоматическое ревью от Google Gemini 1.5 Flash. Результаты носят рекомендательный характер.*
```

**Настройка секрета `GEMINI_API_KEY`:**

1. Зайди на [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (бесплатно, без карты)
2. Нажми **"Create API Key"**
3. В репозитории на GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `GEMINI_API_KEY`
   - Value: твой ключ
4. Сохрани — все последующие PR будут автоматически проходить AI-ревью

<!-- test AI review -->
<!-- test AI review -->
<!-- test Gemini review -->
