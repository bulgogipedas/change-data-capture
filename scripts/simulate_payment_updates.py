from __future__ import annotations

from demo_db import connect


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT payment_id, order_id
                FROM payments
                WHERE payment_status = 'PENDING'
                ORDER BY created_at
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                print("No pending payments to update.")
                return
            payment_id, order_id = row
            cur.execute(
                """
                UPDATE payments
                SET payment_status = 'SUCCESS', paid_at = now()
                WHERE payment_id = %s
                """,
                (payment_id,),
            )
            cur.execute("UPDATE orders SET order_status = 'PAID' WHERE order_id = %s", (order_id,))
            print(f"Marked payment {payment_id} and order {order_id} as successful.")


if __name__ == "__main__":
    main()
