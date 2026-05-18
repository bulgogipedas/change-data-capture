CREATE PUBLICATION shop_publication FOR TABLE
    customers,
    sellers,
    products,
    inventory,
    stock_movements,
    orders,
    order_items,
    payments,
    shipments,
    refunds;
