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
