from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "data" / "reference" / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
REPORT_PATH = ROOT / "task3-dq" / "dq_report.csv"

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "pulseiq_warehouse",
    "user": "pulseiq",
    "password": os.getenv("PGPASSWORD"),
}


CHECKS = [
    {
        "id": "DQ-C01",
        "name": "Payroll equals ledger",
        "table": "fact_payroll / fact_ledger",
        "severity": "CRITICAL",
        "sql": """
            WITH payroll_monthly AS (
                SELECT
                    DATE_TRUNC('month', period_end_date)::date AS month,
                    SUM(employer_cost) AS payroll_cost
                FROM warehouse.fact_payroll
                GROUP BY 1
            ),
            ledger_monthly AS (
                SELECT
                    LEFT(record->>'posting_period', 7) AS month,
                    SUM(
                        COALESCE(
                            (record->>'debit')::numeric, 0
                        )
                    ) AS debits,
                    SUM(
                        COALESCE(
                            (record->>'credit')::numeric, 0
                        )
                    ) AS credits
                FROM dq_reference.fact_ledger
                WHERE record->>'account_code'
                    IN ('5001', '5002', '5003', '5004', '5005')
                GROUP BY 1
            )
            SELECT
                p.month,
                p.payroll_cost,
                l.debits,
                l.credits,
                p.payroll_cost - (l.debits - l.credits) AS difference
            FROM payroll_monthly p
            JOIN ledger_monthly l
              ON TO_CHAR(p.month, 'YYYY-MM') = l.month
            WHERE ABS(
                p.payroll_cost - (l.debits - l.credits)
            ) > 0.01
            ORDER BY p.month
        """,
        "reason": (
            "Payroll totals must reconcile with salary-related "
            "ledger entries."
        ),
    },
    {

        "id": "DQ-C02",
        "name": "Ledger balanced",
        "table": "fact_ledger",
        "severity": "CRITICAL",
        "sql": """
            SELECT record->>'entry_id' AS entry_id,
                   SUM(COALESCE((record->>'debit')::numeric, 0)) AS debit,
                   SUM(COALESCE((record->>'credit')::numeric, 0)) AS credit
            FROM dq_reference.fact_ledger
            GROUP BY record->>'entry_id'
            HAVING ABS(
                SUM(COALESCE((record->>'debit')::numeric, 0))
                - SUM(COALESCE((record->>'credit')::numeric, 0))
            ) > 0.005
        """,
        "reason": "Every ledger entry must have equal debit and credit totals.",
    },
{
        "id": "DQ-C03",
        "name": "Unique payroll rows",
        "table": "fact_payroll",
        "severity": "CRITICAL",
        "sql": """
            SELECT employee_id, period_end_date,
                   COUNT(*) AS row_count,
                   STRING_AGG(payroll_item_id, ', ') AS payroll_ids
            FROM warehouse.fact_payroll
            GROUP BY employee_id, period_end_date
            HAVING COUNT(*) > 1
        """,
        "reason": "Duplicate employee-month payroll rows can overstate payroll  totals.",
    },
    
{
        "id": "DQ-C04",
        "name": "No orphan employees",
        "table": "fact_payroll / dim_employee",
        "severity": "CRITICAL",
        "sql": None,
        "reason": "Payroll employee IDs must exist in the employee dimension.",
    },

{
        "id": "DQ-C05",
        "name": "No attendance after exit",
        "table": "fact_attendance_monthly",
        "severity": "WARNING",
        
        "sql": """
            SELECT a.attendance_fact_id, a.employee_id,
                   a.period_end_date, a.employee_key
            FROM warehouse.fact_attendance_monthly a
            JOIN warehouse.dim_employee d
              ON d.employee_id = a.employee_id
             AND d.employee_key = a.employee_key
            WHERE a.period_end_date > d.valid_to
        """,

        "reason": "Attendance must match a valid employee history period.",
    },
{
        "id": "DQ-C06",
        "name": "Unpaid leave deducted",
        "table": "fact_attendance_monthly / fact_payroll",
        "severity": "WARNING",
        "sql": """
            SELECT a.employee_id, a.period_end_date,
                   a.unpaid_absence_days, p.lop_days
            FROM warehouse.fact_attendance_monthly a
            JOIN warehouse.fact_payroll p
              ON p.employee_id = a.employee_id
             AND p.period_end_date = a.period_end_date
            WHERE a.unpaid_absence_days > COALESCE(p.lop_days, 0) + 0.5
        """,
        "reason": "Unpaid absences should be reflected in loss-of-pay days.",
    },
{
        "id": "DQ-C07",
        "name": "Invoice arithmetic",
        "table": "fact_invoice",
        "severity": "WARNING",
        "sql": """
            SELECT record->>'invoice_id' AS invoice_id
            FROM dq_reference.fact_invoice
            WHERE (record->>'amount_paid')::numeric
                    > (record->>'total_amount')::numeric + 0.01
               OR (record->>'balance_due')::numeric < -0.01
        """,
        "reason": "Payments must not exceed invoice totals or create negative balances.",
    },
{
        "id": "DQ-C08",
        "name": "Expense arithmetic",
        "table": "fact_expense",
        "severity": "WARNING",
        "sql": """
            SELECT record->>'expense_id' AS expense_id
            FROM dq_reference.fact_expense
            WHERE ABS(
                (record->>'total_amount')::numeric
                - (
                    (record->>'amount_excl_gst')::numeric
                    + (record->>'gst_amount')::numeric
                )
            ) > 0.01
        """,
        "reason": "Expense totals must equal the amount excluding GST plus GST.",
    },
{
        "id": "DQ-C09",
        "name": "Task dates sensible",
        "table": "fact_task",
        "severity": "WARNING",
        "sql": """
            SELECT record->>'task_id' AS task_id
            FROM dq_reference.fact_task
            WHERE (
                NULLIF(record->>'completed_date', '') IS NOT NULL
                AND NULLIF(record->>'started_date', '') IS NOT NULL
                AND (record->>'completed_date')::date
                    < (record->>'started_date')::date
            )
            OR (
                LOWER(COALESCE(record->>'status', '')) = 'done'
                AND NULLIF(record->>'completed_date', '') IS NULL
            )
        """,
        "reason": "Task dates must be valid for cycle-time and delivery metrics.",
    },
{
        "id": "DQ-C10",
        "name": "Leave dates sensible",
        "table": "fact_leave",
        "severity": "WARNING",
        "sql": """
            SELECT leave_request_id, start_date, end_date
            FROM warehouse.fact_leave
            WHERE end_date < start_date
        """,
        "reason": "Leave end dates must not precede start dates.",
    },
{
        "id": "DQ-C11",
        "name": "AI feeds are fresh",
        "table": "fact_attrition_risk",
        "severity": "WARNING",
        "sql": """
            SELECT record->>'prediction_id' AS prediction_id,
                   record->>'as_of_date' AS as_of_date
            FROM dq_reference.fact_attrition_risk
            WHERE NULLIF(record->>'as_of_date', '') IS NULL
               OR (record->>'as_of_date')::date < (
                    SELECT MAX((record->>'as_of_date')::date)
                    FROM dq_reference.fact_attrition_risk
                    WHERE NULLIF(record->>'as_of_date', '') IS NOT NULL
               ) - 7
        """,
        "reason": "Old predictions must not be presented as current risk scores.",
    },
{
        "id": "DQ-C12",
        "name": "Dimension history does not overlap",
        "table": "dim_employee",
        "severity": "CRITICAL",
        "sql": """
            SELECT a.employee_id,
                   a.employee_key AS version_a,
                   b.employee_key AS version_b,
                   a.valid_from AS a_from, a.valid_to AS a_to,
                   b.valid_from AS b_from, b.valid_to AS b_to
            FROM warehouse.dim_employee a
            JOIN warehouse.dim_employee b
              ON a.employee_id = b.employee_id
             AND a.employee_key < b.employee_key
             AND a.valid_from <= COALESCE(b.valid_to, DATE '9999-12-31')
             AND b.valid_from <= COALESCE(a.valid_to, DATE '9999-12-31')
        """,
        "reason": "Overlapping employee history versions can duplicate fact joins.",
    },
{
        "id": "DQ-C13",
        "name": "Pipeline freshness",
        "table": "logs/run_summary.json",
        "severity": "CRITICAL",
        "sql": None,
        "reason": "A stale pipeline means dashboards may use outdated data.",
    },
{
        "id": "DQ-C14",
        "name": "Minimum group size",
        "table": "metric_dictionary / reporting queries",
        "severity": "CRITICAL",
        "sql": None,
        "reason": "Small reporting groups may expose individual employee information.",
    },
]


def table_exists(conn, table_name):
    parts = table_name.strip().split(".", 1)

    if len(parts) == 2:
        schema, table = parts
    else:
        table = parts[0]
        schema = None

    with conn.cursor() as cur:
        if schema:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_name = %s
                )
                """,
                (schema, table),
            )
        else:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema IN ('warehouse', 'dq_reference')
                      AND table_name = %s
                )
                """,
                (table,),
            )

        return cur.fetchone()[0]

def check_pipeline_freshness():
    summary_path = ROOT / "logs" / "run_summary.json"

    if not summary_path.exists():
        return 1, "FAIL", "logs/run_summary.json was not found."

    try:
        with open(summary_path, "r", encoding="utf-8") as file:
            summary = json.load(file)

        finished_at = summary.get("finished_at_utc")
        if not finished_at:
            return 1, "FAIL", "Pipeline finish time is missing."

        finished_at = datetime.fromisoformat(
            finished_at.replace("Z", "+00:00")
        )

        if finished_at.tzinfo is None:
            finished_at = finished_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - finished_at

        if age < timedelta(0):
            return 1, "FAIL", "Pipeline finish time is in the future."

        if age > timedelta(hours=24):
            return 1, "FAIL", "Pipeline has not finished within the last 24 hours."

        return 0, "PASS", "Pipeline finished within the last 24 hours."

    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return 1, "ERROR", f"Could not read pipeline summary: {exc}"



def run_checks():
    if not WORKBOOK.exists():
        raise FileNotFoundError(
            f"Reference workbook not found: {WORKBOOK}"
        )

    catalog = pd.read_excel(
        WORKBOOK, sheet_name="dq_checks_catalog"
    )
    print(f"Loaded {len(catalog)} checks from the reference catalog.")

    results = []

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS warehouse.dq_results (
                    result_id BIGSERIAL PRIMARY KEY,
                    check_id TEXT NOT NULL,
                    check_name TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    bad_rows BIGINT,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    risk_explanation TEXT,
                    run_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()

        for check in CHECKS:
            status = "NOT_APPLICABLE"
            bad_rows = None
            message = check["reason"]

            try:
                if check["id"] == "DQ-C13":
                    bad_rows, status, message = (
                        check_pipeline_freshness()
                    )

                elif check["id"] == "DQ-C04":
                    payroll = pd.read_excel(
                        WORKBOOK, sheet_name="fact_payroll"
                    )
                    employees = pd.read_excel(
                        WORKBOOK, sheet_name="dim_employee"
                    )

                    missing = payroll[
                        ~payroll["employee_id"].isin(
                            employees["employee_id"]
                        )
                    ]
                    bad_rows = len(missing)
                    status = "PASS" if bad_rows == 0 else "FAIL"
                    message = (
                        "All payroll employees exist in the employee dimension."
                        if bad_rows == 0
                        else "Orphan payroll IDs: "
                        + ", ".join(
                            missing["payroll_item_id"].astype(str)
                        )
                    )

                elif check["id"] == "DQ-C05":
                    attendance = pd.read_excel(
                        WORKBOOK,
                        sheet_name="fact_attendance_monthly"
                    )
                    employees = pd.read_excel(
                        WORKBOOK, sheet_name="dim_employee"
                    )

                    attendance["period_end_date"] = pd.to_datetime(
                        attendance["period_end_date"],
                        errors="coerce"
                    )
                    employees["exit_date"] = pd.to_datetime(
                        employees["exit_date"],
                        errors="coerce"
                    )

                    exits = (
                        employees[["employee_id", "exit_date"]]
                        .dropna(subset=["exit_date"])
                        .groupby("employee_id", as_index=False)["exit_date"]
                        .max()
                    )
                    exits["exit_month_end"] = (
                        exits["exit_date"] + pd.offsets.MonthEnd(0)
                    )

                    checked = attendance.merge(
                        exits[["employee_id", "exit_month_end"]],
                        on="employee_id",
                        how="inner"
                    )
                    invalid = checked[
                        checked["period_end_date"].notna()
                        & (
                            checked["period_end_date"]
                            > checked["exit_month_end"]
                        )
                    ]

                    bad_rows = len(invalid)
                    status = "PASS" if bad_rows == 0 else "FAIL"
                    message = (
                        "No attendance found after employee exit month."
                        if bad_rows == 0
                        else "Attendance after exit: "
                        + ", ".join(
                            invalid["attendance_fact_id"].astype(str)
                        )
                    )

                elif check["id"] == "DQ-C10":
                    leave = pd.read_excel(
                        WORKBOOK, sheet_name="fact_leave"
                    )
                    leave["start_date"] = pd.to_datetime(
                        leave["start_date"], errors="coerce"
                    )
                    leave["end_date"] = pd.to_datetime(
                        leave["end_date"], errors="coerce"
                    )

                    invalid = leave[
                        leave["start_date"].notna()
                        & leave["end_date"].notna()
                        & (
                            leave["end_date"]
                            < leave["start_date"]
                        )
                    ]

                    bad_rows = len(invalid)
                    status = "PASS" if bad_rows == 0 else "FAIL"
                    message = (
                        "All leave dates are sensible."
                        if bad_rows == 0
                        else "Invalid leave dates: "
                        + ", ".join(
                            invalid["leave_request_id"].astype(str)
                        )
                    )

                elif check["id"] == "DQ-C12":
                    employees = pd.read_excel(
                        WORKBOOK, sheet_name="dim_employee"
                    )
                    employees["valid_from"] = pd.to_datetime(
                        employees["valid_from"], errors="coerce"
                    )
                    employees["valid_to"] = pd.to_datetime(
                        employees["valid_to"], errors="coerce"
                    )
                    employees = employees.sort_values(
                        ["employee_id", "valid_from"]
                    )

                    # Compare each interval with all previous intervals.
                    overlap_ids = []
                    for employee_id, group in employees.groupby(
                        "employee_id"
                    ):
                        group = group.reset_index(drop=True)
                        for i in range(len(group)):
                            start = group.loc[i, "valid_from"]
                            if pd.isna(start):
                                continue

                            for j in range(i):
                                previous_end = group.loc[j, "valid_to"]
                                if (
                                    pd.isna(previous_end)
                                    or start <= previous_end
                                ):
                                    overlap_ids.append(str(employee_id))
                                    break
                            if str(employee_id) in overlap_ids:
                                continue

                    overlap_ids = sorted(set(overlap_ids))
                    bad_rows = len(overlap_ids)
                    status = "PASS" if bad_rows == 0 else "FAIL"
                    message = (
                        "No overlapping employee history intervals."
                        if bad_rows == 0
                        else "Overlapping history for employee IDs: "
                        + ", ".join(overlap_ids)
                    )

                elif check["id"] == "DQ-C14":
                    metric_dict = pd.read_excel(
                        WORKBOOK, sheet_name="metric_dictionary"
                    )
                    raw_minimums = (
                        metric_dict["minimum_group_size"]
                        .dropna()
                        .astype(str)
                        .str.strip()
                    )
                    minimums = raw_minimums.str.extract(
                        r"^(\d+(?:\.\d+)?)",
                        expand=False,
                    )
                    numeric_minimums = pd.to_numeric(
                        minimums, errors="coerce"
                    )
                    invalid = (
                        minimums.isna()
                        | numeric_minimums.isna()
                        | (numeric_minimums <= 0)
                    )
                    bad_rows = int(invalid.sum())
                    status = "PASS" if bad_rows == 0 else "FAIL"
                    message = (
                        f"Positive minimum group-size thresholds are defined "
                        f"for {len(raw_minimums)} metrics; "
                        f"{bad_rows} configured thresholds are invalid."
                    )

                elif check["sql"] is not None:
                    tables = [
                        table.strip()
                        for table in check["table"].split("/")
                    ]

                    if not all(
                        table_exists(conn, table)
                        for table in tables
                    ):
                        status = "NOT_APPLICABLE"
                        message = (
                            f"{check['reason']} Required table "
                            "is not loaded."
                        )
                    else:
                        with conn.cursor() as cur:
                            cur.execute(check["sql"])
                            rows = cur.fetchall()

                        bad_rows = len(rows)
                        status = "PASS" if bad_rows == 0 else "FAIL"
                        message = (
                            "No data-quality issues found."
                            if bad_rows == 0
                            else f"{bad_rows} problematic row(s) found."
                        )

            except Exception as exc:
                conn.rollback()
                status = "ERROR"
                bad_rows = None
                message = f"{check['reason']} Error: {exc}"
                print(f"{check['id']} ERROR: {exc}")

            results.append({
                "check_id": check["id"],
                "check_name": check["name"],
                "table_name": check["table"],
                "bad_rows": bad_rows,
                "status": status,
                "severity": check["severity"],
                "risk_explanation": message,
                "run_time": datetime.now(timezone.utc),
            })

        with conn.cursor() as cur:
            for result in results:
                cur.execute(
                    """
                    INSERT INTO warehouse.dq_results
                    (check_id, check_name, table_name, bad_rows, status,
                     severity, risk_explanation, run_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        result["check_id"],
                        result["check_name"],
                        result["table_name"],
                        result["bad_rows"],
                        result["status"],
                        result["severity"],
                        result["risk_explanation"],
                        result["run_time"],
                    ),
                )

        conn.commit()

    report = pd.DataFrame(results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(REPORT_PATH, index=False)

    print("\nDATA QUALITY GATEKEEPER REPORT")
    print("=" * 76)
    print(
        report[
            ["check_id", "check_name", "bad_rows", "status", "severity"]
        ].to_string(index=False)
    )
    print("\nStatus totals:")
    print(report["status"].value_counts().to_string())
    print(f"\nCSV report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    run_checks()
