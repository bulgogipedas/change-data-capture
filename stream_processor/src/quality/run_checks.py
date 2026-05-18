from __future__ import annotations

from dataclasses import dataclass

import clickhouse_connect

from ..config import Settings


@dataclass(frozen=True)
class QualityCheck:
    name: str
    level: str
    severity: str
    sql: str
    details: str


CHECKS = [
    QualityCheck("orders_non_negative_total", "warehouse", "CRITICAL", "SELECT count() FROM cur_orders FINAL WHERE order_total < 0", "Orders must not have negative totals."),
    QualityCheck("inventory_non_negative", "warehouse", "CRITICAL", "SELECT count() FROM cur_inventory FINAL WHERE quantity_on_hand < 0", "Inventory quantity must not be negative."),
    QualityCheck("successful_payment_has_paid_at", "warehouse", "CRITICAL", "SELECT count() FROM cur_payments FINAL WHERE payment_status = 'SUCCESS' AND paid_at IS NULL", "Successful payments require paid_at."),
    QualityCheck("stock_movement_non_zero", "warehouse", "CRITICAL", "SELECT count() FROM cur_stock_movements FINAL WHERE quantity_delta = 0", "Stock movements cannot have zero quantity."),
    QualityCheck(
        "cancelled_orders_excluded_from_revenue",
        "mart",
        "CRITICAL",
        "SELECT count() FROM (SELECT * FROM cur_orders FINAL) AS o INNER JOIN (SELECT * FROM cur_payments FINAL) AS p ON o.order_id = p.order_id WHERE o.order_status = 'CANCELLED' AND p.payment_status = 'SUCCESS'",
        "Cancelled paid orders should be visible for adjustment review.",
    ),
]


def main() -> None:
    settings = Settings()
    client = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )

    rows = []
    for check in CHECKS:
        failed_count = int(client.query(check.sql).result_rows[0][0])
        rows.append([
            check.name,
            check.level,
            check.severity,
            "PASS" if failed_count == 0 else "FAIL",
            failed_count,
            check.details,
        ])

    client.insert(
        "data_quality_results",
        rows,
        column_names=["check_name", "check_level", "severity", "status", "failed_count", "details"],
    )
    for row in rows:
        print(f"{row[3]} {row[0]} failed_count={row[4]}")


if __name__ == "__main__":
    main()
