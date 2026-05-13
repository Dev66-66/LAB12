# Code Review Report — `app/services/bad_billing.py`

**Reviewer:** Senior Python Developer / Security Engineer  
**Date:** 2026-05-13  
**File:** `app/services/bad_billing.py`  
**Severity scale:** 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low

---

## Executive Summary

The `calculate_bill` function contains **10 distinct defects** spanning four categories:
security vulnerabilities, logic errors, performance issues, and style violations.
Two of them (SQL injection and hardcoded credentials) are immediately exploitable in
production. The function must not be merged in its current form.

---

### Проблема 1: SQL-инъекция (множественная)
**Тип:** Уязвимость безопасности 🔴 Critical  
**Что сгенерировал ИИ:**
```python
cur.execute(f"SELECT * FROM orders WHERE id = {order_id}")
cur.execute(f"SELECT * FROM order_items WHERE order_id = {order_id} AND status != 'cancelled'")
cur.execute(f"UPDATE orders SET total_amount = {res}, status = 'confirmed' WHERE id = {order_id}")
cur.execute(
    f"INSERT INTO billing_log (order_id, amount, discount_code, created_at) "
    f"VALUES ({order_id}, {res}, '{discount_code}', NOW())"
)
cur.execute(f"SELECT username, email FROM users WHERE id = {data[2]}")
```
**В чём проблема:**  
Значения `order_id` и `discount_code` подставляются напрямую в SQL через f-строки.
Злоумышленник может передать `order_id = "1; DROP TABLE orders; --"` и уничтожить
таблицы, либо через `discount_code` получить произвольные данные из БД
(UNION-based injection). Уязвимость присутствует в 5 из 5 запросов.

**Как исправить:**
```python
# Используем параметризованные запросы (ORM или psycopg2 placeholders):
cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))

# Или через SQLAlchemy ORM:
order = await db.get(Order, order_id)
```

---

### Проблема 2: Захардкоженные секреты
**Тип:** Уязвимость безопасности 🔴 Critical  
**Что сгенерировал ИИ:**
```python
DB_PASSWORD = "postgres123"
SECRET_KEY = "my-super-secret-billing-key-2024"
DB_HOST = "localhost"
```
**В чём проблема:**  
Пароль базы данных и секретный ключ хранятся в исходном коде.
При попадании файла в публичный репозиторий (или в руки сотрудника с read-доступом)
компрометируются немедленно. Git-история сохраняет их навсегда — даже после удаления
строк. `SECRET_KEY` также передаётся во внешние HTTP-запросы в открытом виде.

**Как исправить:**
```python
# settings.py (pydantic-settings читает из .env / переменных среды)
from app.core.config import settings

# Использование:
db_url = settings.DATABASE_URL      # из .env, не из кода
secret  = settings.SECRET_KEY       # никогда не в исходнике
```

---

### Проблема 3: Синхронный блокирующий I/O внутри async-функции
**Тип:** Проблема производительности 🟠 High  
**Что сгенерировал ИИ:**
```python
async def calculate_bill(order_id, discount_code):
    conn = psycopg2.connect(...)   # синхронный драйвер
    ...
    data2 = requests.get(...)      # блокирующий HTTP
    time.sleep(2)                  # блокирует event loop
    y = requests.post(...)         # блокирующий HTTP
    time.sleep(1)                  # блокирует event loop
    requests.post(...)             # блокирующий HTTP
```
**В чём проблема:**  
`psycopg2`, `requests` и `time.sleep` блокируют поток выполнения.
В FastAPI / asyncio-приложении это означает, что **весь event loop замирает** на время
каждого вызова: никакие другие запросы не обрабатываются. При 10 RPS суммарный блок —
30+ секунд в секунду, что делает сервис практически недоступным.

**Как исправить:**
```python
import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

async def calculate_bill(db: AsyncSession, order_id: int, ...) -> BillResult:
    # async ORM вместо psycopg2
    order = await db.get(Order, order_id)

    # async HTTP вместо requests
    async with httpx.AsyncClient() as client:
        resp = await client.get(promo_url)

    # asyncio.sleep вместо time.sleep (не блокирует loop)
    await asyncio.sleep(0)   # или убрать sleep вовсе
```

---

### Проблема 4: Полное отсутствие обработки ошибок и проверок None
**Тип:** Отсутствие обработки ошибок 🟠 High  
**Что сгенерировал ИИ:**
```python
data = cur.fetchone()          # может вернуть None
# ... никакой проверки ...
cur.execute(f"... WHERE id = {data[2]}")  # TypeError: 'NoneType' is not subscriptable

user = cur.fetchone()          # тоже может быть None
return {"user": user[0]}       # падение без сообщения об ошибке
```
**В чём проблема:**  
Если заказ не найден, `data` равен `None`. Доступ `data[2]` 65 строк спустя
бросает необработанный `TypeError`. Пользователь получает 500 Internal Server Error
без какого-либо контекста. Аналогично для `user`. Соединение с БД при этом не
закрывается (нет `finally`), что вызывает утечку соединений.

**Как исправить:**
```python
order = await db.get(Order, order_id)
if order is None:
    raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

# Соединение закрывается автоматически через context manager:
async with AsyncSessionLocal() as db:
    ...  # при любом исключении сессия закрывается
```

---

### Проблема 5: Дублирование логики расчёта скидки
**Тип:** Логическая ошибка 🟡 Medium  
**Что сгенерировал ИИ:**
```python
if discount_code == "SAVE10":
    d = res * 0.1
    res = res - d
    if res > 1000:
        res = res - res * 0.05   # повторяется дословно
    if res > 500:
        res = res - 50           # повторяется дословно
elif discount_code == "SAVE15":
    d = res * 0.15
    res = res - d
    if res > 1000:
        res = res - res * 0.05   # дублирование
    if res > 500:
        res = res - 50           # дублирование
elif discount_code == "STAFF":
    d = res * 0.1                # идентично SAVE10 — баг или намерение?
    res = res - d
    if res > 1000:
        res = res - res * 0.05   # дублирование
    if res > 500:
        res = res - 50           # дублирование
```
**В чём проблема:**  
Блок `if res > 1000 / if res > 500` продублирован трижды. Изменение бизнес-правила
(например, порог `500 → 600`) потребует правки в трёх местах — вероятна ошибка.
Кроме того, `STAFF` и `SAVE10` дают одинаковую скидку 10%: это либо намеренно
(нет комментария), либо copy-paste баг. Применение двух порогов `>1000` и `>500`
одновременно означает, что при `res = 1100` сначала снимется 5%, потом ещё 50 — порядок
влияет на результат, но не задокументирован.

**Как исправить:**
```python
DISCOUNT_RATES: dict[str, Decimal] = {
    "SAVE10": Decimal("0.10"),
    "SAVE15": Decimal("0.15"),
    "STAFF":  Decimal("0.10"),
}

def _apply_discount(subtotal: Decimal, code: str) -> tuple[Decimal, Decimal]:
    rate = DISCOUNT_RATES.get(code, Decimal("0"))
    discount = (subtotal * rate).quantize(Decimal("0.01"))
    return subtotal - discount, discount

def _apply_loyalty_bonus(total: Decimal) -> Decimal:
    if total > Decimal("1000"):
        total -= (total * Decimal("0.05")).quantize(Decimal("0.01"))
    if total > Decimal("500"):
        total -= Decimal("50")
    return total
```

---

### Проблема 6: Магические числа и плавающая точка для денег
**Тип:** Логическая ошибка 🟡 Medium  
**Что сгенерировал ИИ:**
```python
d = res * 0.1      # float!
res = res - d
if res > 1000:
    res = res - res * 0.05
if res > 500:
    res = res - 50
z = res * 0.0      # мёртвый код, результат нигде не используется
```
**В чём проблема:**  
Денежные вычисления через `float` накапливают ошибки округления: `0.1 + 0.2 == 0.30000000000000004`.
При счёте в 999.99 результат непредсказуем. Числа `0.1`, `0.15`, `0.05`, `500`, `1000`, `50`
называются магическими — их смысл не понятен без контекста. Переменная `z = res * 0.0`
является мёртвым кодом (dead code) и никогда не используется.

**Как исправить:**
```python
from decimal import Decimal

HIGH_ORDER_THRESHOLD    = Decimal("1000")
MEDIUM_ORDER_THRESHOLD  = Decimal("500")
HIGH_ORDER_BONUS_RATE   = Decimal("0.05")
MEDIUM_ORDER_FLAT_BONUS = Decimal("50")

# Все расчёты через Decimal — точно до копейки:
discount = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
```

---

### Проблема 7: Утечка секрета через внешний HTTP-запрос
**Тип:** Уязвимость безопасности 🟠 High  
**Что сгенерировал ИИ:**
```python
data2 = requests.get(
    f"http://promo-service.internal/validate?code={discount_code}&key={SECRET_KEY}"
)
y = requests.post(
    "http://notifications.internal/send",
    json={"order": order_id, "total": res, "key": SECRET_KEY}
)
requests.post(
    "http://email-service.internal/send",
    json={"to": user[1], "subject": "Your bill", "amount": res, "key": SECRET_KEY}
)
```
**В чём проблема:**  
`SECRET_KEY` передаётся в URL-параметре (логируется proxy-серверами, попадает в
access.log) и в теле каждого запроса. Запросы идут по `http://` (не HTTPS), что
позволяет перехватить ключ в сети. После компрометации ключа атакующий может
подписывать произвольные billing-события.

**Как исправить:**
```python
# 1. Использовать HTTPS
# 2. Передавать ключ только в заголовке Authorization, не в URL и не в теле
async with httpx.AsyncClient() as client:
    await client.post(
        "https://notifications.internal/send",
        json={"order": order_id, "total": str(total)},
        headers={"Authorization": f"Bearer {settings.NOTIFICATION_API_KEY}"},
    )
```

---

### Проблема 8: Неинформативные имена переменных
**Тип:** Нарушение стиля 🟢 Low  
**Что сгенерировал ИИ:**
```python
for x in items:
    res = res + x[4] * x[3]
data2 = requests.get(...)
tmp = data2.json()
y = requests.post(...)
z = res * 0.0
```
**В чём проблема:**  
`x[4]` и `x[3]` — порядковые индексы колонок из `SELECT *`. При изменении схемы
(добавлении колонки) индексы сдвинутся без какой-либо ошибки, и расчёт будет
молча давать неверный результат. `res`, `d`, `tmp`, `y`, `z` не передают намерения:
через 2 недели ни один разработчик (включая автора) не поймёт код без повторного
разбора логики.

**Как исправить:**
```python
subtotal = Decimal("0")
for item in order_items:
    line_total = item.unit_price * item.quantity   # именованные атрибуты ORM
    subtotal += line_total

promo_response = await client.get(promo_url)
promo_data     = promo_response.json()
```

---

### Проблема 9: Отсутствие type hints и docstring
**Тип:** Нарушение стиля 🟢 Low  
**Что сгенерировал ИИ:**
```python
async def calculate_bill(order_id, discount_code):
    # тело без единой аннотации или docstring
```
**В чём проблема:**  
Без type hints IDE и mypy не могут обнаружить ошибки типов до запуска. Вызывающий
код не знает, что возвращает функция — `dict`, `Decimal`, ORM-объект? Отсутствие
docstring означает, что Swagger/OpenAPI документация будет пустой, а новый
разработчик должен читать всю реализацию, чтобы понять контракт функции.

**Как исправить:**
```python
async def calculate_bill(
    db: AsyncSession,
    order_id: int,
    discount_code: str | None = None,
) -> BillResult:
    """Calculate the final bill for an order and persist the result.

    Args:
        db: Active async database session.
        order_id: Primary key of the order to bill.
        discount_code: Optional promotional code.

    Returns:
        BillResult with total, discount, and order metadata.

    Raises:
        HTTPException 404: Order not found.
        HTTPException 400: Invalid or expired discount code.
    """
```

---

### Проблема 10: Функция нарушает Single Responsibility Principle
**Тип:** Нарушение стиля 🟡 Medium  
**Что сгенерировал ИИ:**
```python
async def calculate_bill(order_id, discount_code):
    # 1. Открывает соединение с БД
    # 2. Читает заказ
    # 3. Читает позиции заказа
    # 4. Вызывает внешний promo-сервис
    # 5. Применяет скидку (3 раза)
    # 6. Спит 2 секунды
    # 7. Отправляет уведомление
    # 8. Обновляет БД
    # 9. Пишет в billing_log
    # 10. Читает пользователя
    # 11. Спит 1 секунду
    # 12. Шлёт email
    # 13. Возвращает результат
```
**В чём проблема:**  
Одна функция выполняет 13 различных задач. Это делает её невозможной для
unit-тестирования (нужно мокировать БД + два HTTP-сервиса + email одновременно),
трудной для понимания и хрупкой при изменениях. Изменение логики уведомлений
затрагивает функцию расчёта — нарушение SRP.

**Как исправить:**  
Разбить на специализированные функции:
- `_calculate_subtotal(items)` — арифметика
- `_validate_discount(code)` — HTTP к promo-сервису
- `_apply_discount(subtotal, code)` — бизнес-логика скидок
- `_persist_bill(db, order, total)` — запись в БД
- `_send_notifications(order, user, total)` — уведомления

---

## Итоговая таблица

| # | Проблема | Тип | Severity |
|---|---|---|---|
| 1 | SQL-инъекция (5 запросов) | Уязвимость безопасности | 🔴 Critical |
| 2 | Захардкоженные секреты | Уязвимость безопасности | 🔴 Critical |
| 3 | Синхронный I/O в async | Производительность | 🟠 High |
| 4 | Нет обработки ошибок / None | Отсутствие обработки ошибок | 🟠 High |
| 5 | Дублирование расчёта скидки | Логическая ошибка | 🟡 Medium |
| 6 | Магические числа + float для денег | Логическая ошибка | 🟡 Medium |
| 7 | Секрет утекает через HTTP | Уязвимость безопасности | 🟠 High |
| 8 | Неинформативные имена и `SELECT *` | Нарушение стиля | 🟢 Low |
| 9 | Нет type hints и docstring | Нарушение стиля | 🟢 Low |
| 10 | Нарушение SRP (13 задач в 1 функции) | Нарушение стиля | 🟡 Medium |

**Вердикт: REJECTED.** Файл не должен попадать в основную ветку.  
Требуется полный рефакторинг — см. `app/services/billing_service.py`.
