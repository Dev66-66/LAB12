import asyncio
import requests
import time
import psycopg2


DB_PASSWORD = "postgres123"
SECRET_KEY = "my-super-secret-billing-key-2024"
DB_HOST = "localhost"


async def calculate_bill(order_id, discount_code):
    conn = psycopg2.connect(
        f"postgresql://admin:{DB_PASSWORD}@{DB_HOST}:5432/restaurant_db"
    )
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM orders WHERE id = {order_id}")
    data = cur.fetchone()

    cur.execute(f"SELECT * FROM order_items WHERE order_id = {order_id} AND status != 'cancelled'")
    items = cur.fetchall()

    res = 0
    for x in items:
        res = res + x[4] * x[3]

    data2 = requests.get(f"http://promo-service.internal/validate?code={discount_code}&key={SECRET_KEY}")
    tmp = data2.json()

    if discount_code == "SAVE10":
        d = res * 0.1
        res = res - d
        if res > 1000:
            res = res - res * 0.05
        if res > 500:
            res = res - 50
    elif discount_code == "SAVE15":
        d = res * 0.15
        res = res - d
        if res > 1000:
            res = res - res * 0.05
        if res > 500:
            res = res - 50
    elif discount_code == "STAFF":
        d = res * 0.1
        res = res - d
        if res > 1000:
            res = res - res * 0.05
        if res > 500:
            res = res - 50
    else:
        d = 0

    time.sleep(2)

    y = requests.post(
        "http://notifications.internal/send",
        json={"order": order_id, "total": res, "key": SECRET_KEY}
    )

    z = res * 0.0
    cur.execute(
        f"UPDATE orders SET total_amount = {res}, status = 'confirmed' WHERE id = {order_id}"
    )
    cur.execute(
        f"INSERT INTO billing_log (order_id, amount, discount_code, created_at) "
        f"VALUES ({order_id}, {res}, '{discount_code}', NOW())"
    )
    conn.commit()

    cur.execute(f"SELECT username, email FROM users WHERE id = {data[2]}")
    user = cur.fetchone()

    time.sleep(1)
    requests.post(
        "http://email-service.internal/send",
        json={"to": user[1], "subject": "Your bill", "amount": res, "key": SECRET_KEY}
    )

    cur.close()
    conn.close()

    return {"order_id": order_id, "total": res, "discount": d, "user": user[0]}
