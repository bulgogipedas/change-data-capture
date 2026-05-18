CREATE VIEW IF NOT EXISTS cdc_analytics.dim_sellers AS
SELECT seller_id, seller_name, status, created_at, updated_at
FROM cdc_analytics.cur_sellers FINAL
WHERE is_deleted = 0 AND deleted_at IS NULL;

CREATE VIEW IF NOT EXISTS cdc_analytics.dim_products AS
SELECT product_id, seller_id, sku, product_name, category, price, status, created_at, updated_at
FROM cdc_analytics.cur_products FINAL
WHERE is_deleted = 0 AND deleted_at IS NULL;

CREATE VIEW IF NOT EXISTS cdc_analytics.fact_orders AS
SELECT order_id, customer_id, seller_id, order_status, order_total, currency, created_at, updated_at, cancelled_at
FROM cdc_analytics.cur_orders FINAL
WHERE is_deleted = 0 AND deleted_at IS NULL;

CREATE VIEW IF NOT EXISTS cdc_analytics.fact_payments AS
SELECT payment_id, order_id, payment_status, payment_method, amount, paid_at, failed_at, created_at, updated_at
FROM cdc_analytics.cur_payments FINAL
WHERE is_deleted = 0;

CREATE VIEW IF NOT EXISTS cdc_analytics.fact_inventory_movements AS
SELECT movement_id, product_id, movement_type, quantity_delta, reason, order_id, created_at
FROM cdc_analytics.cur_stock_movements FINAL
WHERE is_deleted = 0;

CREATE VIEW IF NOT EXISTS cdc_analytics.fact_refunds AS
SELECT refund_id, payment_id, order_id, refund_status, refund_amount, reason, refunded_at, created_at, updated_at
FROM cdc_analytics.cur_refunds FINAL
WHERE is_deleted = 0;

CREATE VIEW IF NOT EXISTS cdc_analytics.mart_realtime_inventory AS
SELECT
    i.product_id,
    p.seller_id,
    s.seller_name,
    p.sku,
    p.product_name,
    p.category,
    i.quantity_on_hand,
    i.reserved_quantity,
    i.low_stock_threshold,
    i.quantity_on_hand <= i.low_stock_threshold AS is_low_stock,
    i.quantity_on_hand = 0 AS is_out_of_stock,
    i.updated_at,
    i.ingested_at
FROM (SELECT * FROM cdc_analytics.cur_inventory FINAL) AS i
LEFT JOIN (SELECT * FROM cdc_analytics.cur_products FINAL) AS p ON i.product_id = p.product_id
LEFT JOIN (SELECT * FROM cdc_analytics.cur_sellers FINAL) AS s ON p.seller_id = s.seller_id
WHERE i.is_deleted = 0 AND p.is_deleted = 0 AND p.deleted_at IS NULL;

CREATE VIEW IF NOT EXISTS cdc_analytics.mart_seller_performance AS
SELECT
    s.seller_id,
    s.seller_name,
    countIf(o.order_status != 'CANCELLED') AS total_orders,
    countIf(o.order_status = 'CANCELLED') AS cancelled_orders,
    sumIf(p.amount, p.payment_status = 'SUCCESS' AND o.order_status != 'CANCELLED') AS gross_revenue,
    coalesce(sumIf(r.refund_amount, r.refund_status = 'COMPLETED'), 0) AS refund_amount,
    gross_revenue - refund_amount AS net_revenue
FROM (SELECT * FROM cdc_analytics.cur_sellers FINAL) AS s
LEFT JOIN (SELECT * FROM cdc_analytics.cur_orders FINAL) AS o ON s.seller_id = o.seller_id AND o.is_deleted = 0
LEFT JOIN (SELECT * FROM cdc_analytics.cur_payments FINAL) AS p ON o.order_id = p.order_id AND p.is_deleted = 0
LEFT JOIN (SELECT * FROM cdc_analytics.cur_refunds FINAL) AS r ON o.order_id = r.order_id AND r.is_deleted = 0
WHERE s.is_deleted = 0
GROUP BY s.seller_id, s.seller_name;

CREATE VIEW IF NOT EXISTS cdc_analytics.mart_payment_monitoring AS
SELECT
    payment_status,
    count() AS payment_count,
    sum(amount) AS payment_amount,
    max(updated_at) AS latest_status_update
FROM cdc_analytics.cur_payments FINAL
WHERE is_deleted = 0
GROUP BY payment_status;

CREATE VIEW IF NOT EXISTS cdc_analytics.mart_executive_overview AS
SELECT
    (SELECT countDistinct(order_id) FROM cdc_analytics.cur_orders FINAL WHERE is_deleted = 0) AS total_orders,
    (SELECT countDistinct(order_id) FROM cdc_analytics.cur_orders FINAL WHERE is_deleted = 0 AND order_status = 'CANCELLED') AS cancelled_orders,
    (SELECT countDistinct(payment_id) FROM cdc_analytics.cur_payments FINAL WHERE is_deleted = 0 AND payment_status = 'SUCCESS') AS successful_payments,
    (
        SELECT coalesce(sum(p.amount), 0)
        FROM (SELECT * FROM cdc_analytics.cur_payments FINAL WHERE is_deleted = 0 AND payment_status = 'SUCCESS') AS p
        INNER JOIN (SELECT * FROM cdc_analytics.cur_orders FINAL WHERE is_deleted = 0 AND order_status != 'CANCELLED') AS o
            ON p.order_id = o.order_id
    ) AS gmv,
    (SELECT coalesce(sum(refund_amount), 0) FROM cdc_analytics.cur_refunds FINAL WHERE is_deleted = 0 AND refund_status = 'COMPLETED') AS refund_amount,
    (SELECT countDistinct(seller_id) FROM cdc_analytics.cur_sellers FINAL WHERE is_deleted = 0 AND deleted_at IS NULL AND status = 'ACTIVE') AS active_sellers;
