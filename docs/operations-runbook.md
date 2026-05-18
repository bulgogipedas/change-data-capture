# Operations Runbook

For a clean presenter flow, use `docs/demo-runbook.md`. This file is the shorter operator reference.

## Happy Path

```bash
cp .env.example .env
podman compose up -d postgres redpanda clickhouse debezium redpanda-console
podman compose ps
./scripts/register_connector.sh
./scripts/create_topics.sh
podman exec cdc-redpanda rpk topic list
```

Processor terminal:

```bash
cd stream_processor && uv run python -m src.main
```

Dashboard terminal:

```bash
cd dashboard && uv run streamlit run app.py
```

Use Docker instead of Podman by replacing `podman compose` with `docker compose`.

## Service Health

```bash
podman compose ps
podman exec cdc-postgres pg_isready -U cdc_user -d shopdb
podman exec cdc-redpanda rpk cluster health
curl -fsS http://localhost:8083/connectors
curl -fsS http://localhost:8123/ping
podman exec cdc-redpanda rpk topic list
curl -sS "http://localhost:8123/?database=cdc_analytics" --data-binary "SELECT count() FROM raw_cdc_events"
```

The expected CDC topics are named like `dbserver1.public.orders`, `dbserver1.public.inventory`, and `dbserver1.public.payments`.

## Demo Commands

```bash
uv run --project scripts python scripts/simulate_flash_sale.py
uv run --project scripts python scripts/simulate_payment_updates.py
uv run --project scripts python scripts/simulate_inventory_changes.py
uv run --project scripts python scripts/simulate_refunds_and_cancellations.py
uv run --project scripts python scripts/simulate_delete_handling.py
cd stream_processor && uv run python -m src.quality.run_checks
```

## Inspect

- Redpanda Console: `http://localhost:8080`
- Streamlit: `http://localhost:8501`
- Debezium Connect: `http://localhost:8083/connectors`
- ClickHouse: `http://localhost:8123/play`

## Reset

Run:

```bash
uv run --project scripts python scripts/reset_demo.py
```

For a full rebuild, recreate containers and volumes, register the connector again, and restart the processor.

## Podman Machine / Socket Troubleshooting

If `podman compose` fails before reading the compose file, verify the VM first:

```bash
podman machine inspect
podman machine start
podman info
podman system connection list
```

If `podman machine start` says success but `inspect` still reports `State: "stopped"`, restart the VM:

```bash
podman machine stop
podman machine start
podman info
```

If the socket still fails with `connection refused` or `operation not permitted`, recreate the local VM:

```bash
podman machine stop
podman machine rm
podman machine init --cpus 4 --memory 4096 --disk-size 100
podman machine start
podman info
```

Docker fallback:

```bash
docker compose -f compose.yml config
docker compose -f compose.yml up -d
docker compose -f compose.yml ps
```

## Related Docs

- `docs/demo-story.md`: presenter script and business incident narrative.
- `docs/demo-runbook.md`: clean reset/replay flow.
- `docs/screenshots.md`: screenshot capture checklist.
- `docs/interview-notes.md`: technical talking points and expected questions.
