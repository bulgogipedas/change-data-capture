# Demo Story

The demo follows ShopPulse during Flash Sale Friday.

1. Operations starts with a baseline dashboard: current GMV, seller revenue, stock, payments, and pipeline freshness.
2. A flash sale creates new orders against `TrailLite Everyday Backpack`.
3. PostgreSQL records orders, order items, pending payments, inventory updates, and stock movement audit entries.
4. Debezium captures the changes from WAL and writes them to Redpanda topics.
5. The processor writes raw events and current-state rows into ClickHouse.
6. The dashboard shows order count and GMV moving within seconds.
7. Inventory crosses the low-stock threshold.
8. A pending payment becomes successful.
9. A paid order is cancelled and refunded.
10. The dashboard removes cancelled orders from revenue and shows refund amount.
11. The batch comparison reminds the audience that an hourly ETL would still be stale.

Key message: CDC turns operational database changes into a reliable event stream that makes dashboards and downstream systems fresher, cheaper, and easier to audit.
