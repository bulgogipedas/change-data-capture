from __future__ import annotations

from demo_db import connect


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*), coalesce(sum(order_total), 0) FROM orders")
            orders, total = cur.fetchone()
            print("Simulated batch snapshot would only update on the next scheduled refresh.")
            print(f"Current source orders={orders}, source order_total={total}")


if __name__ == "__main__":
    main()
