CREATE DATABASE IF NOT EXISTS cdc_analytics;

CREATE TABLE IF NOT EXISTS cdc_analytics.raw_cdc_events
(
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3),
    source_table LowCardinality(String),
    primary_key String,
    op LowCardinality(String),
    event_ts_ms UInt64,
    source_ts_ms UInt64,
    kafka_topic String,
    kafka_partition Int32,
    kafka_offset Int64,
    snapshot String,
    version UInt64,
    is_deleted UInt8,
    before_json String,
    after_json String,
    raw_json String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ingested_at)
ORDER BY (source_table, primary_key, version, kafka_partition, kafka_offset);
