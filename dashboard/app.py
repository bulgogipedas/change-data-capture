from __future__ import annotations

import os
from pathlib import Path

import clickhouse_connect
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


st.set_page_config(page_title="ShopPulse CDC Platform", layout="wide")


STYLE = """
<style>
html, body, [class*="css"] {
  font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
}
.stApp {
  background: #ffffff;
  color: #161616;
}
[data-testid="stMetric"] {
  background: #f4f4f4;
  border: 1px solid #e0e0e0;
  padding: 16px;
  border-radius: 0;
}
h1, h2, h3 {
  font-weight: 400;
  letter-spacing: 0;
}
</style>
"""


@st.cache_resource
def client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        database=os.getenv("CLICKHOUSE_DATABASE", "cdc_analytics"),
    )


def query_df(sql: str) -> pd.DataFrame:
    return client().query_df(sql)


def scalar(sql: str, default=0):
    rows = client().query(sql).result_rows
    return rows[0][0] if rows else default


def money(value) -> str:
    return f"${float(value or 0):,.2f}"


def render_executive() -> None:
    st.header("Executive overview")
    df = query_df("SELECT * FROM mart_executive_overview")
    row = df.iloc[0] if not df.empty else {}
    cols = st.columns(6)
    cols[0].metric("GMV", money(row.get("gmv", 0)))
    cols[1].metric("Total orders", int(row.get("total_orders", 0)))
    cols[2].metric("Successful payments", int(row.get("successful_payments", 0)))
    cols[3].metric("Cancelled orders", int(row.get("cancelled_orders", 0)))
    cols[4].metric("Refund amount", money(row.get("refund_amount", 0)))
    cols[5].metric("Active sellers", int(row.get("active_sellers", 0)))

    st.subheader("Recent orders")
    st.dataframe(
        query_df(
            """
            SELECT order_id, order_status, order_total, currency, created_at, updated_at
            FROM fact_orders
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 20
            """
        ),
        use_container_width=True,
    )

    st.subheader("Batch ETL comparison")
    current_orders = scalar("SELECT count() FROM fact_orders")
    st.info(f"CDC current order count: {current_orders}. An hourly batch dashboard would remain stale until its next refresh.")


def render_inventory() -> None:
    st.header("Real-time inventory")
    cols = st.columns(3)
    cols[0].metric("Low stock products", scalar("SELECT count() FROM mart_realtime_inventory WHERE is_low_stock"))
    cols[1].metric("Out of stock products", scalar("SELECT count() FROM mart_realtime_inventory WHERE is_out_of_stock"))
    cols[2].metric("Latest inventory event", scalar("SELECT coalesce(toString(max(ingested_at)), 'no events') FROM cur_inventory"))

    st.subheader("Inventory by product")
    st.dataframe(
        query_df(
            """
            SELECT seller_name, sku, product_name, category, quantity_on_hand, low_stock_threshold, is_low_stock, updated_at
            FROM mart_realtime_inventory
            ORDER BY is_low_stock DESC, quantity_on_hand ASC
            """
        ),
        use_container_width=True,
    )

    st.subheader("Stock movement audit trail")
    st.dataframe(
        query_df(
            """
            SELECT m.created_at, p.product_name, m.movement_type, m.quantity_delta, m.reason, m.order_id
            FROM fact_inventory_movements m
            LEFT JOIN dim_products p ON m.product_id = p.product_id
            ORDER BY m.created_at DESC
            LIMIT 50
            """
        ),
        use_container_width=True,
    )


def render_sellers() -> None:
    st.header("Seller operations")
    st.dataframe(
        query_df(
            """
            SELECT seller_name, total_orders, cancelled_orders, gross_revenue, refund_amount, net_revenue
            FROM mart_seller_performance
            ORDER BY net_revenue DESC
            """
        ),
        use_container_width=True,
    )

    st.subheader("Top products by ordered units")
    st.dataframe(
        query_df(
            """
            SELECT p.product_name, p.category, s.seller_name, sum(oi.quantity) AS units_sold, sum(oi.line_total) AS ordered_amount
            FROM (SELECT * FROM cur_order_items FINAL) AS oi
            LEFT JOIN dim_products p ON oi.product_id = p.product_id
            LEFT JOIN dim_sellers s ON p.seller_id = s.seller_id
            WHERE oi.is_deleted = 0
            GROUP BY p.product_name, p.category, s.seller_name
            ORDER BY units_sold DESC
            LIMIT 20
            """
        ),
        use_container_width=True,
    )


def render_payments() -> None:
    st.header("Payment monitoring")
    st.dataframe(query_df("SELECT * FROM mart_payment_monitoring ORDER BY payment_status"), use_container_width=True)

    st.subheader("Recent payment transitions")
    st.dataframe(
        query_df(
            """
            SELECT payment_id, order_id, payment_status, payment_method, amount, paid_at, failed_at, updated_at
            FROM fact_payments
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 30
            """
        ),
        use_container_width=True,
    )


def render_health() -> None:
    st.header("CDC pipeline health")
    cols = st.columns(4)
    cols[0].metric("Raw CDC events", scalar("SELECT count() FROM raw_cdc_events"))
    cols[1].metric("Failed events", scalar("SELECT count() FROM pipeline_event_log WHERE level = 'ERROR'"))
    cols[2].metric("DQ failures", scalar("SELECT count() FROM data_quality_results WHERE status = 'FAIL'"))
    cols[3].metric("Latest event", scalar("SELECT coalesce(toString(max(ingested_at)), 'no events') FROM raw_cdc_events"))

    st.subheader("Latest CDC event by topic")
    st.dataframe(
        query_df(
            """
            SELECT kafka_topic, max(ingested_at) AS latest_ingested_at, count() AS events
            FROM raw_cdc_events
            GROUP BY kafka_topic
            ORDER BY latest_ingested_at DESC
            """
        ),
        use_container_width=True,
    )

    st.subheader("Data quality results")
    st.dataframe(
        query_df(
            """
            SELECT checked_at, check_name, check_level, severity, status, failed_count, details
            FROM data_quality_results
            ORDER BY checked_at DESC
            LIMIT 50
            """
        ),
        use_container_width=True,
    )

    st.subheader("Processor log")
    st.dataframe(
        query_df(
            """
            SELECT logged_at, level, component, event_type, source_table, message
            FROM pipeline_event_log
            ORDER BY logged_at DESC
            LIMIT 100
            """
        ),
        use_container_width=True,
    )


st.markdown(STYLE, unsafe_allow_html=True)
st.title("ShopPulse real-time CDC platform")
st.caption("Operational changes in PostgreSQL streamed through Debezium and Redpanda into ClickHouse analytics.")

page = st.sidebar.radio(
    "Dashboard",
    ["Executive overview", "Real-time inventory", "Seller operations", "Payment monitoring", "CDC pipeline health"],
)
st.sidebar.caption("Refresh the page after running demo scripts to see new CDC-driven state.")

if page == "Executive overview":
    render_executive()
elif page == "Real-time inventory":
    render_inventory()
elif page == "Seller operations":
    render_sellers()
elif page == "Payment monitoring":
    render_payments()
else:
    render_health()
