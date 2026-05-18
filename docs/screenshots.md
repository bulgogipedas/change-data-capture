# Screenshots Guide

Use this guide to capture portfolio screenshots after running the full demo flow.

Recommended folder:

```text
docs/assets/screenshots/
```

Create it if needed:

```bash
mkdir -p docs/assets/screenshots
```

## Screenshot Checklist

| Screenshot | Where to capture | Suggested filename | What it proves |
|---|---|---|---|
| Executive overview | Streamlit `http://localhost:8501` | `01-executive-overview.png` | Business users see GMV, orders, refunds, cancellations, and active sellers |
| Real-time inventory | Streamlit Real-time inventory page | `02-realtime-inventory.png` | Inventory has changed and low-stock products are visible |
| Seller operations | Streamlit Seller operations page | `03-seller-operations.png` | Seller revenue/order views update from CDC-derived marts |
| Payment monitoring | Streamlit Payment monitoring page | `04-payment-monitoring.png` | Payment/refund statuses are visible as operational state |
| CDC pipeline health | Streamlit CDC pipeline health page | `05-pipeline-health.png` | Raw event counts, freshness, failure count, and DQ results are visible |
| Redpanda topics | Redpanda Console `http://localhost:8080` | `06-redpanda-topics.png` | CDC topics exist for source tables |
| Topic messages | Redpanda Console topic detail | `07-redpanda-order-events.png` | Debezium events are present in the streaming layer |
| Debezium status | Browser or terminal output from connector status | `08-debezium-status.png` | Connector and task are `RUNNING` |
| ClickHouse raw counts | Terminal or ClickHouse playground | `09-clickhouse-cdc-counts.png` | Events landed in ClickHouse by table |
| Data quality output | Terminal or Streamlit health page | `10-data-quality-output.png` | Quality checks pass after the demo |

## Recommended Capture Order

1. Start all services.
2. Register the connector and create topics.
3. Start the processor.
4. Start Streamlit.
5. Run all demo scripts.
6. Run data quality checks.
7. Capture Streamlit pages.
8. Capture Redpanda Console.
9. Capture ClickHouse query output.

## Commands Worth Capturing

Connector status:

```bash
curl -sS http://localhost:8083/connectors/shop-postgres-source/status
```

ClickHouse CDC counts:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT source_table, count() FROM raw_cdc_events GROUP BY source_table ORDER BY source_table"
```

Operation counts:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT source_table, op, count() FROM raw_cdc_events GROUP BY source_table, op ORDER BY source_table, op"
```

Executive mart:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT * FROM mart_executive_overview FORMAT PrettyCompact"
```

Quality summary:

```bash
curl -sS "http://localhost:8123/?database=cdc_analytics" \
  --data-binary "SELECT status, count(), sum(failed_count) FROM data_quality_results GROUP BY status FORMAT PrettyCompact"
```

## README Placement

After screenshots are captured, add a compact section to the README:

```markdown
## Screenshots

![Executive overview](docs/assets/screenshots/01-executive-overview.png)
![Real-time inventory](docs/assets/screenshots/02-realtime-inventory.png)
![Pipeline health](docs/assets/screenshots/05-pipeline-health.png)
```

Keep the README focused: use three to five screenshots there, and keep the full screenshot set in `docs/assets/screenshots/`.
