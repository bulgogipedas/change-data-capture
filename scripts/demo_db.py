from __future__ import annotations

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def connect():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "shopdb"),
        user=os.getenv("POSTGRES_USER", "cdc_user"),
        password=os.getenv("POSTGRES_PASSWORD", "cdc_password"),
    )
