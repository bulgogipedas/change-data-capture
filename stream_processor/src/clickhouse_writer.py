from __future__ import annotations

from decimal import Decimal
from typing import Any

import clickhouse_connect

from .config import Settings
from .debezium import CdcEvent, json_dumps


CURRENT_COLUMNS = {
    "customers": ["customer_id", "email", "full_name", "status", "created_at", "updated_at", "deleted_at", "is_deleted", "version"],
    "sellers": ["seller_id", "seller_name", "status", "created_at", "updated_at", "deleted_at", "is_deleted", "version"],
    "products": ["product_id", "seller_id", "sku", "product_name", "category", "price", "status", "created_at", "updated_at", "deleted_at", "is_deleted", "version"],
    "inventory": ["inventory_id", "product_id", "quantity_on_hand", "reserved_quantity", "low_stock_threshold", "updated_at", "is_deleted", "version"],
    "orders": ["order_id", "customer_id", "seller_id", "order_status", "order_total", "currency", "created_at", "updated_at", "cancelled_at", "deleted_at", "is_deleted", "version"],
    "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "line_total", "created_at", "is_deleted", "version"],
    "stock_movements": ["movement_id", "product_id", "movement_type", "quantity_delta", "reason", "order_id", "created_at", "is_deleted", "version"],
    "payments": ["payment_id", "order_id", "payment_status", "payment_method", "amount", "paid_at", "failed_at", "created_at", "updated_at", "is_deleted", "version"],
    "shipments": ["shipment_id", "order_id", "shipment_status", "carrier", "tracking_number", "shipped_at", "delivered_at", "updated_at", "is_deleted", "version"],
    "refunds": ["refund_id", "payment_id", "order_id", "refund_status", "refund_amount", "reason", "refunded_at", "created_at", "updated_at", "is_deleted", "version"],
}


DECIMAL_FIELDS = {"price", "order_total", "unit_price", "line_total", "amount", "refund_amount"}


def _clean_value(column: str, value: Any) -> Any:
    if value is None:
        return None
    if column in DECIMAL_FIELDS:
        return Decimal(str(value))
    return value


class ClickHouseWriter:
    def __init__(self, settings: Settings):
        self.client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database,
        )

    def write_event(self, event: CdcEvent) -> None:
        self.write_raw_event(event)
        self.write_current_state(event)
        self.write_log(
            level="INFO",
            component="stream_processor",
            event_type="cdc_event_processed",
            source_table=event.table,
            message=f"{event.op} {event.table} {event.primary_key}",
            context={"topic": event.topic, "partition": event.partition, "offset": event.offset},
        )

    def write_raw_event(self, event: CdcEvent) -> None:
        row = [
            event.table,
            event.primary_key,
            event.op,
            event.event_ts_ms,
            event.source_ts_ms,
            event.topic,
            event.partition,
            event.offset,
            event.snapshot,
            event.version,
            event.is_deleted,
            json_dumps(event.before),
            json_dumps(event.after),
            json_dumps(event.raw),
        ]
        self.client.insert(
            "raw_cdc_events",
            [row],
            column_names=[
                "source_table",
                "primary_key",
                "op",
                "event_ts_ms",
                "source_ts_ms",
                "kafka_topic",
                "kafka_partition",
                "kafka_offset",
                "snapshot",
                "version",
                "is_deleted",
                "before_json",
                "after_json",
                "raw_json",
            ],
        )

    def write_current_state(self, event: CdcEvent) -> None:
        columns = CURRENT_COLUMNS.get(event.table)
        if not columns:
            raise ValueError(f"No current-state mapping for {event.table}")

        row = event.row
        values = []
        for column in columns:
            if column == "is_deleted":
                values.append(event.is_deleted)
            elif column == "version":
                values.append(event.version)
            else:
                values.append(_clean_value(column, row.get(column)))

        self.client.insert(f"cur_{event.table}", [values], column_names=columns)

    def write_log(self, level: str, component: str, event_type: str, source_table: str, message: str, context: dict[str, Any]) -> None:
        self.client.insert(
            "pipeline_event_log",
            [[level, component, event_type, source_table, message, json_dumps(context)]],
            column_names=["level", "component", "event_type", "source_table", "message", "context_json"],
        )
