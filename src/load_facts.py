
import pandas as pd
import psycopg

def connect():
    return psycopg.connect(
        host="localhost",
        port=5433,
        dbname="pulseiq_warehouse",
        user="pulseiq",
        password="pulseiq_dev_password",
    )

def load_dataframe(conn, csv_path, table, columns, key):
    df = pd.read_csv(csv_path)
    df = df[columns]

    # Convert pandas NaN/NaT values to SQL NULL.
    records = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    with conn.cursor() as cur:
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(f'"{c}"' for c in columns)
        updates = ", ".join(
            f'"{c}" = EXCLUDED."{c}"'
            for c in columns if c != key
        )
        query = f"""
            INSERT INTO warehouse."{table}" ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT ("{key}") DO UPDATE SET {updates}
        """
        cur.executemany(query, records)

    print(f"{table}: processed {len(records)} rows")

def main():
    attendance_columns = [
        "attendance_fact_id", "employee_id", "date_key",
        "employee_key", "department_id", "scheduled_days",
        "present_days", "wfh_days", "half_days_unpaid",
        "paid_leave_days", "unpaid_absence_days", "late_arrivals",
        "avg_hours_worked", "overtime_hours", "attendance_rate",
        "period_end_date"
    ]

    leave_columns = [
        "leave_request_id", "employee_id", "employee_key",
        "leave_type_code", "start_date_key", "end_date_key",
        "start_date", "end_date", "days", "status",
        "applied_on", "decided_on", "approver_id", "reason"
    ]

    with connect() as conn:
        load_dataframe(
            conn, "data/clean/attendance.csv",
            "fact_attendance_monthly", attendance_columns,
            "attendance_fact_id"
        )
        load_dataframe(
            conn, "data/clean/leave.csv",
            "fact_leave", leave_columns,
            "leave_request_id"
        )

    print("Attendance and leave loads finished.")

if __name__ == "__main__":
    main()