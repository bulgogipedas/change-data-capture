# Data Model

## Source Tables

The PostgreSQL source has ten transactional tables:

- `customers`
- `sellers`
- `products`
- `inventory`
- `stock_movements`
- `orders`
- `order_items`
- `payments`
- `shipments`
- `refunds`

Business-level deletes use `deleted_at` where relevant. Physical deletes are still supported and represented downstream as `is_deleted = 1`.

## ClickHouse Layers

- `raw_cdc_events`: parsed Debezium metadata plus raw JSON payloads.
- `cur_*`: latest row images with `ReplacingMergeTree(version)`.
- Fact views: orders, payments, refunds, and inventory movements.
- Dimension views: products and sellers.
- Mart views: executive overview, inventory, seller performance, and payment monitoring.
- Health tables: pipeline logs, data quality results, and offset snapshots.

## Versioning

The processor derives a `version` from Debezium source timestamp and Kafka offset. Current-state tables insert immutable row versions and ClickHouse resolves the newest record per key.
