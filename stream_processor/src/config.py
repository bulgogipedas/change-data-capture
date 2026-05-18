from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    redpanda_brokers: str = os.getenv("REDPANDA_BROKERS", "localhost:9092")
    consumer_group: str = os.getenv("CDC_CONSUMER_GROUP", "clickhouse-cdc-writer")
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    clickhouse_database: str = os.getenv("CLICKHOUSE_DATABASE", "cdc_analytics")
    clickhouse_user: str = os.getenv("CLICKHOUSE_USER", "default")
    clickhouse_password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    poll_timeout_seconds: float = float(os.getenv("CDC_POLL_TIMEOUT_SECONDS", "1.0"))
    flush_every_records: int = int(os.getenv("CDC_FLUSH_EVERY_RECORDS", "50"))


TOPICS = [
    "dbserver1.public.customers",
    "dbserver1.public.sellers",
    "dbserver1.public.products",
    "dbserver1.public.inventory",
    "dbserver1.public.stock_movements",
    "dbserver1.public.orders",
    "dbserver1.public.order_items",
    "dbserver1.public.payments",
    "dbserver1.public.shipments",
    "dbserver1.public.refunds",
]
