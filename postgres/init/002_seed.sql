INSERT INTO customers (customer_id, email, full_name) VALUES
('00000000-0000-0000-0000-000000000101', 'maya.chen@example.com', 'Maya Chen'),
('00000000-0000-0000-0000-000000000102', 'nora.patel@example.com', 'Nora Patel'),
('00000000-0000-0000-0000-000000000103', 'leo.santos@example.com', 'Leo Santos'),
('00000000-0000-0000-0000-000000000104', 'amira.hassan@example.com', 'Amira Hassan');

INSERT INTO sellers (seller_id, seller_name) VALUES
('00000000-0000-0000-0000-000000000201', 'Northstar Outfitters'),
('00000000-0000-0000-0000-000000000202', 'Volt Home Goods'),
('00000000-0000-0000-0000-000000000203', 'BrightDesk Supply');

INSERT INTO products (product_id, seller_id, sku, product_name, category, price) VALUES
('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000201', 'NS-BAG-001', 'TrailLite Everyday Backpack', 'Bags', 79.00),
('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000201', 'NS-JKT-002', 'StormShell Rain Jacket', 'Apparel', 129.00),
('00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000202', 'VH-LMP-011', 'ArcLine Desk Lamp', 'Home', 48.50),
('00000000-0000-0000-0000-000000000304', '00000000-0000-0000-0000-000000000203', 'BD-CHR-020', 'ErgoTask Chair', 'Office', 219.00);

INSERT INTO inventory (inventory_id, product_id, quantity_on_hand, reserved_quantity, low_stock_threshold) VALUES
('00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000301', 40, 0, 8),
('00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000302', 22, 0, 6),
('00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000303', 55, 0, 12),
('00000000-0000-0000-0000-000000000404', '00000000-0000-0000-0000-000000000304', 14, 0, 4);

INSERT INTO orders (order_id, customer_id, seller_id, order_status, order_total, currency, created_at, updated_at) VALUES
('00000000-0000-0000-0000-000000000501', '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000201', 'PAID', 79.00, 'USD', now() - interval '25 minutes', now() - interval '24 minutes'),
('00000000-0000-0000-0000-000000000502', '00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000202', 'CREATED', 97.00, 'USD', now() - interval '12 minutes', now() - interval '12 minutes');

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, line_total) VALUES
('00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000501', '00000000-0000-0000-0000-000000000301', 1, 79.00, 79.00),
('00000000-0000-0000-0000-000000000602', '00000000-0000-0000-0000-000000000502', '00000000-0000-0000-0000-000000000303', 2, 48.50, 97.00);

INSERT INTO stock_movements (movement_id, product_id, movement_type, quantity_delta, reason, order_id, created_at) VALUES
('00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000301', 'SALE', -1, 'Seed paid order', '00000000-0000-0000-0000-000000000501', now() - interval '24 minutes'),
('00000000-0000-0000-0000-000000000702', '00000000-0000-0000-0000-000000000303', 'SALE', -2, 'Seed pending order', '00000000-0000-0000-0000-000000000502', now() - interval '12 minutes');

INSERT INTO payments (payment_id, order_id, payment_status, payment_method, amount, paid_at, created_at, updated_at) VALUES
('00000000-0000-0000-0000-000000000801', '00000000-0000-0000-0000-000000000501', 'SUCCESS', 'CARD', 79.00, now() - interval '24 minutes', now() - interval '25 minutes', now() - interval '24 minutes'),
('00000000-0000-0000-0000-000000000802', '00000000-0000-0000-0000-000000000502', 'PENDING', 'WALLET', 97.00, NULL, now() - interval '12 minutes', now() - interval '12 minutes');

INSERT INTO shipments (shipment_id, order_id, shipment_status, carrier, tracking_number, shipped_at) VALUES
('00000000-0000-0000-0000-000000000901', '00000000-0000-0000-0000-000000000501', 'SHIPPED', 'DHL', 'DHL-SEED-501', now() - interval '10 minutes');
