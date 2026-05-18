from __future__ import annotations

from demo_db import connect


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id, p.payment_id, p.amount
                FROM orders o
                JOIN payments p ON o.order_id = p.order_id
                WHERE o.order_status = 'PAID' AND p.payment_status = 'SUCCESS'
                ORDER BY o.updated_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                print("No paid successful order found for cancellation/refund.")
                return
            order_id, payment_id, amount = row
            cur.execute(
                "UPDATE orders SET order_status = 'CANCELLED', cancelled_at = now() WHERE order_id = %s",
                (order_id,),
            )
            cur.execute("UPDATE payments SET payment_status = 'REFUNDED' WHERE payment_id = %s", (payment_id,))
            cur.execute(
                """
                INSERT INTO refunds (payment_id, order_id, refund_status, refund_amount, reason, refunded_at)
                VALUES (%s, %s, 'COMPLETED', %s, 'Customer cancelled during flash sale', now())
                """,
                (payment_id, order_id, amount),
            )
            print(f"Cancelled order {order_id} and completed refund for {amount}.")


if __name__ == "__main__":
    main()
