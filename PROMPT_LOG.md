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
