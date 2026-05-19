from __future__ import annotations

import os
from pathlib import Path
from typing import Any

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
  padding: 14px 16px;
  border-radius: 0;
}
[data-testid="stMetricLabel"] {
  color: #525252;
}
[data-testid="stMetricValue"] {
  color: #161616;
  font-weight: 400;
}
h1, h2, h3 {
  font-weight: 400;
  letter-spacing: 0;
}
.hero {
  border-left: 4px solid #0f62fe;
  padding: 8px 0 8px 16px;
  margin-bottom: 18px;
}
.section-note {
  color: #525252;
  margin-top: -8px;
  margin-bottom: 14px;
}
div[data-testid="stDataFrame"] {
  border: 1px solid #e0e0e0;
}
</style>
"""


EMPTY_TABLE = pd.DataFrame()


@st.cache_resource
def client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        database=os.getenv("CLICKHOUSE_DATABASE", "cdc_analytics"),
    )


def query_df(sql: str, label: str) -> pd.DataFrame:
    try:
        return client().query_df(sql)
    except Exception as exc:  # Streamlit should render the rest of the page during demos.
        st.error(f"{label} could not be loaded.")
        with st.expander("Query error details"):
            st.code(sql.strip(), language="sql")
            st.exception(exc)
        return EMPTY_TABLE


def scalar(sql: str, label: str, default: Any = 0) -> Any:
    try:
        rows = client().query(sql).result_rows
        return rows[0][0] if rows and rows[0] else default
    except Exception as exc:
        st.warning(f"{label} is unavailable.")
        with st.expander(f"{label} query details"):
            st.code(sql.strip(), language="sql")
            st.caption(str(exc))
        return default


def database_ready() -> bool:
    try:
        client().query("SELECT 1")
        return True
    except Exception as exc:
        st.error("ClickHouse is not reachable from the dashboard.")
        st.caption("Start the local stack, then refresh this page.")
        st.code(
            "\n".join(
                [
                    "podman machine start",
                    "podman compose -f compose.yml up -d",
                    "./scripts/register_connector.sh",
                    "./scripts/create_topics.sh",
                ]
            ),
            language="bash",
        )
        with st.expander("Connection error"):
            st.exception(exc)
        return False


def table_exists(table_name: str) -> bool:
    escaped = table_name.replace("'", "''")
    count = scalar(
        f"""
        SELECT count()
        FROM system.tables
        WHERE database = currentDatabase() AND name = '{escaped}'
        """,
        f"{table_name} availability",
        default=0,
    )
    return int(count or 0) > 0


def money(value: Any) -> str:
    return f"${float(value or 0):,.2f}"


def as_int(value: Any) -> int:
    return int(value or 0)


def row_value(row: pd.Series | dict[str, Any], key: str, default: Any = 0) -> Any:
    if isinstance(row, pd.Series):
        value = row.get(key, default)
    else:
        value = row.get(key, default)
    if pd.isna(value):
        return default
    return value


def render_dataframe(sql: str, label: str, empty_message: str) -> pd.DataFrame:
    df = query_df(sql, label)
    if df.empty:
        st.info(empty_message)
    else:
        st.dataframe(df, width="stretch", hide_index=True)
    return df


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1>ShopPulse real-time CDC platform</h1>
          <p>PostgreSQL changes streamed through Debezium and Redpanda into ClickHouse analytics.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not database_ready():
        st.stop()

    raw_events = scalar("SELECT count() FROM raw_cdc_events", "Raw CDC event count", default=0)
    latest_event = scalar(
        "SELECT coalesce(toString(max(ingested_at)), 'no events') FROM raw_cdc_events",
        "Latest CDC event",
        default="no events",
    )
    cdc_tables = scalar(
        "SELECT countDistinct(source_table) FROM raw_cdc_events",
        "CDC source table count",
        default=0,
    )

    cols = st.columns(3)
    cols[0].metric("Raw CDC events", as_int(raw_events))
    cols[1].metric("CDC source tables", as_int(cdc_tables))
    cols[2].metric("Latest event", latest_event)


def render_executive() -> None:
    st.header("Executive overview")
    st.markdown('<p class="section-note">A business summary of current orders, refunds, sellers, and revenue.</p>', unsafe_allow_html=True)

    df = query_df("SELECT * FROM mart_executive_overview", "Executive overview mart")
    row = df.iloc[0] if not df.empty else {}
    cols = st.columns(6)
    cols[0].metric("GMV", money(row_value(row, "gmv", 0)))
    cols[1].metric("Total orders", as_int(row_value(row, "total_orders", 0)))
    cols[2].metric("Successful payments", as_int(row_value(row, "successful_payments", 0)))
    cols[3].metric("Cancelled orders", as_int(row_value(row, "cancelled_orders", 0)))
    cols[4].metric("Refund amount", money(row_value(row, "refund_amount", 0)))
    cols[5].metric("Active sellers", as_int(row_value(row, "active_sellers", 0)))

    st.subheader("Recent orders")
    render_dataframe(
        """
        SELECT order_id, order_status, order_total, currency, created_at, updated_at
        FROM fact_orders
        ORDER BY updated_at DESC
        LIMIT 20
        """,
        "Recent orders",
        "No order facts are available yet. Run the demo sequence while the CDC processor is running.",
    )

    st.subheader("Batch ETL comparison")
    current_orders = scalar("SELECT count() FROM fact_orders", "Current order count", default=0)
    st.info(
        f"CDC current order count: {current_orders}. "
        "An hourly batch dashboard would stay stale until its next scheduled refresh."
    )


def render_inventory() -> None:
    st.header("Real-time inventory")
    st.markdown('<p class="section-note">Current stock state plus a movement audit trail created from CDC events.</p>', unsafe_allow_html=True)

    cols = st.columns(3)
    cols[0].metric(
        "Low stock products",
        as_int(scalar("SELECT count() FROM mart_realtime_inventory WHERE is_low_stock", "Low stock count", default=0)),
    )
    cols[1].metric(
        "Out of stock products",
        as_int(scalar("SELECT count() FROM mart_realtime_inventory WHERE is_out_of_stock", "Out-of-stock count", default=0)),
    )
    cols[2].metric(
        "Latest inventory event",
        scalar("SELECT coalesce(toString(max(ingested_at)), 'no events') FROM cur_inventory", "Latest inventory event", default="no events"),
    )

    st.subheader("Inventory by product")
    render_dataframe(
        """
        SELECT seller_name, sku, product_name, category, quantity_on_hand, low_stock_threshold, is_low_stock
        FROM mart_realtime_inventory
        ORDER BY is_low_stock DESC, quantity_on_hand ASC
        """,
        "Inventory mart",
        "No inventory rows are available yet. Confirm the Debezium snapshot has completed.",
    )

    st.subheader("Stock movement audit trail")
    render_dataframe(
        """
        SELECT m.created_at, p.product_name, m.movement_type, m.quantity_delta, m.reason, m.order_id
        FROM fact_inventory_movements AS m
        LEFT JOIN dim_products AS p ON m.product_id = p.product_id
        ORDER BY m.created_at DESC
        LIMIT 50
        """,
        "Stock movement audit trail",
        "No stock movement facts are available yet.",
    )


def render_sellers() -> None:
    st.header("Seller operations")
    st.markdown('<p class="section-note">Seller-level revenue, cancellations, refunds, and product demand.</p>', unsafe_allow_html=True)

    render_dataframe(
        """
        SELECT seller_name, total_orders, cancelled_orders, gross_revenue, refund_amount, net_revenue
        FROM mart_seller_performance
        ORDER BY net_revenue DESC
        """,
        "Seller performance mart",
        "No seller performance rows are available yet.",
    )

    st.subheader("Top products by ordered units")
    render_dataframe(
        """
        SELECT
            coalesce(p.product_name, 'Unknown product') AS product_name,
            coalesce(p.category, 'Unknown category') AS category,
            coalesce(s.seller_name, 'Unknown seller') AS seller_name,
            sum(oi.quantity) AS units_sold,
            sum(oi.line_total) AS ordered_amount
        FROM (SELECT * FROM cur_order_items FINAL) AS oi
        LEFT JOIN dim_products AS p ON oi.product_id = p.product_id
        LEFT JOIN dim_sellers AS s ON p.seller_id = s.seller_id
        WHERE oi.is_deleted = 0
        GROUP BY product_name, category, seller_name
        ORDER BY units_sold DESC
        LIMIT 20
        """,
        "Top products",
        "No ordered product rows are available yet. Run the flash sale demo script.",
    )


def render_payments() -> None:
    st.header("Payment monitoring")
    st.markdown('<p class="section-note">Payment status totals and recent lifecycle transitions.</p>', unsafe_allow_html=True)

    render_dataframe(
        """
        SELECT payment_status, payment_count, payment_amount, latest_status_update
        FROM mart_payment_monitoring
        ORDER BY payment_status
        """,
        "Payment monitoring mart",
        "No payment rows are available yet.",
    )

    st.subheader("Recent payment transitions")
    render_dataframe(
        """
        SELECT payment_id, order_id, payment_status, payment_method, amount, paid_at, failed_at, updated_at
        FROM fact_payments
        ORDER BY updated_at DESC
        LIMIT 30
        """,
        "Recent payment transitions",
        "No payment facts are available yet.",
    )


def render_health() -> None:
    st.header("CDC pipeline health")
    st.markdown('<p class="section-note">A lightweight trust layer for freshness, failures, and quality checks.</p>', unsafe_allow_html=True)

    cols = st.columns(4)
    cols[0].metric("Raw CDC events", as_int(scalar("SELECT count() FROM raw_cdc_events", "Raw CDC events", default=0)))
    cols[1].metric(
        "Failed events",
        as_int(scalar("SELECT count() FROM pipeline_event_log WHERE level = 'ERROR'", "Failed event count", default=0)),
    )
    cols[2].metric(
        "DQ failures",
        as_int(scalar("SELECT count() FROM data_quality_results WHERE status = 'FAIL'", "DQ failure count", default=0)),
    )
    cols[3].metric(
        "Latest event",
        scalar("SELECT coalesce(toString(max(ingested_at)), 'no events') FROM raw_cdc_events", "Latest CDC event", default="no events"),
    )

    st.subheader("Latest CDC event by topic")
    render_dataframe(
        """
        SELECT kafka_topic, max(ingested_at) AS latest_ingested_at, count() AS events
        FROM raw_cdc_events
        GROUP BY kafka_topic
        ORDER BY latest_ingested_at DESC
        """,
        "Latest CDC event by topic",
        "No raw CDC events are available yet.",
    )

    st.subheader("Data quality results")
    if table_exists("data_quality_results"):
        render_dataframe(
            """
            SELECT checked_at, check_name, check_level, severity, status, failed_count, details
            FROM data_quality_results
            ORDER BY checked_at DESC
            LIMIT 50
            """,
            "Data quality results",
            "No quality checks have been run yet. Run `make quality` after demo data lands.",
        )
    else:
        st.info("The data quality table has not been created yet. Restart ClickHouse with the current init scripts.")

    st.subheader("Processor log")
    render_dataframe(
        """
        SELECT logged_at, level, component, event_type, source_table, message
        FROM pipeline_event_log
        ORDER BY logged_at DESC
        LIMIT 100
        """,
        "Processor log",
        "No processor log rows are available yet.",
    )


st.markdown(STYLE, unsafe_allow_html=True)
render_header()

page = st.sidebar.radio(
    "Dashboard",
    ["Executive overview", "Real-time inventory", "Seller operations", "Payment monitoring", "CDC pipeline health"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Run the demo scripts, then refresh this page to see CDC-driven state changes.")
st.sidebar.caption("Redpanda Console: http://localhost:8080")

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
