CREATE TABLE IF NOT EXISTS cdc_analytics.pipeline_event_log
(
    logged_at DateTime64(3, 'UTC') DEFAULT now64(3),
    level LowCardinality(String),
    component LowCardinality(String),
    event_type LowCardinality(String),
    source_table String,
    message String,
    context_json String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(logged_at)
ORDER BY (logged_at, component, event_type);

CREATE TABLE IF NOT EXISTS cdc_analytics.data_quality_results
(
    checked_at DateTime64(3, 'UTC') DEFAULT now64(3),
    check_name String,
    check_level LowCardinality(String),
    severity LowCardinality(String),
    status LowCardinality(String),
    failed_count UInt64,
    details String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(checked_at)
ORDER BY (checked_at, check_level, check_name);

CREATE TABLE IF NOT EXISTS cdc_analytics.consumer_offsets_snapshot
(
    captured_at DateTime64(3, 'UTC') DEFAULT now64(3),
    consumer_group String,
    kafka_topic String,
    kafka_partition Int32,
    current_offset Int64,
    high_watermark Int64,
    lag Int64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(captured_at)
ORDER BY (captured_at, consumer_group, kafka_topic, kafka_partition);
