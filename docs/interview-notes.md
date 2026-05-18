# Interview Notes

## Short Project Pitch

"I built a real-time CDC platform for an e-commerce flash sale scenario. PostgreSQL is the operational source, Debezium captures row-level changes from WAL, Redpanda stores the CDC topics, a Python processor normalizes events, ClickHouse serves analytical marts, and Streamlit shows real-time order, payment, refund, inventory, seller, and pipeline health dashboards."

## Why CDC Instead Of Batch ETL?

Batch ETL is good for periodic reporting, but it is weak for operational freshness. During a flash sale, orders, payments, refunds, and inventory can change many times between hourly refreshes. CDC captures the actual row-level changes from the database log and moves only what changed.

Strong answer:
"CDC reduces freshness lag and avoids full-refresh work. It also preserves intermediate state transitions, such as payment moving from pending to successful to refunded, which can be lost or blurred in snapshot-style batch pipelines."

## What Does Debezium Do?

Debezium reads PostgreSQL's write-ahead log through logical replication. It emits structured events containing:

- `op`: operation type, such as snapshot read, insert, update, or delete.
- `before`: previous row image when available.
- `after`: new row image when available.
- `source`: metadata such as table, database, and source timestamp.

In this project, Debezium creates topics such as `dbserver1.public.orders` and `dbserver1.public.inventory`.

## What Does Redpanda/Kafka Do?

Redpanda is the durable event backbone. It decouples capture from processing:

- Debezium can publish events without knowing ClickHouse details.
- The processor can restart and resume from offsets.
- Topics can be inspected in Redpanda Console during the demo.
- Future consumers could reuse the same CDC stream.

## Why ClickHouse?

ClickHouse is built for analytical reads and high-volume inserts. That makes it a good fit for serving dashboards over CDC-derived tables:

- Raw event tables preserve audit history.
- Current-state tables keep latest row versions.
- Views expose facts, dimensions, and marts.
- Aggregates such as GMV, refunds, low-stock counts, and payment status counts are fast.

## How Are INSERT, UPDATE, And DELETE Handled?

| Source operation | Debezium op | Downstream handling |
|---|---|---|
| Snapshot read | `r` | Treat as baseline current-state row |
| Insert | `c` | Insert raw event and latest current-state row |
| Update | `u` | Insert new version of current-state row |
| Delete | `d` | Use `before` payload and mark `is_deleted = 1` |
| Tombstone | null payload | Ignore for analytics in MVP |

The processor stores topic, partition, and offset metadata for auditability.

## How Is Data Quality Checked?

The MVP uses Python-driven SQL checks against ClickHouse. Checks include:

- Orders must not have negative totals.
- Inventory quantity must not be negative.
- Successful payments must have `paid_at`.
- Stock movement quantity cannot be zero.
- Cancelled paid orders must remain visible for revenue adjustment review.

Results are written to `data_quality_results` and shown on the pipeline health dashboard.

## How Can Freshness Be Measured?

Freshness can be measured at multiple points:

- Debezium source timestamp from CDC events.
- Processor ingestion timestamp in ClickHouse.
- Latest event timestamp by Kafka topic.
- Dashboard query freshness from max `ingested_at`.
- Consumer lag from Redpanda consumer group metadata.

The MVP exposes event counts and latest timestamps. A production version would export these as metrics.

## MVP Trade-Offs

| Decision | Why it is acceptable for MVP | Production improvement |
|---|---|---|
| Python processor | Simple, readable, easy to demo | Flink/Kafka Streams for stronger state and scaling |
| Manual replay | Clear for local demo | Orchestrated replay/backfill jobs |
| Custom DQ checks | Easy to understand | Soda, Great Expectations, or dbt tests |
| No schema registry | Keeps stack small | Schema Registry and compatibility rules |
| Manual dashboard refresh | Fine for presentation | Live refresh, scheduled cache, or websocket updates |
| Local credentials | Good for demo | Secret manager and proper access controls |

## Possible Questions And Strong Answers

### Why not query PostgreSQL directly from the dashboard?

PostgreSQL is optimized for transactional workloads, not analytical dashboard queries. ClickHouse lets us serve aggregates without putting read pressure on the operational database.

### How do you avoid duplicate processing?

The processor stores Kafka metadata and writes immutable row versions. Current-state tables use versioned replacement logic. A production system would add stronger exactly-once guarantees and replay controls.

### What happens if the processor is down?

Events remain in Redpanda. When the processor restarts, it resumes from its consumer group offset. If a rebuild is needed, we can reset offsets and replay into ClickHouse.

### Why use Redpanda instead of Kafka?

Redpanda is Kafka-compatible but simpler for local development because it avoids ZooKeeper and has an efficient single-binary architecture. The same topic/consumer model applies.

### What is the role of raw CDC tables?

Raw tables are the audit and debugging layer. If a mart looks wrong, we can inspect the exact event payload, operation type, source timestamp, topic, partition, and offset.

### How would you productionize this?

I would add managed infrastructure, schema registry, a DLQ, replay tooling, Flink for stateful processing, dbt for modeling/tests, orchestration for backfills, metrics in Prometheus/Grafana, CI/CD, and access control.

### What is the most important engineering lesson?

Real-time pipelines need both freshness and trust. It is not enough to stream events quickly; the platform also needs replayability, data quality checks, observability, and clear semantics for updates and deletes.
