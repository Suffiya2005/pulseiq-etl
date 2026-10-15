"""Load employee history into the warehouse dimension."""

from pathlib import Path

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
CLEAN_FILE = ROOT / "data" / "clean" / "employees.csv"


def main():
    df = pd.read_csv(CLEAN_FILE, dtype={"employee_key": str, "employee_id": str})

    columns = [
        "employee_key", "employee_id", "department_id", "role_id",
        "valid_from", "valid_to", "is_current", "change_reason",
    ]
    df = df[columns].copy()

    # Convert source Y/N values to actual Python booleans.
    flags = df["is_current"].astype(str).str.strip().str.upper()
    if not flags.isin(["Y", "N"]).all():
        raise ValueError("Unexpected is_current values; expected only Y/N.")
    df["is_current"] = flags.eq("Y")

    # Convert blank dates to NULL and valid dates to date values.
    for col in ["valid_from", "valid_to"]:
        df[col] = pd.to_datetime(df[col], errors="raise").dt.date

    if df["employee_key"].duplicated().any():
        raise ValueError("Duplicate employee_key values found in clean CSV.")

    rows = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    with psycopg.connect(
        host="localhost",
        port=5433,
        dbname="pulseiq_warehouse",
        user="pulseiq",
        password="pulseiq_dev_password",
    ) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO warehouse.dim_employee (
                    employee_key, employee_id, department_id, role_id,
                    valid_from, valid_to, is_current, change_reason
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (employee_key) DO UPDATE SET
                    employee_id = EXCLUDED.employee_id,
                    department_id = EXCLUDED.department_id,
                    role_id = EXCLUDED.role_id,
                    valid_from = EXCLUDED.valid_from,
                    valid_to = EXCLUDED.valid_to,
                    is_current = EXCLUDED.is_current,
                    change_reason = EXCLUDED.change_reason
                """,
                rows,
            )

    print(f"Employee history records processed: {len(df)}")
    print(f"Unique employee IDs: {df['employee_id'].nunique()}")
    print(f"Current versions in CSV: {int(df['is_current'].sum())}")


if __name__ == "__main__":
    main()
