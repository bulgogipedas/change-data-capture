from __future__ import annotations

from demo_db import connect


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT product_id, quantity_on_hand, low_stock_threshold
                FROM inventory
                ORDER BY quantity_on_hand DESC
                LIMIT 1
                """
            )
            product_id, quantity, threshold = cur.fetchone()
            new_quantity = max(threshold - 1, 0)
            delta = new_quantity - quantity
            cur.execute(
                "UPDATE inventory SET quantity_on_hand = %s WHERE product_id = %s",
                (new_quantity, product_id),
            )
            cur.execute(
                """
                INSERT INTO stock_movements (product_id, movement_type, quantity_delta, reason)
                VALUES (%s, 'ADJUSTMENT', %s, 'Operations low-stock simulation')
                """,
                (product_id, delta),
            )
            if new_quantity == 0:
                cur.execute("UPDATE products SET status = 'OUT_OF_STOCK' WHERE product_id = %s", (product_id,))
            print(f"Adjusted product {product_id} inventory from {quantity} to {new_quantity}.")


if __name__ == "__main__":
    main()
