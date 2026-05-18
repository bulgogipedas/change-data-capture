from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


PRIMARY_KEYS = {
    "customers": "customer_id",
    "sellers": "seller_id",
    "products": "product_id",
    "inventory": "inventory_id",
    "stock_movements": "movement_id",
    "orders": "order_id",
    "order_items": "order_item_id",
    "payments": "payment_id",
    "shipments": "shipment_id",
    "refunds": "refund_id",
}


@dataclass(frozen=True)
class CdcEvent:
    table: str
    primary_key: str
    op: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    event_ts_ms: int
    source_ts_ms: int
    topic: str
    partition: int
    offset: int
    snapshot: str
    version: int
    is_deleted: int
    raw: dict[str, Any]

    @property
    def row(self) -> dict[str, Any]:
        payload = self.before if self.op == "d" else self.after
        return payload or {}


def parse_message(value: bytes | None, topic: str, partition: int, offset: int) -> CdcEvent | None:
    if value is None:
        return None

    raw = json.loads(value.decode("utf-8"))
    payload = raw.get("payload", raw)

    op = payload.get("op")
    if not op:
        return None

    source = payload.get("source") or {}
    table = source.get("table") or topic.split(".")[-1]
    before = payload.get("before")
    after = payload.get("after")
    row = before if op == "d" else after
    if not row:
        return None

    pk_field = PRIMARY_KEYS.get(table)
    if not pk_field or pk_field not in row:
        raise ValueError(f"Unable to resolve primary key for {table}")

    event_ts_ms = int(payload.get("ts_ms") or 0)
    source_ts_ms = int(source.get("ts_ms") or event_ts_ms)
    offset_component = max(offset, 0) % 100000
    version = source_ts_ms * 100000 + offset_component

    return CdcEvent(
        table=table,
        primary_key=str(row[pk_field]),
        op=op,
        before=before,
        after=after,
        event_ts_ms=event_ts_ms,
        source_ts_ms=source_ts_ms,
        topic=topic,
        partition=partition,
        offset=offset,
        snapshot=str(source.get("snapshot") or "false"),
        version=version,
        is_deleted=1 if op == "d" else 0,
        raw=payload,
    )


def json_dumps(value: Any) -> str:
    if value is None:
        return ""
    return json.dumps(value, sort_keys=True, default=str)
