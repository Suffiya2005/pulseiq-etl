
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
    "host": os.getenv("WAREHOUSE_HOST", "localhost"),
    "port": int(os.getenv("WAREHOUSE_PORT", "5433")),
    "dbname": os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
    "user": os.getenv("WAREHOUSE_USER", "pulseiq"),
    "password": os.getenv("WAREHOUSE_PASSWORD"),
}

def clean_value(value):
    """Convert pandas/numpy values to JSON-compatible Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()

    if hasattr(value, "isoformat"):
        return value.isoformat()

    if hasattr(value, "item"):
        return value.item()

    return value
def load_table(conn, table_name):
    df = pd.read_excel(WORKBOOK, sheet_name=table_name)
    df.columns = [str(c).strip().lower() for c in df.columns]

    with conn.cursor() as cur:
        # Preserve the existing table and its permissions.
        cur.execute(
            sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.{} (
                    source_row BIGSERIAL PRIMARY KEY,
                    record JSONB NOT NULL
                )
            """).format(
                sql.Identifier("dq_reference"),
                sql.Identifier(table_name),
            )
        )

        # Clear old records without dropping the table.
        cur.execute(
            sql.SQL("TRUNCATE TABLE {}.{}").format(
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

        # Keep API access after every refresh.
        if table_name in ("fact_ledger", "fact_invoice"):
            cur.execute(
                sql.SQL(
                    "GRANT SELECT ON TABLE {}.{} TO {}"
                ).format(
                    sql.Identifier("dq_reference"),
                    sql.Identifier(table_name),
                    sql.Identifier("pulseiq_dashboard"),
                )
            )

    print(f"Loaded {len(df):,} rows into dq_reference.{table_name}")
    return len(df)

def main():
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK}")

    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "WAREHOUSE_PASSWORD is not set. Check the ETL environment configuration."
        )

    with psycopg.connect(**DB_CONFIG) as conn:
        conn.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                sql.Identifier("dq_reference")
            )
        )

        # Create source refresh metadata table.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS
            dq_reference.source_refresh_metadata (
                source_table TEXT PRIMARY KEY,
                last_successful_refresh TIMESTAMPTZ NOT NULL,
                rows_loaded BIGINT NOT NULL,
                source_file TEXT NOT NULL,
                load_status TEXT NOT NULL
                    CHECK (load_status IN ('success'))
            )
        """)

        # Allow the read-only API account to inspect metadata.
        conn.execute("""
            GRANT SELECT ON TABLE
            dq_reference.source_refresh_metadata
            TO pulseiq_dashboard
        """)

        # Load each reference table and record its successful refresh.
        for table_name in TABLES:
            rows_loaded = load_table(conn, table_name)

            conn.execute("""
                INSERT INTO dq_reference.source_refresh_metadata (
                    source_table,
                    last_successful_refresh,
                    rows_loaded,
                    source_file,
                    load_status
                )
                VALUES (
                    %s,
                    clock_timestamp(),
                    %s,
                    %s,
                    'success'
                )
                ON CONFLICT (source_table)
                DO UPDATE SET
                    last_successful_refresh = EXCLUDED.last_successful_refresh,
                    rows_loaded = EXCLUDED.rows_loaded,
                    source_file = EXCLUDED.source_file,
                    load_status = EXCLUDED.load_status
            """, (
                table_name,
                rows_loaded,
                WORKBOOK.name,
            ))

    print("\nReference data loaded successfully.")


if __name__ == "__main__":
    main()
