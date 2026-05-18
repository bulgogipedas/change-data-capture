CREATE TABLE IF NOT EXISTS cdc_analytics.cur_customers
(
    customer_id String,
    email String,
    full_name String,
    status LowCardinality(String),
    created_at Nullable(DateTime64(6, 'UTC')),
    updated_at Nullable(DateTime64(6, 'UTC')),
    deleted_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY customer_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_sellers
(
    seller_id String,
    seller_name String,
    status LowCardinality(String),
    created_at Nullable(DateTime64(6, 'UTC')),
    updated_at Nullable(DateTime64(6, 'UTC')),
    deleted_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY seller_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_products
(
    product_id String,
    seller_id String,
    sku String,
    product_name String,
    category String,
    price Decimal(12, 2),
    status LowCardinality(String),
    created_at Nullable(DateTime64(6, 'UTC')),
    updated_at Nullable(DateTime64(6, 'UTC')),
    deleted_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY product_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_inventory
(
    inventory_id String,
    product_id String,
    quantity_on_hand Int32,
    reserved_quantity Int32,
    low_stock_threshold Int32,
    updated_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY inventory_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_orders
(
    order_id String,
    customer_id String,
    seller_id String,
    order_status LowCardinality(String),
    order_total Decimal(12, 2),
    currency FixedString(3),
    created_at Nullable(DateTime64(6, 'UTC')),
    updated_at Nullable(DateTime64(6, 'UTC')),
    cancelled_at Nullable(DateTime64(6, 'UTC')),
    deleted_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY order_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_order_items
(
    order_item_id String,
    order_id String,
    product_id String,
    quantity Int32,
    unit_price Decimal(12, 2),
    line_total Decimal(12, 2),
    created_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY order_item_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_stock_movements
(
    movement_id String,
    product_id String,
    movement_type LowCardinality(String),
    quantity_delta Int32,
    reason String,
    order_id Nullable(String),
    created_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY movement_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_payments
(
    payment_id String,
    order_id String,
    payment_status LowCardinality(String),
    payment_method LowCardinality(String),
    amount Decimal(12, 2),
    paid_at Nullable(DateTime64(6, 'UTC')),
    failed_at Nullable(DateTime64(6, 'UTC')),
    created_at Nullable(DateTime64(6, 'UTC')),
    updated_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY payment_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_shipments
(
    shipment_id String,
    order_id String,
    shipment_status LowCardinality(String),
    carrier Nullable(String),
    tracking_number Nullable(String),
    shipped_at Nullable(DateTime64(6, 'UTC')),
    delivered_at Nullable(DateTime64(6, 'UTC')),
    updated_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY shipment_id;

CREATE TABLE IF NOT EXISTS cdc_analytics.cur_refunds
(
    refund_id String,
    payment_id String,
    order_id String,
    refund_status LowCardinality(String),
    refund_amount Decimal(12, 2),
    reason String,
    refunded_at Nullable(DateTime64(6, 'UTC')),
    created_at Nullable(DateTime64(6, 'UTC')),
    updated_at Nullable(DateTime64(6, 'UTC')),
    is_deleted UInt8,
    version UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(version)
ORDER BY refund_id;
