# Repository Structure

This repository is intentionally scoped to the implemented MVP. Advanced placeholders such as dbt, orchestration, monitoring, schema registry, and cloud deployment are documented as future improvements instead of appearing as empty folders.

```text
.
├── .github/workflows/
│   └── validate.yml
├── clickhouse/init/
│   ├── 001_raw_tables.sql
│   ├── 002_current_tables.sql
│   ├── 003_fact_dim_marts.sql
│   └── 004_observability_tables.sql
├── dashboard/
│   ├── app.py
│   ├── pyproject.toml
│   └── uv.lock
├── debezium/connectors/
│   └── postgres-source.json
├── docs/
│   ├── architecture.md
│   ├── cdc-design.md
│   ├── data-model.md
│   ├── demo-story.md
│   ├── interview-notes.md
│   ├── repository-structure.md
│   ├── screenshots.md
│   └── assets/screenshots/
├── postgres/init/
│   ├── 001_schema.sql
│   ├── 002_seed.sql
│   └── 003_publication.sql
├── scripts/
│   ├── check_demo_health.sh
│   ├── create_topics.sh
│   ├── register_connector.sh
│   ├── run_demo_sequence.sh
│   ├── simulate_flash_sale.py
│   ├── simulate_payment_updates.py
│   ├── simulate_inventory_changes.py
│   ├── simulate_refunds_and_cancellations.py
│   ├── simulate_delete_handling.py
│   └── validate_project.sh
├── stream_processor/
│   ├── src/
│   ├── pyproject.toml
│   └── uv.lock
├── compose.yml
├── Makefile
└── README.md
```

## Public Docs

| File | Purpose |
|---|---|
| `README.md` | Main portfolio landing page and run instructions |
| `docs/architecture.md` | Component responsibilities and data flow |
| `docs/cdc-design.md` | Debezium envelope and CDC handling strategy |
| `docs/data-model.md` | PostgreSQL and ClickHouse model overview |
| `docs/demo-story.md` | Presenter narrative for the flash sale incident |
| `docs/interview-notes.md` | Interview talking points and Q&A |
| `docs/screenshots.md` | Screenshot capture checklist |

## Local-Only Notes

Operational runbooks can be kept locally if needed, but runbook-style files under `docs/` are intentionally ignored by git.

```text
docs/*runbook.md
docs/private/
```

This keeps GitHub focused on the project story, architecture, and runnable MVP.
