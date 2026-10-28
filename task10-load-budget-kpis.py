
from pathlib import Path

import pandas as pd
import psycopg

WORKBOOK = Path(
    "data/source/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)

def connect():
    return psycopg.connect(
        host="localhost",
        port=5433,
        dbname="pulseiq_warehouse",
        user="pulseiq",
        password="pulseiq_dev_password",
    )

def load_table(conn, df, table, columns, key_columns):
    df = df[columns].copy()
    df = df.astype(object).where(pd.notna(df), None)

    definitions = {
        "department_id": "TEXT NOT NULL",
        "month": "DATE NOT NULL",
        "budget_payroll_cost": "NUMERIC(14,2)",
        "attendance_rate_target": "NUMERIC(8,4)",
        "overtime_share_target_pct": "NUMERIC(8,4)",
        "attrition_monthly_target_pct": "NUMERIC(8,4)",
        "task_completion_target_pct": "NUMERIC(8,4)",
    }

    create_columns = ", ".join(
        f'"{col}" {definitions[col]}'
        for col in columns
    )
    primary_key = ", ".join(f'"{col}"' for col in key_columns)

    with conn.cursor() as cur:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS warehouse."{table}" '
            f'({create_columns}, PRIMARY KEY ({primary_key}))'
        )

        placeholders = ", ".join(["%s"] * len(columns))
        col_sql = ", ".join(f'"{col}"' for col in columns)
        updates = ", ".join(
            f'"{col}" = EXCLUDED."{col}"'
            for col in columns if col not in key_columns
        )

        sql = (
            f'INSERT INTO warehouse."{table}" ({col_sql}) '
            f'VALUES ({placeholders}) '
            f'ON CONFLICT ({primary_key}) DO UPDATE SET {updates}'
        )
        records = list(df.itertuples(index=False, name=None))
        cur.executemany(sql, records)

    print(f"{table}: loaded {len(df)} rows")

def main():
    budget = pd.read_excel(
        WORKBOOK, sheet_name="budget_payroll_dept_month"
    )
    targets = pd.read_excel(WORKBOOK, sheet_name="kpi_targets")

    budget["month"] = pd.to_datetime(budget["month"]).dt.date
    targets["month"] = pd.to_datetime(targets["month"]).dt.date

    if budget.duplicated(["department_id", "month"]).any():
        raise ValueError("Duplicate department/month rows in budget")
    if targets.duplicated(["department_id", "month"]).any():
        raise ValueError("Duplicate department/month rows in KPI targets")

    with connect() as conn:
        load_table(
            conn, budget,
            "budget_payroll_dept_month",
            ["department_id", "month", "budget_payroll_cost"],
            ["department_id", "month"],
        )
        load_table(
            conn, targets,
            "kpi_targets",
            [
                "month", "department_id",
                "attendance_rate_target",
                "overtime_share_target_pct",
                "attrition_monthly_target_pct",
                "task_completion_target_pct",
            ],
            ["month", "department_id"],
        )

    print("Task 10 budget and KPI targets loaded.")

if __name__ == "__main__":
    main()