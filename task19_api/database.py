import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env.example")
load_dotenv(ROOT / ".env", override=True)


def get_connection():
    user = os.getenv("TASK18_DB_USER")
    password = os.getenv("TASK18_DB_PASSWORD")

    if not user or not password:
        raise RuntimeError("Task 18 read-only database credentials are missing.")

    return psycopg.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        dbname=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
        user=user,
        password=password,
        connect_timeout=5,
        options="-c default_transaction_read_only=on",
    )
