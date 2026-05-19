# CDC Check Walkthrough

Use this walkthrough to prove the platform is really doing Change Data Capture, not just showing seeded dashboard data.

## Goal

Demonstrate that a business change written to PostgreSQL appears as:

1. A row-level Debezium event in Redpanda.
2. A processed record in ClickHouse raw/current tables.
3. An updated metric or table in Streamlit.

## Happy Path

Run these commands from the repository root unless noted otherwise.

### 1. Start the Runtime

```bash
podman machine start
podman compose -f compose.yml up -d
podman compose -f compose.yml ps
```

Expected result:

- PostgreSQL is healthy.
- Redpanda is healthy.
- Debezium is healthy.
- ClickHouse is healthy.
- Redpanda Console is available at `http://localhost:8080`.

If Podman reports a socket or connection error, restart the machine:

```bash
podman machine stop
podman machine start
podman info
```

### 2. Register CDC

```bash
./scripts/register_connector.sh
./scripts/create_topics.sh
curl -sS http://localhost:8083/connectors/shop-postgres-source/status
```

Expected result:

- Connector state is `RUNNING`.
- Task state is `RUNNING`.

### 3. Start the Processor

In a dedicated terminal:

```bash
cd stream_processor
uv run python -m src.main
```

Keep this terminal open. It should print consumed table names and CDC operations as events arrive.

### 4. Open the Dashboard

In another terminal:

```bash
cd dashboard
uv run streamlit run app.py --server.port 8501
```

Open `http://localhost:8501`.

Expected result:

- The page renders without exceptions.
- If ClickHouse is down, the dashboard shows a clear startup hint instead of a traceback.

### 5. Run a Business Event

From the repository root:

```bash
uv run --project scripts python scripts/simulate_flash_sale.py
```

This creates:

- A new order.
- A new order item.
- A pending payment.
- An inventory decrement.
- A stock movement audit row.

### 6. Check Redpanda Topics

```bash
podman exec cdc-redpanda rpk topic list
podman exec cdc-redpanda rpk topic consume dbserver1.public.orders --num 1
```

What to look for:

- Topic names like `dbserver1.public.orders`, `dbserver1.public.inventory`, and `dbserver1.public.payments`.
- Debezium envelope fields:
  - `before`
  - `after`
  - `op`
  - `source`
  - `ts_ms`

For the flash sale insert, `op` should be `c`.

### 7. Check ClickHouse Raw CDC Events

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT source_table, op, count() FROM raw_cdc_events GROUP BY source_table, op ORDER BY source_table, op FORMAT PrettyCompact"
```

Expected result:

- `orders` has create events.
- `order_items` has create events.
- `payments` has create events.
- `inventory` has update events.
- `stock_movements` has create events.

### 8. Check ClickHouse Current State

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT order_id, order_status, order_total, updated_at FROM fact_orders ORDER BY updated_at DESC LIMIT 5 FORMAT PrettyCompact"
```

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT product_name, quantity_on_hand, low_stock_threshold, is_low_stock FROM mart_realtime_inventory ORDER BY is_low_stock DESC, quantity_on_hand ASC FORMAT PrettyCompact"
```

Expected result:

- The latest order appears in `fact_orders`.
- The affected product quantity decreases.
- Low-stock flags update when quantity reaches the threshold.

### 9. Run More CDC Cases

```bash
uv run --project scripts python scripts/simulate_payment_updates.py
uv run --project scripts python scripts/simulate_inventory_changes.py
uv run --project scripts python scripts/simulate_refunds_and_cancellations.py
uv run --project scripts python scripts/simulate_delete_handling.py
```

What each script proves:

| Script | CDC behavior | Business meaning |
|---|---|---|
| `simulate_payment_updates.py` | `UPDATE` on payments/orders | Payment lifecycle moves from pending to paid |
| `simulate_inventory_changes.py` | `UPDATE` on inventory plus movement insert | Operations sees stock risk quickly |
| `simulate_refunds_and_cancellations.py` | `UPDATE` order/payment plus refund insert | Cancelled/refunded orders stop inflating revenue |
| `simulate_delete_handling.py` | Physical `DELETE` on shipment | Downstream marks deleted rows correctly |

### 10. Check Data Quality

```bash
cd stream_processor
uv run python -m src.quality.run_checks
```

Expected result:

- All checks return `PASS`.
- `data_quality_results` is populated in ClickHouse.

### 11. Refresh Streamlit

Refresh `http://localhost:8501` and click through:

- Executive overview
- Real-time inventory
- Seller operations
- Payment monitoring
- CDC pipeline health

What to explain:

- PostgreSQL is the source of truth.
- Debezium captured changes from WAL.
- Redpanda carried the events.
- Python normalized Debezium envelopes.
- ClickHouse served current analytical state.
- Streamlit showed the updated business view.

## Quick Demo Sequence

After services and the processor are running:

```bash
./scripts/run_demo_sequence.sh
cd stream_processor
uv run python -m src.quality.run_checks
```

Then refresh Streamlit and open Redpanda Console.

## Interview Talking Point

The important proof is not just that the dashboard changes. The proof is that the same source write can be traced through every layer:

```text
PostgreSQL row change
  -> Debezium envelope in Redpanda
  -> raw_cdc_events in ClickHouse
  -> current/fact/mart view
  -> Streamlit dashboard metric
```
