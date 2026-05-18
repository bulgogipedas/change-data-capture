# CDC Design

## Debezium Operations

| Operation | `op` | Handling |
|---|---|---|
| Snapshot read | `r` | Treat as baseline upsert |
| Insert | `c` | Use `after` as the latest row image |
| Update | `u` | Use `after` as the latest row image |
| Delete | `d` | Use `before` and set `is_deleted = 1` |
| Tombstone | null payload | Ignore for analytics |

## Idempotency

Raw events preserve topic, partition, and offset. Current-state tables are immutable append tables with a version column, so replays can rebuild state by truncating downstream tables and consuming from the beginning.

## Failure Handling

The MVP records processing failures in `pipeline_event_log`. A production extension can publish failed records to `cdc.dead_letter` with the original payload and exception context.

## Replay

1. Stop the processor.
2. Truncate ClickHouse raw/current/health tables.
3. Reset the consumer group offset to earliest.
4. Restart the processor.
5. Run data quality checks.
