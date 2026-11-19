
"""Refresh PulseIQ public monthly aggregates from PostgreSQL."""

import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public_data"
OUTPUT_FILE = OUTPUT_DIR / "public_monthly_metrics.csv"

COLUMNS = [
    "month",
    "headcount_start",
    "hires",
    "exits",
    "headcount_end",
    "monthly_attrition_pct",
    "rolling_12m_attrition_pct",
    "attendance_rate_pct",
    "late_arrivals",
]


def get_connection():
    load_dotenv(ROOT / ".env", override=False)

    required = [
        "WAREHOUSE_HOST",
        "WAREHOUSE_PORT",
        "WAREHOUSE_DB",
        "WAREHOUSE_USER",
        "WAREHOUSE_PASSWORD",
    ]

    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing warehouse environment settings: "
            + ", ".join(missing)
        )

    return psycopg.connect(
        host=os.environ["WAREHOUSE_HOST"],
        port=int(os.environ["WAREHOUSE_PORT"]),
        dbname=os.environ["WAREHOUSE_DB"],
        user=os.environ["WAREHOUSE_USER"],
        password=os.environ["WAREHOUSE_PASSWORD"],
        connect_timeout=15,
        options="-c default_transaction_read_only=on",
    )


def load_aggregates(conn):
    with conn.cursor() as cur:

        # Company-wide monthly workforce aggregates.
        cur.execute("""
            SELECT
                month_start_date,
                SUM(headcount_start) AS headcount_start,
                SUM(hires) AS hires,
                SUM(exits) AS exits,
                SUM(voluntary_exits) AS voluntary_exits,
                SUM(transfers_in) AS transfers_in,
                SUM(transfers_out) AS transfers_out,
                SUM(headcount_end) AS headcount_end
            FROM warehouse.fact_headcount_monthly
            GROUP BY month_start_date
            ORDER BY month_start_date
        """)

        workforce_rows = cur.fetchall()

        # Company-wide attendance aggregates.
        cur.execute("""
            SELECT
                DATE_TRUNC('month', period_end_date)::date AS month_start_date,
                SUM(scheduled_days) AS scheduled_days,
                SUM(present_days) AS present_days,
                SUM(half_days_unpaid) AS half_days_unpaid,
                SUM(late_arrivals) AS late_arrivals
            FROM warehouse.fact_attendance_monthly
            GROUP BY DATE_TRUNC('month', period_end_date)::date
            ORDER BY month_start_date
        """)

        attendance_rows = cur.fetchall()

    workforce_columns = [
        "month_start_date",
        "headcount_start",
        "hires",
        "exits",
        "voluntary_exits",
        "transfers_in",
        "transfers_out",
        "headcount_end",
    ]

    attendance_columns = [
        "month_start_date",
        "scheduled_days",
        "present_days",
        "half_days_unpaid",
        "late_arrivals",
    ]

    workforce = pd.DataFrame(
        workforce_rows, columns=workforce_columns
    )
    attendance = pd.DataFrame(
    attendance_rows, columns=attendance_columns
)

# Convert PostgreSQL Decimal values to numeric floats.
    for col in attendance_columns[1:]:
     attendance[col] = pd.to_numeric(
        attendance[col], errors="coerce"
    ).astype(float)
    if workforce.empty:
        raise ValueError("No workforce records found in warehouse.")

    if attendance.empty:
        raise ValueError("No attendance records found in warehouse.")

    return workforce, attendance


def build_public_data(workforce, attendance):
    workforce["month_start_date"] = pd.to_datetime(
        workforce["month_start_date"]
    )

    attendance["month_start_date"] = pd.to_datetime(
        attendance["month_start_date"]
    )

    workforce = workforce.sort_values("month_start_date").copy()

    # Validate monthly headcount reconciliation.
    expected_end = (
        workforce["headcount_start"]
        + workforce["hires"]
        + workforce["transfers_in"]
        - workforce["exits"]
        - workforce["transfers_out"]
    )

    if not expected_end.equals(workforce["headcount_end"]):
        raise ValueError(
            "Headcount reconciliation failed. "
            "Existing public CSV has not been replaced."
        )

    # Preserve the public dashboard's voluntary attrition methodology.
    workforce["monthly_attrition_pct"] = (
        workforce["voluntary_exits"]
        / workforce["headcount_start"].replace(0, pd.NA)
        * 100
    )

    rolling_exits = workforce["voluntary_exits"].rolling(
        window=12, min_periods=12
    ).sum()

    rolling_base = workforce["headcount_start"].rolling(
        window=12, min_periods=12
    ).mean()

    workforce["rolling_12m_attrition_pct"] = (
        rolling_exits / rolling_base.replace(0, pd.NA) * 100
    )

    # Use the official warehouse attendance formula.
    attendance["attendance_rate_pct"] = (
        (
            attendance["present_days"]
            + 0.5 * attendance["half_days_unpaid"]
        )
        / attendance["scheduled_days"].replace(0, pd.NA)
        * 100
    )

    public = workforce.merge(
        attendance[
            [
                "month_start_date",
                "attendance_rate_pct",
                "late_arrivals",
            ]
        ],
        on="month_start_date",
        how="left",
        validate="one_to_one",
    )

    # Keep only the latest available warehouse reporting period.
    public["month"] = public["month_start_date"].dt.strftime("%Y-%m")

    result = public[COLUMNS].copy()

    # Validate the final public dataset before publishing.
    if result["month"].duplicated().any():
        raise ValueError("Duplicate reporting months found.")

    if result["headcount_end"].isna().any():
        raise ValueError("Missing closing headcount values.")

    if (result["headcount_end"] < 0).any():
        raise ValueError("Invalid negative headcount found.")

    if not result["month"].is_monotonic_increasing:
        raise ValueError("Reporting months are not ordered.")

    return result


def main():
    print("Connecting to PulseIQ warehouse...")

    with get_connection() as conn:
        workforce, attendance = load_aggregates(conn)

    print("Workforce months:", len(workforce))
    print("Attendance months:", len(attendance))

    public = build_public_data(workforce, attendance)

    # Write to a temporary file first. Preserve the previous CSV
    # if validation or writing fails.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    temporary_file = OUTPUT_DIR / "public_monthly_metrics.tmp.csv"

    try:
        public.to_csv(
            temporary_file,
            index=False,
            float_format="%.2f",
        )
        pd.read_csv(temporary_file)

        temporary_file.replace(OUTPUT_FILE)
    finally:
        if temporary_file.exists():
            temporary_file.unlink()

    latest = public.iloc[-1]

    print("Public dataset refreshed successfully.")
    print("Output:", OUTPUT_FILE)
    print("Monthly rows:", len(public))
    print("Data cutoff:", latest["month"])
    print("Closing headcount:", int(latest["headcount_end"]))
    print("Department-level data: excluded")
    print("Employee-level data: excluded")
    print("Payroll data: excluded")
    print("Headcount reconciliation: passed")


if __name__ == "__main__":
    main()