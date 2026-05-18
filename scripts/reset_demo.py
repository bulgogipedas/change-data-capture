from __future__ import annotations

from demo_db import connect


def main() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM refunds;
                DELETE FROM shipments WHERE shipment_id <> '00000000-0000-0000-0000-000000000901';
                DELETE FROM payments WHERE payment_id NOT IN ('00000000-0000-0000-0000-000000000801', '00000000-0000-0000-0000-000000000802');
                DELETE FROM stock_movements WHERE movement_id NOT IN ('00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000702');
                DELETE FROM order_items WHERE order_item_id NOT IN ('00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000602');
                DELETE FROM orders WHERE order_id NOT IN ('00000000-0000-0000-0000-000000000501', '00000000-0000-0000-0000-000000000502');
                UPDATE inventory SET quantity_on_hand = CASE product_id
                    WHEN '00000000-0000-0000-0000-000000000301' THEN 40
                    WHEN '00000000-0000-0000-0000-000000000302' THEN 22
                    WHEN '00000000-0000-0000-0000-000000000303' THEN 55
                    WHEN '00000000-0000-0000-0000-000000000304' THEN 14
                    ELSE quantity_on_hand
                END;
                UPDATE products SET status = 'ACTIVE', deleted_at = NULL;
                UPDATE orders SET order_status = 'PAID', cancelled_at = NULL WHERE order_id = '00000000-0000-0000-0000-000000000501';
                UPDATE orders SET order_status = 'CREATED', cancelled_at = NULL WHERE order_id = '00000000-0000-0000-0000-000000000502';
                UPDATE payments SET payment_status = 'SUCCESS', paid_at = now(), failed_at = NULL WHERE payment_id = '00000000-0000-0000-0000-000000000801';
                UPDATE payments SET payment_status = 'PENDING', paid_at = NULL, failed_at = NULL WHERE payment_id = '00000000-0000-0000-0000-000000000802';
                """
            )
            print("Reset source demo data. Rebuild ClickHouse by replaying CDC topics if needed.")


if __name__ == "__main__":
    main()
