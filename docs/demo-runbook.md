# Demo Runbook

This runbook is for a clean, repeatable local demo of the Real-Time Order & Inventory CDC Platform.

## Safety Note

The destructive reset commands remove local containers and volumes for this project. They delete local PostgreSQL, Redpanda, and ClickHouse demo state. Use them only when you want a clean replay.

## Clean Reset

From the repo root:

```bash
podman compose -f compose.yml down
```

Destructive full reset:

```bash
podman compose -f compose.yml down -v
```

If individual containers are stuck:

```bash
podman rm -f cdc-postgres cdc-redpanda cdc-clickhouse cdc-debezium cdc-redpanda-console
```

## Fresh Start

```bash
cp .env.example .env
podman machine start
podman info
podman compose -f compose.yml config
podman compose -f compose.yml up -d
podman compose -f compose.yml ps
```

## Health Checks

```bash
podman exec cdc-postgres pg_isready -U cdc_user -d shopdb
podman exec cdc-redpanda rpk cluster health
curl -fsS http://localhost:8083/connectors
curl -fsS http://localhost:8123/ping
```

## Register CDC Connector

```bash
./scripts/register_connector.sh
./scripts/create_topics.sh
curl -sS http://localhost:8083/connectors/shop-postgres-source/status
podman exec cdc-redpanda rpk topic list
```

Expected connector state:

```text
connector.state = RUNNING
tasks[0].state = RUNNING
```

## Start Processor

Open a dedicated terminal:

```bash
cd "/Users/tamagoasin/Documents/01 Projects/cdc/stream_processor"
uv run python -m src.main
```

Expected output includes snapshot events:

```text
Processed r orders ...
Processed r inventory ...
Processed r payments ...
```

## Start Dashboard

Open another terminal:

```bash
cd "/Users/tamagoasin/Documents/01 Projects/cdc/dashboard"
uv run streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Run Demo Scripts

From the repo root:

```bash
uv run --project scripts python scripts/simulate_flash_sale.py
uv run --project scripts python scripts/simulate_payment_updates.py
uv run --project scripts python scripts/simulate_inventory_changes.py
uv run --project scripts python scripts/simulate_refunds_and_cancellations.py
uv run --project scripts python scripts/simulate_delete_handling.py
```

## Run Data Quality Checks

```bash
cd stream_processor
uv run python -m src.quality.run_checks
```

Expected output:

```text
PASS orders_non_negative_total failed_count=0
PASS inventory_non_negative failed_count=0
PASS successful_payment_has_paid_at failed_count=0
PASS stock_movement_non_zero failed_count=0
PASS cancelled_orders_excluded_from_revenue failed_count=0
```

## Verify ClickHouse

Raw CDC event counts:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT source_table, count() FROM raw_cdc_events GROUP BY source_table ORDER BY source_table"
```

Operations summary:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT source_table, op, count() FROM raw_cdc_events GROUP BY source_table, op ORDER BY source_table, op"
```

Executive mart:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT * FROM mart_executive_overview FORMAT PrettyCompact"
```

Data quality summary:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT status, count(), sum(failed_count) FROM data_quality_results GROUP BY status FORMAT PrettyCompact"
```

## Capture Screenshots

Recommended folder:

```bash
mkdir -p docs/assets/screenshots
```

Capture:

- `01-executive-overview.png`
- `02-realtime-inventory.png`
- `03-payment-monitoring.png`
- `04-pipeline-health.png`
- `05-redpanda-topics.png`
- `06-debezium-status.png`
- `07-clickhouse-cdc-counts.png`
- `08-data-quality-output.png`

See `docs/screenshots.md` for the full screenshot checklist.

## Stop Demo

Stop local Python terminals with `Ctrl+C`.

Stop containers:

```bash
podman compose -f compose.yml down
```

Keep volumes if you want to preserve demo state. Use `down -v` only for a clean replay.
