
import os
from pathlib import Path

import pandas as pd
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "data" / "reference" / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

TABLES = [
    "fact_ledger",
    "fact_invoice",
    "fact_expense",
    "fact_task",
    "fact_attrition_risk",
]

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "pulseiq_warehouse",
    "user": "pulseiq",
    "password": os.getenv("PGPASSWORD"),
}



def clean_value(value):
    """Convert Excel/Pandas values into JSON-serializable Python values."""
    import datetime
    import numpy as np

    if pd.isna(value):
        return None

    if isinstance(value, (pd.Timestamp, datetime.datetime, datetime.date)):
        return value.isoformat()
def clean_value(value):
    """Convert pandas/numpy values to PostgreSQL-friendly Python values."""
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        return value.item()
    return value
    if isinstance(value, np.generic):
        return clean_value(value.item())

    return value



def load_table(conn, table_name):
    df = pd.read_excel(WORKBOOK, sheet_name=table_name)
    df.columns = [str(c).strip().lower() for c in df.columns]

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                sql.Identifier("dq_reference"),
                sql.Identifier(table_name),
            )
        )

        # Store source values in JSONB for a safe, loss-minimizing import.
        cur.execute(
            sql.SQL(
                "CREATE TABLE {}.{} ("
                "source_row BIGSERIAL PRIMARY KEY, "
                "record JSONB NOT NULL)"
            ).format(
                sql.Identifier("dq_reference"),
                sql.Identifier(table_name),
            )
        )

        insert_query = sql.SQL(
            "INSERT INTO {}.{} (record) VALUES (%s)"
        ).format(
            sql.Identifier("dq_reference"),
            sql.Identifier(table_name),
        )

        for _, row in df.iterrows():
            record = {
                str(column): clean_value(value)
                for column, value in row.items()
            }
            cur.execute(insert_query, (Jsonb(record),))

    print(f"Loaded {len(df):,} rows into dq_reference.{table_name}")


def main():
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK}")

    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "PGPASSWORD is not set. Set it in PowerShell before running."
        )

    with psycopg.connect(**DB_CONFIG) as conn:
        conn.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                sql.Identifier("dq_reference")
            )
        )

        for table_name in TABLES:
            load_table(conn, table_name)

    print("\nReference data loaded successfully.")


if __name__ == "__main__":
    main()
