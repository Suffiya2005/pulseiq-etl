
"""Load clean PulseIQ data into PostgreSQL warehouse."""

import os
from pathlib import Path

import pandas as pd
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT / "data" / "clean"


def connect():
    return psycopg.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        dbname=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
        user=os.getenv("WAREHOUSE_USER", "pulseiq"),
        password=os.getenv(
            "WAREHOUSE_PASSWORD", "pulseiq_dev_password"
        ),
    )


def upsert_dataframe(conn, table_name, df, conflict_columns):
    """Insert or update rows using the declared conflict key."""
    if df.empty:
        print(f"{table_name}: no rows to load")
        return

    columns = list(df.columns)

    insert_stmt = sql.SQL(
        "INSERT INTO warehouse.{} ({}) VALUES ({}) "
        "ON CONFLICT ({}) "
    ).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        sql.SQL(", ").join(map(sql.Identifier, conflict_columns)),
    )

    update_columns = [
        column for column in columns
        if column not in conflict_columns
    ]

    if update_columns:
        insert_stmt += sql.SQL("DO UPDATE SET ") + sql.SQL(
            ", "
        ).join(
            sql.SQL("{} = EXCLUDED.{}").format(
                sql.Identifier(column),
                sql.Identifier(column),
            )
            for column in update_columns
        )
    else:
        insert_stmt += sql.SQL("DO NOTHING")

    records = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in df.itertuples(index=False, name=None)
    ]

    with conn.cursor() as cur:
        cur.executemany(insert_stmt, records)

    print(f"{table_name}: processed {len(records)} rows")


def load_payroll(conn):
    df = pd.read_csv(CLEAN_DIR / "payroll.csv")

    # Load only columns present in the warehouse table.
    columns = [
        "payroll_item_id", "run_id", "employee_id", "date_key",
        "employee_key", "period_end_date", "department_id", "role_id",
        "payable_days", "lop_days", "overtime_hours_paid",
        "variable_pay_type", "monthly_fixed_gross", "basic", "hra",
        "conveyance", "medical", "special_allowance", "earned_fixed_pay",
        "overtime_pay", "variable_pay", "gross_pay", "pf_employee",
        "esi_employee", "professional_tax", "tds", "other_deductions",
        "total_deductions", "net_pay", "pf_employer", "esi_employer",
        "employer_cost", "headcount_flag",
    ]

    df = df[columns]
    upsert_dataframe(conn, "fact_payroll", df, ["payroll_item_id"])


def main():
    with connect() as conn:
        load_payroll(conn)

    print("Warehouse payroll load finished.")


if __name__ == "__main__":
    main()
