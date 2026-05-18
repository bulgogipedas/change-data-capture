from __future__ import annotations

import random
from decimal import Decimal

from demo_db import connect


FLASH_PRODUCT_ID = "00000000-0000-0000-0000-000000000301"


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, seller_id, price FROM products WHERE product_id = %s", (FLASH_PRODUCT_ID,))
            product_id, seller_id, price = cur.fetchone()
            cur.execute("SELECT customer_id FROM customers ORDER BY random() LIMIT 1")
            customer_id = cur.fetchone()[0]
            quantity = random.choice([1, 1, 2])
            total = Decimal(price) * quantity

            cur.execute(
                """
                INSERT INTO orders (customer_id, seller_id, order_status, order_total)
                VALUES (%s, %s, 'CREATED', %s)
                RETURNING order_id
                """,
                (customer_id, seller_id, total),
            )
            order_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (order_id, product_id, quantity, price, total),
            )
            cur.execute(
                """
                UPDATE inventory
                SET quantity_on_hand = greatest(quantity_on_hand - %s, 0)
                WHERE product_id = %s
                """,
                (quantity, product_id),
            )
            cur.execute(
                """
                INSERT INTO stock_movements (product_id, movement_type, quantity_delta, reason, order_id)
                VALUES (%s, 'SALE', %s, 'Flash sale checkout', %s)
                """,
                (product_id, -quantity, order_id),
            )
            cur.execute(
                """
                INSERT INTO payments (order_id, payment_status, payment_method, amount)
                VALUES (%s, 'PENDING', 'CARD', %s)
                """,
                (order_id, total),
            )
            print(f"Created flash sale order {order_id} for {quantity} unit(s), total={total}")


if __name__ == "__main__":
    main()
