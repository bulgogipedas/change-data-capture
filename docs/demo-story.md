# Demo Story: Flash Sale Incident

## Opening Script

"ShopPulse is running a flash sale. Orders are arriving quickly, inventory is changing every few seconds, payment status is moving from pending to successful, and some customers are cancelling or requesting refunds. In a batch ETL world, business teams would wait for the next hourly refresh. In this demo, we use CDC so each database change becomes an event and the dashboard reflects the incident much faster."

## Business Problem

During a high-traffic sale, stale data causes operational mistakes:

- Customers may see products as available when stock has already dropped.
- Sellers may see outdated order counts and revenue.
- Finance may not see payment/refund changes in time.
- Operations may miss low-stock alerts.
- Analytics may run repeated full-refresh jobs just to pick up a handful of changed rows.

## What Batch ETL Would Miss

An hourly batch pipeline would likely miss the most important part of the incident:

- The order spike between refresh windows.
- Inventory dropping below the low-stock threshold.
- Payment status changes from `PENDING` to `SUCCESS`.
- Refunds and cancellations that should reduce revenue.
- Deletes or deactivations that downstream systems need to respect.

The result is a dashboard that looks polished but tells the wrong story.

## What CDC Solves

The CDC pipeline captures inserts, updates, and deletes from PostgreSQL WAL with Debezium. Redpanda stores those events as Kafka-compatible topics. The Python processor reads the Debezium envelope, writes raw events and current-state rows into ClickHouse, and Streamlit queries the analytical marts.

The demo proves that operational changes can flow from source database to dashboard without a full table refresh.

## Presenter Flow

### 1. Set The Scene

Show the Streamlit Executive overview.

Say:
"This is the baseline state before the flash sale. The dashboard is reading ClickHouse, not PostgreSQL directly. ClickHouse is being updated by CDC events."

Show:

- GMV
- total orders
- cancelled orders
- refund amount
- active sellers

### 2. Show The Event Backbone

Open Redpanda Console at `http://localhost:8080`.

Show:

- `dbserver1.public.orders`
- `dbserver1.public.inventory`
- `dbserver1.public.payments`
- `dbserver1.public.refunds`
- `dbserver1.public.stock_movements`

Say:
"Each table has a CDC topic. Debezium publishes row-level changes here, and the processor consumes these topics."

### 3. Start The Flash Sale

Run:

```bash
uv run --project scripts python scripts/simulate_flash_sale.py
```

Explain:
"This script creates an order, order item, pending payment, stock movement, and inventory update in PostgreSQL. In a real system, this would be produced by the checkout service."

Show in the processor terminal:

- `Processed c orders`
- `Processed c order_items`
- `Processed c payments`
- `Processed u inventory`
- `Processed c stock_movements`

### 4. Show Inventory Falling

Open the Real-time inventory page.

Run:

```bash
uv run --project scripts python scripts/simulate_inventory_changes.py
```

Show:

- low-stock product count
- inventory by product
- stock movement timeline

Say:
"The operations team does not need to wait for the next hourly refresh to see stock risk."

### 5. Show Payment Status Updates

Run:

```bash
uv run --project scripts python scripts/simulate_payment_updates.py
```

Open the Payment monitoring page.

Show:

- pending payments
- successful payments
- recent payment transitions

Say:
"Payment state is not a static fact. It changes over time. CDC captures those updates."

### 6. Show Cancellation And Refund Impact

Run:

```bash
uv run --project scripts python scripts/simulate_refunds_and_cancellations.py
```

Show:

- refund amount on Executive overview
- seller performance revenue adjustment
- payment status changing to `REFUNDED`

Say:
"Revenue metrics must react to cancellations and refunds. Counting created orders as revenue would overstate the business."

### 7. Demonstrate Delete Handling

Run:

```bash
uv run --project scripts python scripts/simulate_delete_handling.py
```

Show ClickHouse raw events:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT source_table, op, count() FROM raw_cdc_events GROUP BY source_table, op ORDER BY source_table, op"
```

Say:
"Deletes are also data. Debezium emits delete events, and the serving layer can mark current-state records as deleted while retaining the raw audit trail."

### 8. Show Quality And Health

Run:

```bash
cd stream_processor
uv run python -m src.quality.run_checks
```

Open CDC pipeline health.

Show:

- raw CDC event counts
- latest event timestamps
- failed events
- DQ results

Say:
"Real-time is not enough. The pipeline also needs trust signals: freshness, failure counts, and data quality results."

## What To Show In ClickHouse

Raw CDC counts:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT source_table, count() FROM raw_cdc_events GROUP BY source_table ORDER BY source_table"
```

Executive mart:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT * FROM mart_executive_overview FORMAT PrettyCompact"
```

Inventory mart:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT seller_name, product_name, quantity_on_hand, low_stock_threshold, is_low_stock FROM mart_realtime_inventory ORDER BY is_low_stock DESC, quantity_on_hand ASC FORMAT PrettyCompact"
```

## Closing Explanation

"The important thing here is not the dashboard itself. The important thing is the data movement pattern. PostgreSQL remains the operational source. Debezium turns database changes into events. Redpanda makes those events durable and inspectable. The processor turns events into analytical state. ClickHouse serves fast queries. Streamlit gives the business a fresh view of what is happening."

"This MVP is intentionally local and simple, but it demonstrates the core architecture used in production CDC platforms."
