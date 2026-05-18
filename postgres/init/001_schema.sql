CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE customers (
    customer_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL UNIQUE,
    full_name text NOT NULL,
    status text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE sellers (
    seller_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_name text NOT NULL,
    status text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SUSPENDED', 'INACTIVE')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE products (
    product_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id uuid NOT NULL REFERENCES sellers(seller_id),
    sku text NOT NULL,
    product_name text NOT NULL,
    category text NOT NULL,
    price numeric(12, 2) NOT NULL CHECK (price >= 0),
    status text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'OUT_OF_STOCK')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (seller_id, sku)
);

CREATE TABLE inventory (
    inventory_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid NOT NULL UNIQUE REFERENCES products(product_id),
    quantity_on_hand integer NOT NULL CHECK (quantity_on_hand >= 0),
    reserved_quantity integer NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    low_stock_threshold integer NOT NULL DEFAULT 10 CHECK (low_stock_threshold >= 0),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    order_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid NOT NULL REFERENCES customers(customer_id),
    seller_id uuid NOT NULL REFERENCES sellers(seller_id),
    order_status text NOT NULL DEFAULT 'CREATED' CHECK (order_status IN ('CREATED', 'PAID', 'PACKED', 'SHIPPED', 'DELIVERED', 'CANCELLED')),
    order_total numeric(12, 2) NOT NULL CHECK (order_total >= 0),
    currency char(3) NOT NULL DEFAULT 'USD',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    cancelled_at timestamptz,
    deleted_at timestamptz
);

CREATE TABLE order_items (
    order_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES orders(order_id),
    product_id uuid NOT NULL REFERENCES products(product_id),
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12, 2) NOT NULL CHECK (unit_price >= 0),
    line_total numeric(12, 2) NOT NULL CHECK (line_total >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE stock_movements (
    movement_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid NOT NULL REFERENCES products(product_id),
    movement_type text NOT NULL CHECK (movement_type IN ('SALE', 'RESTOCK', 'ADJUSTMENT', 'CANCELLATION', 'REFUND')),
    quantity_delta integer NOT NULL CHECK (quantity_delta <> 0),
    reason text NOT NULL,
    order_id uuid REFERENCES orders(order_id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE payments (
    payment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES orders(order_id),
    payment_status text NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')),
    payment_method text NOT NULL CHECK (payment_method IN ('CARD', 'BANK_TRANSFER', 'WALLET', 'COD')),
    amount numeric(12, 2) NOT NULL CHECK (amount >= 0),
    paid_at timestamptz,
    failed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE shipments (
    shipment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES orders(order_id),
    shipment_status text NOT NULL DEFAULT 'PENDING' CHECK (shipment_status IN ('PENDING', 'SHIPPED', 'DELIVERED', 'RETURNED')),
    carrier text,
    tracking_number text,
    shipped_at timestamptz,
    delivered_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE refunds (
    refund_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id uuid NOT NULL REFERENCES payments(payment_id),
    order_id uuid NOT NULL REFERENCES orders(order_id),
    refund_status text NOT NULL DEFAULT 'REQUESTED' CHECK (refund_status IN ('REQUESTED', 'APPROVED', 'REJECTED', 'COMPLETED')),
    refund_amount numeric(12, 2) NOT NULL CHECK (refund_amount >= 0),
    reason text NOT NULL,
    refunded_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER customers_set_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER sellers_set_updated_at BEFORE UPDATE ON sellers FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER products_set_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER inventory_set_updated_at BEFORE UPDATE ON inventory FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER orders_set_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER payments_set_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER shipments_set_updated_at BEFORE UPDATE ON shipments FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER refunds_set_updated_at BEFORE UPDATE ON refunds FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE customers REPLICA IDENTITY FULL;
ALTER TABLE sellers REPLICA IDENTITY FULL;
ALTER TABLE products REPLICA IDENTITY FULL;
ALTER TABLE inventory REPLICA IDENTITY FULL;
ALTER TABLE stock_movements REPLICA IDENTITY FULL;
ALTER TABLE orders REPLICA IDENTITY FULL;
ALTER TABLE order_items REPLICA IDENTITY FULL;
ALTER TABLE payments REPLICA IDENTITY FULL;
ALTER TABLE shipments REPLICA IDENTITY FULL;
ALTER TABLE refunds REPLICA IDENTITY FULL;
