from __future__ import annotations

from demo_db import connect


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shipments (order_id, shipment_status, carrier, tracking_number)
                SELECT order_id, 'PENDING', 'DEMO', 'DELETE-ME'
                FROM orders
                ORDER BY created_at DESC
                LIMIT 1
                RETURNING shipment_id
                """
            )
            shipment_id = cur.fetchone()[0]
            cur.execute("DELETE FROM shipments WHERE shipment_id = %s", (shipment_id,))
            print(f"Inserted and physically deleted shipment {shipment_id} to demonstrate Debezium delete handling.")


if __name__ == "__main__":
    main()
