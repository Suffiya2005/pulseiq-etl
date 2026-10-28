import json
import os
import re
from pathlib import Path

import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example", override=False)

st.set_page_config(
    page_title="PulseIQ Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("PulseIQ Analytics Dashboard")
st.caption(
    "Task 1 — ETL Pipeline | Task 2 — Analytics Warehouse | "
    "Task 3 — Analytics | Task 4 — Attendance Trends"
)

page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Overview",
        "Task 1 - ETL",
        "Task 2 - Warehouse",
        "Task 3 - Analytics",
        "Task 4 - Attendance Trends Analysis",
        "Task 5 - Workforce & Headcount",
        "Task 6 - Attendance & Leave Trends",
        "Task 7 - Attrition Analytics",
        "Task 8 - Team Productivity",
        "Task 9 - Payroll Cost & Reconciliation",
    ],
)

CLEAN_DIR = ROOT / os.getenv("CLEAN_DATA_DIR", "data/clean")
REJECTED_DIR = ROOT / os.getenv("REJECTED_DIR", "rejected")
SUMMARY_PATH = ROOT / os.getenv("LOG_DIR", "logs") / "run_summary.json"


def get_connection():
    return psycopg.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        dbname=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
        user=os.getenv("WAREHOUSE_USER", "pulseiq"),
        password=os.getenv("WAREHOUSE_PASSWORD", ""),
        connect_timeout=5,
    )


def warehouse_query(query, params=None):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def normalize_columns(frame):
    frame = frame.copy()
    frame.columns = [
        re.sub(
            r"[^a-z0-9]+",
            "_",
            str(column).strip().lower(),
        ).strip("_")
        for column in frame.columns
    ]
    return frame


def read_csv_safely(path):
    if not path.exists():
        return None

    try:
        return normalize_columns(pd.read_csv(path))
    except Exception as exc:
        st.warning(f"Could not read {path.name}: {exc}")
        return None


def find_column(frame, candidates, require_values=False):
    if frame is None:
        return None

    for candidate in candidates:
        if candidate in frame.columns:
            if not require_values or frame[candidate].notna().any():
                return candidate

    return None


def numeric_column(frame, column):
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":
    st.subheader("Project Overview")
    st.write(
        "Explore the PulseIQ ETL pipeline, analytics warehouse, "
        "headcount dashboard, and attendance analysis."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Task 1 — ETL Pipeline")
        st.write(
            "Clean and validate data, preview cleaned files, "
            "and review rejected records."
        )

        clean_files = (
            list(CLEAN_DIR.glob("*.csv"))
            if CLEAN_DIR.exists()
            else []
        )

        st.metric("Clean CSV datasets", len(clean_files))

    with col2:
        st.markdown("### Task 2 — Analytics Warehouse")
        st.write(
            "Explore PostgreSQL dimensions, fact tables, "
            "and business metrics."
        )

        try:
            result = warehouse_query(
                "SELECT COUNT(*) AS total "
                "FROM warehouse.fact_payroll"
            )
            st.metric(
                "Payroll records",
                f"{int(result.iloc[0]['total']):,}",
            )
            st.success("PostgreSQL connection successful")

        except Exception:
            st.warning(
                "Warehouse unavailable. Check Docker PostgreSQL "
                "and WAREHOUSE_* settings."
            )

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Task 3 — Analytics Dashboard")
        st.write(
            "Explore headcount trends, departments, role mix, "
            "joiners, leavers, and tenure."
        )
        st.link_button(
            "Open Superset",
            "http://localhost:8088",
        )

    with col4:
        st.markdown("### Task 4 — Attendance Trends Analysis")
        st.write(
            "Analyze attendance and leave patterns, compare departments, "
            "and review trends, late arrivals, and AI/ML anomalies."
        )
        st.markdown(
            "- Monthly attendance trend and 3-month rolling average\n"
            "- Department-wise attendance comparison\n"
            "- Leave days by type\n"
            "- Monthly late-arrival trend\n"
            "- AI/ML anomaly chart\n"
            "- Weekday attendance trend (synthetic demo only)"
        )
        st.info(
            "Select Task 4 - Attendance Trends Analysis in the sidebar "
            "to open the detailed dashboard."
        )
    if SUMMARY_PATH.exists():
        st.subheader("Latest ETL Run")

        try:
            st.json(
                json.loads(
                    SUMMARY_PATH.read_text(encoding="utf-8")
                )
            )
        except (json.JSONDecodeError, OSError):
            st.warning("Could not read the ETL run summary.")


# ============================================================
# TASK 1 — ETL
# ============================================================

elif page == "Task 1 - ETL":
    st.subheader("ETL Pipeline Dashboard")

    if SUMMARY_PATH.exists():
        try:
            st.markdown("### Latest ETL Run")
            st.json(
                json.loads(
                    SUMMARY_PATH.read_text(encoding="utf-8")
                )
            )
        except (json.JSONDecodeError, OSError):
            st.error("Could not read the ETL summary.")
    else:
        st.info(
            "Run the ETL pipeline first to generate the summary."
        )

    st.markdown("### Clean Data Preview")

    if CLEAN_DIR.exists():
        csv_files = sorted(CLEAN_DIR.glob("*.csv"))

        if csv_files:
            selected = st.selectbox(
                "Select clean dataset",
                csv_files,
                format_func=lambda path: path.name,
            )

            try:
                dataframe = pd.read_csv(selected)

                col1, col2 = st.columns(2)
                col1.metric("Rows", f"{len(dataframe):,}")
                col2.metric("Columns", len(dataframe.columns))

                st.dataframe(
                    dataframe.head(100),
                    use_container_width=True,
                )

                st.download_button(
                    "Download selected CSV",
                    data=selected.read_bytes(),
                    file_name=selected.name,
                    mime="text/csv",
                )

            except Exception as exc:
                st.error(f"Could not read dataset: {exc}")
        else:
            st.info("No cleaned CSV files found.")
    else:
        st.info("Clean data folder has not been created yet.")

    st.markdown("### Rejected Data")

    if REJECTED_DIR.exists():
        rejected_files = sorted(
            REJECTED_DIR.glob("*.csv")
        )

        if rejected_files:
            selected_reject = st.selectbox(
                "Select rejected file",
                rejected_files,
                format_func=lambda path: path.name,
            )

            try:
                rejected_dataframe = pd.read_csv(selected_reject)
                st.metric(
                    "Rejected rows",
                    f"{len(rejected_dataframe):,}",
                )
                st.dataframe(
                    rejected_dataframe.head(100),
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Could not read rejected file: {exc}")
        else:
            st.info("No rejected CSV files found.")
    else:
        st.info("Rejected data folder has not been created yet.")


# ============================================================
# TASK 2 — ANALYTICS WAREHOUSE
# ============================================================

elif page == "Task 2 - Warehouse":
    st.subheader("PostgreSQL Analytics Warehouse")

    table_options = [
        "dim_date",
        "dim_department",
        "dim_role",
        "dim_employee",
        "dim_leave_type",
        "fact_payroll",
        "fact_attendance_monthly",
        "fact_leave",
        "fact_headcount_monthly",
    ]

    try:
        count_frames = []

        with get_connection() as connection:
            with connection.cursor() as cursor:
                for table in table_options:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM warehouse.{table}"
                    )
                    count_frames.append(
                        {
                            "Table": table,
                            "Rows": cursor.fetchone()[0],
                        }
                    )

        st.markdown("### Warehouse Table Counts")
        st.dataframe(
            pd.DataFrame(count_frames),
            use_container_width=True,
            hide_index=True,
        )

        payroll = warehouse_query(
            """
            SELECT
                COUNT(*) AS payroll_rows,
                COUNT(DISTINCT employee_id) AS employees,
                COALESCE(SUM(gross_pay), 0) AS gross_pay,
                COALESCE(SUM(net_pay), 0) AS net_pay
            FROM warehouse.fact_payroll
            """
        )

        st.markdown("### Payroll KPIs")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Payroll Records",
            f"{int(payroll.iloc[0]['payroll_rows']):,}",
        )
        col2.metric(
            "Employees",
            f"{int(payroll.iloc[0]['employees']):,}",
        )
        col3.metric(
            "Gross Pay",
            f"₹{float(payroll.iloc[0]['gross_pay']):,.2f}",
        )
        col4.metric(
            "Net Pay",
            f"₹{float(payroll.iloc[0]['net_pay']):,.2f}",
        )

        attendance = warehouse_query(
            """
            SELECT
                COUNT(*) AS records,
                ROUND(AVG(attendance_rate)::numeric, 4) AS avg_rate
            FROM warehouse.fact_attendance_monthly
            """
        )

        st.markdown("### Attendance")
        col1, col2 = st.columns(2)

        col1.metric(
            "Attendance Records",
            f"{int(attendance.iloc[0]['records']):,}",
        )

        average_rate = attendance.iloc[0]["avg_rate"]
        col2.metric(
            "Average Attendance Rate",
            "N/A"
            if pd.isna(average_rate)
            else f"{float(average_rate) * 100:.2f}%",
        )

        leave = warehouse_query(
            """
            SELECT
                COUNT(*) AS records,
                COALESCE(SUM(days), 0) AS leave_days
            FROM warehouse.fact_leave
            """
        )

        st.markdown("### Leave")
        col1, col2 = st.columns(2)

        col1.metric(
            "Leave Requests",
            f"{int(leave.iloc[0]['records']):,}",
        )
        col2.metric(
            "Total Leave Days",
            f"{float(leave.iloc[0]['leave_days']):,.2f}",
        )

        headcount = warehouse_query(
            """
            SELECT
                COUNT(*) AS records,
                COALESCE(SUM(headcount_end), 0) AS headcount_end
            FROM warehouse.fact_headcount_monthly
            """
        )

        st.markdown("### Headcount")
        col1, col2 = st.columns(2)

        col1.metric(
            "Monthly Department Records",
            f"{int(headcount.iloc[0]['records']):,}",
        )
        col2.metric(
            "Sum of Monthly Ending Headcount",
            f"{int(headcount.iloc[0]['headcount_end']):,}",
        )

        st.markdown("### Explore Warehouse Table")
        selected_table = st.selectbox(
            "Select table",
            table_options,
        )

        preview = warehouse_query(
            f"SELECT * FROM warehouse.{selected_table} LIMIT 100"
        )

        st.dataframe(
            preview,
            use_container_width=True,
        )

        st.download_button(
            "Download table preview as CSV",
            data=preview.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_table}_preview.csv",
            mime="text/csv",
        )

    except Exception as exc:
        st.error(
            "Warehouse query failed. Check PostgreSQL is running "
            "and WAREHOUSE_* settings are correct."
        )
        st.caption(str(exc))


# ============================================================
# TASK 3 — ANALYTICS
# ============================================================

elif page == "Task 3 - Analytics":
    st.subheader("Task 3 — Superset Analytics")
    st.write(
        "Open the interactive Superset dashboard to use "
        "department filters and explore saved charts."
    )

    st.link_button(
        "Open PulseIQ Superset",
        "http://localhost:8088",
    )

    st.markdown("### Included analytics")
    st.markdown(
        "- Monthly headcount trend\n"
        "- Headcount by department\n"
        "- Role mix\n"
        "- Monthly joiners vs leavers\n"
        "- Current headcount KPI\n"
        "- Department-wise tenure distribution"
    )

    st.info(
        "Superset opens separately; the interactive charts are "
        "linked here rather than embedded inside Streamlit."
    )

    st.markdown("### C14 — Minimum Group Size Privacy Check")
    st.write(
        "Reporting groups below their metric-specific minimum "
        "are suppressed to protect employee privacy."
    )

    st.info(
        "Minimum group size: 10 for M04, M05, M06 and M27; "
        "5 for other configured metrics. Task-level metrics use "
        "a minimum of 5 tasks."
    )
    st.caption(
        "The Gatekeeper's C14 report remains the audit record "
        "of detected undersized groups. This section documents "
        "the rule; actual metric values must be suppressed at "
        "the point where those values are rendered."
    )


# ============================================================
# TASK 4 — ATTENDANCE TRENDS ANALYSIS
# ============================================================

elif page == "Task 4 - Attendance Trends Analysis":
    st.subheader("Task 4 — Attendance Trends Analysis")
    st.caption(
        "Monthly attendance, department comparisons, leave, late arrivals, "
        "AI/ML anomalies, and a clearly labelled synthetic weekday demo."
    )

    task4_dir = ROOT / "task4-attendance"
    task4_note = task4_dir / "docs" / "TASK4_ATTENDANCE_INSIGHTS.md"
    demo_candidates = [
        task4_dir / "data" / "attendance_daily_sample.csv",
        ROOT / "data" / "reference" / "attendance_daily_sample.csv",
    ]
    demo_path = next((path for path in demo_candidates if path.exists()), None)
    anomaly_path = (
        ROOT / "data" / "reference" / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
    )

    attendance_path = CLEAN_DIR / "attendance.csv"
    employees_path = CLEAN_DIR / "employees.csv"
    leave_path = CLEAN_DIR / "leave.csv"
    attendance_df = read_csv_safely(attendance_path)
    employees_df = read_csv_safely(employees_path)
    leave_df = read_csv_safely(leave_path)

    if attendance_df is None or attendance_df.empty:
        st.error(
            f"Clean attendance data was not found or is empty at {attendance_path}. "
            "Run the ETL pipeline first."
        )
    else:
        date_column = find_column(
            attendance_df, ["period_end_date", "attendance_date", "date"], require_values=True
        )
        scheduled_column = find_column(attendance_df, ["scheduled_days", "scheduled"])
        present_column = find_column(attendance_df, ["present_days", "present"])
        half_column = find_column(attendance_df, ["half_days_unpaid"])
        late_column = find_column(attendance_df, ["late_arrivals", "late_arrival"])

        if not date_column or not scheduled_column or not present_column:
            st.error(
                "Attendance data needs date, scheduled-days, and present-days columns. "
                "Detected columns: " + ", ".join(attendance_df.columns)
            )
        else:
            attendance_df[date_column] = pd.to_datetime(attendance_df[date_column], errors="coerce")
            attendance_df = attendance_df.dropna(subset=[date_column]).copy()
            attendance_df["_scheduled"] = numeric_column(attendance_df, scheduled_column)
            attendance_df["_present"] = numeric_column(attendance_df, present_column)
            attendance_df["_half"] = numeric_column(attendance_df, half_column) if half_column else 0
            attendance_df["_late"] = numeric_column(attendance_df, late_column) if late_column else 0
            attendance_df["_attendance_numerator"] = attendance_df["_present"] + 0.5 * attendance_df["_half"]
            attendance_df["_month"] = attendance_df[date_column].dt.to_period("M").dt.to_timestamp()

            # Resolve department names from attendance values first, then join employees.
            department_names = {
                "D00": "Executive Office", "D01": "Engineering", "D02": "Product & Design",
                "D03": "Data & AI", "D04": "Sales", "D05": "Marketing",
                "D06": "Customer Support", "D07": "Human Resources", "D08": "Finance & Accounts",
                "D09": "Operations & IT", "D10": "Legal & Compliance",
            }
            attendance_df["_department_name"] = pd.NA
            direct_name_col = find_column(attendance_df, ["department_name", "department", "dept_name"], require_values=True)
            if direct_name_col:
                attendance_df["_department_name"] = attendance_df[direct_name_col].astype("string").str.strip()
            else:
                direct_id_col = find_column(attendance_df, ["department_id", "dept_id"], require_values=True)
                if direct_id_col:
                    ids = attendance_df[direct_id_col].astype("string").str.strip().str.upper()
                    attendance_df["_department_name"] = ids.map(department_names).fillna(ids)

            if employees_df is not None and not employees_df.empty:
                emp_key = find_column(employees_df, ["employee_key", "employee_id", "employeeid"], require_values=True)
                emp_dept = find_column(employees_df, ["department_id", "dept_id"], require_values=True)
                emp_name = find_column(employees_df, ["department_name", "department", "dept_name"], require_values=True)
                att_key = find_column(attendance_df, ["employee_key", "employee_id", "employeeid"], require_values=True)
                if att_key and emp_key and (emp_dept or emp_name):
                    employee_map = employees_df[[emp_key] + ([emp_dept] if emp_dept else []) + ([emp_name] if emp_name else [])].copy()
                    employee_map[emp_key] = employee_map[emp_key].astype("string").str.strip()
                    employee_map = employee_map.drop_duplicates(subset=[emp_key], keep="first").set_index(emp_key)
                    att_keys = attendance_df[att_key].astype("string").str.strip()
                    if emp_name:
                        mapped_names = att_keys.map(employee_map[emp_name])
                    else:
                        mapped_ids = att_keys.map(employee_map[emp_dept]).astype("string").str.strip().str.upper()
                        mapped_names = mapped_ids.map(department_names).fillna(mapped_ids)
                    attendance_df["_department_name"] = attendance_df["_department_name"].fillna(mapped_names)

            st.markdown("### Filters")
            if attendance_df.empty:
                st.warning("No valid attendance dates are available.")
            else:
                minimum_date = attendance_df[date_column].min().date()
                maximum_date = attendance_df[date_column].max().date()
                selected_range = st.date_input(
                    "Reporting date range", value=(minimum_date, maximum_date),
                    min_value=minimum_date, max_value=maximum_date, key="task4_date_range",
                )
                filtered = attendance_df.copy()
                if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
                    start_date, end_date = selected_range
                    filtered = filtered[filtered[date_column].dt.date.between(start_date, end_date)]

                department_values = sorted(
                    filtered["_department_name"].dropna().astype(str).unique().tolist()
                )
                if department_values:
                    chosen_department = st.selectbox(
                        "Department", ["All departments"] + department_values, key="task4_department"
                    )
                    if chosen_department != "All departments":
                        filtered = filtered[filtered["_department_name"].astype(str) == chosen_department]
                else:
                    st.info("Department values could not be mapped from attendance.csv and employees.csv.")

                total_scheduled = filtered["_scheduled"].sum()
                attendance_rate = 100 * filtered["_attendance_numerator"].sum() / total_scheduled if total_scheduled else 0
                total_late = filtered["_late"].sum()
                total_records = len(filtered)
                col1, col2, col3 = st.columns(3)
                col1.metric("Weighted attendance rate", f"{attendance_rate:.2f}%")
                col2.metric("Late arrivals", f"{total_late:,.0f}")
                col3.metric("Employee-month records", f"{total_records:,}")

                st.markdown("### 1. Monthly Attendance Trend")
                monthly = (
                    filtered.groupby("_month", as_index=False)
                    .agg(scheduled_days=("_scheduled", "sum"), attendance_numerator=("_attendance_numerator", "sum"), late_arrivals=("_late", "sum"))
                    .sort_values("_month")
                )
                monthly["attendance_rate_pct"] = 100 * monthly["attendance_numerator"] / monthly["scheduled_days"].mask(monthly["scheduled_days"].eq(0))
                monthly["rolling_3_month_avg_pct"] = monthly["attendance_rate_pct"].rolling(3, min_periods=1).mean()
                if not monthly.empty:
                    trend = monthly.set_index("_month")[["attendance_rate_pct", "rolling_3_month_avg_pct"]].rename(columns={"attendance_rate_pct": "Monthly attendance %", "rolling_3_month_avg_pct": "3-month rolling average %"})
                    st.line_chart(trend)
                    monthly["mom_change_pp"] = monthly["attendance_rate_pct"].diff()
                    st.dataframe(monthly[["_month", "attendance_rate_pct", "rolling_3_month_avg_pct", "mom_change_pp"]].rename(columns={"_month": "Month", "attendance_rate_pct": "Attendance rate %", "rolling_3_month_avg_pct": "3-month rolling avg %", "mom_change_pp": "MoM change (percentage points)"}), use_container_width=True, hide_index=True)
                    st.caption("Weighted monthly rate = (present days + 0.5 × unpaid half-days) / scheduled days.")
                else:
                    st.info("No attendance records match the selected filters.")

                st.markdown("### 2. Monthly Late Arrivals")
                if not monthly.empty:
                    st.line_chart(monthly.set_index("_month")[["late_arrivals"]])

                st.markdown("### 3. Department-wise Attendance")
                department_summary = (
                    filtered.dropna(subset=["_department_name"])
                    .groupby("_department_name", as_index=False)
                    .agg(scheduled_days=("_scheduled", "sum"), attendance_numerator=("_attendance_numerator", "sum"), late_arrivals=("_late", "sum"))
                )
                if not department_summary.empty:
                    department_summary["attendance_rate_pct"] = 100 * department_summary["attendance_numerator"] / department_summary["scheduled_days"].mask(department_summary["scheduled_days"].eq(0))
                    department_summary = department_summary.dropna(subset=["attendance_rate_pct"]).sort_values("attendance_rate_pct", ascending=False)
                    if not department_summary.empty:
                        st.bar_chart(department_summary.set_index("_department_name")[["attendance_rate_pct"]])
                        highest, lowest = department_summary.iloc[0], department_summary.iloc[-1]
                        st.write(f"Highest in selected data: **{highest['_department_name']}** ({highest['attendance_rate_pct']:.2f}%). Lowest: **{lowest['_department_name']}** ({lowest['attendance_rate_pct']:.2f}%).")
                        st.dataframe(department_summary, use_container_width=True, hide_index=True)
                else:
                    st.info("Department comparison needs valid department values in employees.csv.")

                st.markdown("### 4. Leave Days by Type")
                if leave_df is not None and not leave_df.empty:
                    leave_type_column = find_column(leave_df, ["leave_type_name", "leave_type", "leave_type_code", "type"], require_values=True)
                    leave_days_column = find_column(leave_df, ["days", "leave_days", "duration_days", "leave_duration"])
                    if leave_type_column and leave_days_column:
                        leave_df["_leave_days"] = numeric_column(leave_df, leave_days_column)
                        leave_summary = leave_df.groupby(leave_type_column)["_leave_days"].sum().sort_values(ascending=False)
                        st.bar_chart(leave_summary)
                        st.dataframe(leave_summary.rename("Total leave days").reset_index(), use_container_width=True, hide_index=True)
                    else:
                        st.info("Leave file found, but leave type/day columns need review.")
                else:
                    st.info(f"Clean leave data not found at {leave_path}.")

                st.markdown("### 5. Weekday Attendance Trend — Synthetic Demo Only")

                if demo_path:
                    demo_df = read_csv_safely(demo_path)
                    if demo_df is not None and not demo_df.empty:
                        weekday_column = find_column(demo_df, ["weekday"])
                        demo_present_column = find_column(demo_df, ["present"])
                        demo_scheduled_column = find_column(demo_df, ["scheduled"])
                        demo_late_column = find_column(demo_df, ["late_arrival"])
                        if weekday_column and demo_present_column and demo_scheduled_column:
                            demo_df["_present"] = numeric_column(demo_df, demo_present_column)
                            demo_df["_scheduled"] = numeric_column(demo_df, demo_scheduled_column)
                            demo_df["_late"] = numeric_column(demo_df, demo_late_column) if demo_late_column else 0
                            weekday_summary = demo_df.groupby(weekday_column).agg(scheduled_days=("_scheduled", "sum"), present_days=("_present", "sum"), late_arrivals=("_late", "sum"))
                            weekday_summary["attendance_rate_pct"] = 100 * weekday_summary["present_days"] / weekday_summary["scheduled_days"].mask(weekday_summary["scheduled_days"].eq(0))
                            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                            weekday_summary = weekday_summary.reindex([day for day in weekday_order if day in weekday_summary.index])
                            st.bar_chart(weekday_summary[["attendance_rate_pct"]])
                            st.dataframe(weekday_summary.reset_index(), use_container_width=True, hide_index=True)
                        else:
                            st.info("Synthetic demo data exists, but expected columns were not found.")
                else:
                    st.info("Synthetic weekday sample CSV was not found.")

                st.markdown("### 6. AI/ML Attendance Anomaly Context")
                if anomaly_path.exists():
                    try:
                        anomaly_df = normalize_columns(pd.read_excel(anomaly_path, sheet_name="fact_anomaly"))
                        source_column = find_column(anomaly_df, ["source_dataset"])
                        flagged_column = find_column(anomaly_df, ["flagged"])
                        period_column = find_column(anomaly_df, ["period"])
                        if source_column and flagged_column and period_column:
                            anomaly_df = anomaly_df[
                                anomaly_df[source_column].astype(str).str.lower().eq("attendance_monthly_features")
                                & anomaly_df[flagged_column].astype(str).str.upper().eq("Y")
                            ].copy()
                            anomaly_df[period_column] = pd.to_datetime(anomaly_df[period_column], errors="coerce")
                            anomaly_df = anomaly_df.dropna(subset=[period_column])
                            anomaly_df["_month"] = anomaly_df[period_column].dt.to_period("M").dt.to_timestamp()
                            anomaly_monthly = anomaly_df.groupby("_month").size().rename("Flagged employee-month records")
                            if not anomaly_monthly.empty:
                                st.bar_chart(anomaly_monthly)
                            else:
                                st.info("No flagged attendance anomaly records were found in the workbook.")
                            st.caption("The AI/ML sample flags employee-month records, not individual days.")
                        else:
                            st.info("Anomaly workbook does not have the expected columns.")
                    except Exception as exc:
                        st.warning(f"Could not load the anomaly workbook: {exc}")
                else:
                    st.info(f"AI/ML sample workbook not found at {anomaly_path}.")

                st.markdown("### 7. HR Takeaways and Limitations")
                st.markdown(
                    "- Compare lower-attendance months with leave, public holidays, staffing coverage, and reporting completeness before acting.\n"
                    "- Department differences indicate where to review staffing and records; they do not establish causes.\n"
                    "- The supplied PulseIQ attendance source is monthly aggregated, so actual weekday attendance cannot be derived from it.\n"
                    "- The weekday chart is synthetic demonstration data, not real workforce results.\n"
                    "- AI/ML flags represent employee-month records, not individual flagged days."
                )
                if task4_note.exists():
                    with st.expander("View saved Task 4 insight note"):
                        st.markdown(task4_note.read_text(encoding="utf-8"))


# TASK 5 ? WORKFORCE & HEADCOUNT
elif page == "Task 5 - Workforce & Headcount":
    st.subheader("Task 5 ? Workforce & Headcount")
    st.caption("CEO workforce dashboard | Governed metric views only")

    department_names = {
        "D00": "Executive Office",
        "D01": "Engineering",
        "D02": "Product & Design",
        "D03": "Data & AI",
        "D04": "Sales",
        "D05": "Marketing",
        "D06": "Customer Support",
        "D07": "Human Resources",
        "D08": "Finance & Accounts",
        "D09": "Operations & IT",
        "D10": "Legal & Compliance",
    }

    try:
        headcount = warehouse_query("""
            SELECT month_start_date, department_id, headcount
            FROM warehouse.metric_m01_headcount
            ORDER BY month_start_date, department_id
        """)

        hires = warehouse_query("""
            SELECT month_start_date, department_id, hires
            FROM warehouse.metric_m02_hires
            ORDER BY month_start_date, department_id
        """)

        exits = warehouse_query("""
            SELECT month_start_date, department_id, exits
            FROM warehouse.metric_m03_exits
            ORDER BY month_start_date, department_id
        """)

        if headcount.empty:
            st.warning("No headcount records are available in the governed metric view.")
        else:
            headcount["month_start_date"] = pd.to_datetime(headcount["month_start_date"])
            hires["month_start_date"] = pd.to_datetime(hires["month_start_date"])
            exits["month_start_date"] = pd.to_datetime(exits["month_start_date"])

            min_date = headcount["month_start_date"].min().date()
            max_date = headcount["month_start_date"].max().date()

            st.markdown("### Filters")
            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                selected_departments = st.multiselect(
                    "Department",
                    options=sorted(headcount["department_id"].dropna().unique()),
                    default=sorted(headcount["department_id"].dropna().unique()),
                    format_func=lambda d: f"{d} ? {department_names.get(d, d)}",
                )

            with filter_col2:
                date_range = st.date_input(
                    "Date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )

            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = min_date, max_date

            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)

            filtered = headcount[
                headcount["department_id"].isin(selected_departments)
                & headcount["month_start_date"].between(start_ts, end_ts)
            ].copy()

            filtered_hires = hires[
                hires["department_id"].isin(selected_departments)
                & hires["month_start_date"].between(start_ts, end_ts)
            ].copy()

            filtered_exits = exits[
                exits["department_id"].isin(selected_departments)
                & exits["month_start_date"].between(start_ts, end_ts)
            ].copy()

            if filtered.empty:
                st.info("No headcount data matches the selected filters.")
            else:
                latest_month = filtered["month_start_date"].max()
                latest = filtered[filtered["month_start_date"] == latest_month]
                current_headcount = int(latest["headcount"].sum())

                previous_month = latest_month - pd.DateOffset(months=1)
                previous = filtered[filtered["month_start_date"] == previous_month]
                previous_headcount = int(previous["headcount"].sum()) if not previous.empty else None

                total_hires = int(filtered_hires["hires"].sum()) if not filtered_hires.empty else 0
                total_exits = int(filtered_exits["exits"].sum()) if not filtered_exits.empty else 0

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Latest Headcount", f"{current_headcount:,}")
                k2.metric(
                    "Month-on-Month Change",
                    "N/A" if previous_headcount is None else f"{current_headcount - previous_headcount:+,}",
                )
                k3.metric("Hires in Selected Period", f"{total_hires:,}")
                k4.metric("Exits in Selected Period", f"{total_exits:,}")

                st.markdown("### CEO Questions")
                st.markdown(
                    "1. What is our latest available workforce size?\n"
                    "2. How has headcount changed over time?\n"
                    "3. Which departments have the largest teams?\n"
                    "4. How many hires and exits occurred in the selected period?\n"
                    "5. What location-tier and work-mode data is available for workforce planning?"
                )

                st.markdown("### Headcount trend")
                trend = (
                    filtered.groupby("month_start_date", as_index=False)["headcount"]
                    .sum()
                    .sort_values("month_start_date")
                )
                st.line_chart(trend, x="month_start_date", y="headcount")
                first_value = int(trend.iloc[0]["headcount"])
                last_value = int(trend.iloc[-1]["headcount"])
                st.caption(
                    f"Insight: Headcount changed from {first_value:,} to {last_value:,} "
                    f"across the selected date range."
                )

                st.markdown("### Department workforce breakdown")
                dept = (
                    latest.groupby("department_id", as_index=False)["headcount"]
                    .sum()
                    .sort_values("headcount", ascending=False)
                )
                dept["department"] = dept["department_id"].map(department_names).fillna(dept["department_id"])
                dept_chart = dept.rename(columns={"department": "Department", "headcount": "Employees"})
                st.bar_chart(dept_chart, x="Department", y="Employees", horizontal=True)
                if not dept.empty:
                    st.caption(
                        f"Insight: {dept.iloc[0]['department']} has the largest headcount "
                        f"({int(dept.iloc[0]['headcount']):,}) in the latest selected month."
                    )

                st.markdown("### Hires and exits")
                movement = pd.merge(
                    filtered_hires.groupby("month_start_date", as_index=False)["hires"].sum(),
                    filtered_exits.groupby("month_start_date", as_index=False)["exits"].sum(),
                    on="month_start_date",
                    how="outer",
                ).fillna(0).sort_values("month_start_date")
                if not movement.empty:
                    movement_chart = movement.rename(
                        columns={"month_start_date": "Month", "hires": "Hires", "exits": "Exits"}
                    ).sort_values("Month")
                    st.line_chart(movement_chart, x="Month", y=["Hires", "Exits"])
                    st.caption(
                        f"Insight: The selected period contains {total_hires:,} hires "
                        f"and {total_exits:,} exits."
                    )
                else:
                    st.info("No hires or exits are available for the selected filters.")

                st.markdown("### Location tier and work mode")

                location_mode = warehouse_query("""
                    SELECT
                        COALESCE(l.city_tier, 'Unknown') AS city_tier,
                        COALESCE(e.work_mode, 'Unknown') AS work_mode,
                        COUNT(*) AS employees
                    FROM warehouse.dim_employee e
                    LEFT JOIN warehouse.dim_location l
                      ON e.work_location = l.work_location
                    WHERE e.is_current = TRUE
                      AND e.department_id = ANY(%s)
                    GROUP BY 1, 2
                    ORDER BY 1, 2
                """, (selected_departments,))

                tier_data = location_mode.groupby(
                    "city_tier", as_index=False
                )["employees"].sum()

                mode_data = location_mode.groupby(
                    "work_mode", as_index=False
                )["employees"].sum()

                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.markdown("#### Employees by city tier")
                    st.bar_chart(
                        tier_data,
                        x="city_tier",
                        y="employees",
                    )

                with chart_col2:
                    st.markdown("#### Employees by work mode")
                    st.bar_chart(
                        mode_data,
                        x="work_mode",
                        y="employees",
                    )

                st.caption(
                    "Counts use current employee records. Unknown values are "
                    "shown separately rather than inferred."
                )

    except Exception as exc:
        st.error(f"Task 5 dashboard could not load: {exc}")
        st.caption(
            "Check the database connection settings and availability of the Task 5 metric views."
        )



# TASK 6 - ATTENDANCE & LEAVE TRENDS
elif page == "Task 6 - Attendance & Leave Trends":
    st.subheader("Task 6 - Attendance & Leave Trends")
    st.caption(
        "Monthly attendance, leave, late arrivals, overtime "
        "and holiday context"
    )

    department_names = {
        "D00": "Executive Office",
        "D01": "Engineering",
        "D02": "Product & Design",
        "D03": "Data & AI",
        "D04": "Sales",
        "D05": "Marketing",
        "D06": "Customer Support",
        "D07": "Human Resources",
        "D08": "Finance & Accounts",
        "D09": "Operations & IT",
        "D10": "Legal & Compliance",
    }

    try:
        # ---------------------------------------------------------
        # 1. Load monthly attendance and attach department mapping
        # ---------------------------------------------------------
        attendance = warehouse_query("""
            SELECT
                DATE_TRUNC('month', a.period_end_date)::date AS month,
                COALESCE(e.department_id, 'Unknown') AS department_id,
                SUM(COALESCE(a.scheduled_days, 0)) AS scheduled_days,
                SUM(COALESCE(a.present_days, 0)) AS present_days,
                SUM(COALESCE(a.late_arrivals, 0)) AS late_arrivals
            FROM warehouse.fact_attendance_monthly a
            LEFT JOIN (
                SELECT employee_id, department_id
                FROM warehouse.dim_employee
                WHERE is_current = TRUE
            ) e
                ON e.employee_id = a.employee_id
            GROUP BY 1, 2
            ORDER BY 1, 2
        """)

        # ---------------------------------------------------------
        # 2. Load leave records by month, type, status and department
        # ---------------------------------------------------------
        leave = warehouse_query("""
            SELECT
                DATE_TRUNC('month', l.start_date)::date AS month,
                COALESCE(e.department_id, 'Unknown') AS department_id,
                COALESCE(t.leave_type_name, l.leave_type_code, 'Unknown')
                    AS leave_type,
                COALESCE(l.status, 'Unknown') AS status,
                SUM(COALESCE(l.days, 0)) AS leave_days,
                COUNT(*) AS leave_requests
            FROM warehouse.fact_leave l
            LEFT JOIN warehouse.dim_leave_type t
                ON t.leave_type_code = l.leave_type_code
            LEFT JOIN (
                SELECT employee_id, department_id
                FROM warehouse.dim_employee
                WHERE is_current = TRUE
            ) e
                ON e.employee_id = l.employee_id
            GROUP BY 1, 2, 3, 4
            ORDER BY 1, 2, 3, 4
        """)

        # ---------------------------------------------------------
        # 3. Load monthly overtime totals
        # ---------------------------------------------------------
        overtime = warehouse_query("""
            SELECT
                DATE_TRUNC('month', period_end_date)::date AS month,
                SUM(COALESCE(overtime_hours_paid, 0)) AS overtime_hours
            FROM warehouse.fact_payroll
            GROUP BY 1
            ORDER BY 1
        """)

        if attendance.empty:
            st.warning("No monthly attendance data is available.")
        else:
            for frame in (attendance, leave, overtime):
                if not frame.empty and "month" in frame.columns:
                    frame["month"] = pd.to_datetime(frame["month"])

            # Ensure numeric calculations remain safe.
            for col in ("scheduled_days", "present_days", "late_arrivals"):
                attendance[col] = pd.to_numeric(
                    attendance[col], errors="coerce"
                ).fillna(0)

            attendance["attendance_rate_pct"] = (
                100 * attendance["present_days"]
                / attendance["scheduled_days"].where(
                    attendance["scheduled_days"] > 0
                )
            )

            # -----------------------------------------------------
            # 4. Department and date filters
            # -----------------------------------------------------
            st.markdown("### Filters")

            department_options = sorted(
                attendance["department_id"].dropna().unique().tolist()
            )

            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                selected_departments = st.multiselect(
                    "Department",
                    options=department_options,
                    default=department_options,
                    format_func=lambda d: (
                        f"{d} - {department_names.get(d, d)}"
                    ),
                    key="task6_departments",
                )

            with filter_col2:
                min_month = attendance["month"].min().date()
                max_month = attendance["month"].max().date()

                selected_range = st.date_input(
                    "Month range",
                    value=(min_month, max_month),
                    min_value=min_month,
                    max_value=max_month,
                    key="task6_date_range",
                )

            if (
                isinstance(selected_range, (tuple, list))
                and len(selected_range) == 2
            ):
                start_date, end_date = selected_range
            else:
                start_date, end_date = min_month, max_month

            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)

            if start_ts > end_ts:
                st.warning("Start date must not be after end date.")
                st.stop()

            filtered = attendance[
                attendance["department_id"].isin(selected_departments)
                & attendance["month"].between(start_ts, end_ts)
            ].copy()

            filtered_leave = leave[
                leave["department_id"].isin(selected_departments)
                & leave["month"].between(start_ts, end_ts)
            ].copy() if not leave.empty else leave.copy()

            if filtered.empty:
                st.info("No attendance data matches these filters.")
            else:
                # Recalculate from summed day counts, never average
                # department/month percentages.
                monthly = (
                    filtered.groupby("month", as_index=False)
                    .agg(
                        scheduled_days=("scheduled_days", "sum"),
                        present_days=("present_days", "sum"),
                        late_arrivals=("late_arrivals", "sum"),
                    )
                    .sort_values("month")
                )

                monthly["attendance_rate_pct"] = (
                    100 * monthly["present_days"]
                    / monthly["scheduled_days"].where(
                        monthly["scheduled_days"] > 0
                    )
                )

                monthly["late_arrival_rate_pct"] = (
                    100 * monthly["late_arrivals"]
                    / monthly["scheduled_days"].where(
                        monthly["scheduled_days"] > 0
                    )
                )

                # -------------------------------------------------
                # 5. KPI summary
                # -------------------------------------------------
                total_scheduled = monthly["scheduled_days"].sum()
                total_present = monthly["present_days"].sum()
                total_late = monthly["late_arrivals"].sum()

                overall_rate = (
                    100 * total_present / total_scheduled
                    if total_scheduled > 0 else 0
                )

                valid = monthly.dropna(
                    subset=["attendance_rate_pct"]
                )

                st.markdown("### Attendance summary")

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Overall attendance", f"{overall_rate:.2f}%")
                k2.metric("Scheduled days", f"{total_scheduled:,.0f}")
                k3.metric("Present days", f"{total_present:,.0f}")
                k4.metric("Late arrivals", f"{total_late:,.0f}")

                # -------------------------------------------------
                # 6. Attendance trend and rolling average
                # -------------------------------------------------
                st.markdown("### Monthly attendance rate")
                st.caption(
                    "Weighted attendance = total present days / "
                    "total scheduled days. The source is monthly aggregated."
                )
                attendance_chart = monthly[
                    ["month", "attendance_rate_pct"]
                ].copy()

                attendance_chart = attendance_chart.rename(
                    columns={
                        "month": "Month",
                        "attendance_rate_pct": "Attendance rate (%)",
                    }
                )

                attendance_chart["3-month rolling average (%)"] = (
                    attendance_chart["Attendance rate (%)"]
                    .rolling(window=3, min_periods=1)
                    .mean()
                )

                attendance_chart["Month"] = (
                    attendance_chart["Month"].astype(str)
                )
                attendance_chart = monthly[
                    ["month", "attendance_rate_pct"]
                ].copy()

                attendance_chart = attendance_chart.rename(
                    columns={
                        "month": "Month",
                        "attendance_rate_pct": "Attendance rate (%)",
                    }
                )

                attendance_chart["3-month rolling average (%)"] = (
                    attendance_chart["Attendance rate (%)"]
                    .rolling(window=3, min_periods=1)
                    .mean()
                )

                attendance_chart["Month"] = (
                    attendance_chart["Month"].astype(str)
                )
                st.line_chart(
                    attendance_chart,
                    x="Month",
                    y=[
                        "Attendance rate (%)",
                        "3-month rolling average (%)",
                    ],
                )

                st.markdown("### Monthly late arrivals")
                st.line_chart(
                    monthly,
                    x="month",
                    y="late_arrivals",
                )


                                # Department attendance comparison
                st.markdown("### Department attendance comparison")

                dept_summary = (
                    filtered.groupby("department_id", as_index=False)
                    .agg(
                        scheduled_days=("scheduled_days", "sum"),
                        present_days=("present_days", "sum"),
                    )
                )

                dept_summary["attendance_rate_pct"] = (
                    100 * dept_summary["present_days"]
                    / dept_summary["scheduled_days"].where(
                        dept_summary["scheduled_days"] > 0
                    )
                )

                dept_summary["department"] = (
                    dept_summary["department_id"]
                    .map(department_names)
                    .fillna(dept_summary["department_id"])
                )

                dept_chart = dept_summary.rename(
                    columns={
                        "department": "Department",
                        "attendance_rate_pct": "Attendance rate (%)",
                    }
                )

                st.bar_chart(
                    dept_chart,
                    x="Department",
                    y="Attendance rate (%)",
                )

                st.dataframe(
                    dept_summary[
                        [
                            "department",
                            "scheduled_days",
                            "present_days",
                            "attendance_rate_pct",
                        ]
                    ].rename(
                        columns={
                            "department": "Department",
                            "scheduled_days": "Scheduled days",
                            "present_days": "Present days",
                            "attendance_rate_pct": "Attendance rate (%)",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                               # -------------------------------------------------
                # 7. Three objective unusual-month findings
                # -------------------------------------------------
                st.markdown("### Three unusual-month findings")

                if len(valid) >= 2:
                    baseline = overall_rate
                    unusual = valid.copy()

                    unusual["deviation_pp"] = (
                        unusual["attendance_rate_pct"] - baseline
                    )
                    unusual["absolute_deviation_pp"] = (
                        unusual["deviation_pp"].abs()
                    )

                    unusual = unusual.sort_values(
                        "absolute_deviation_pp",
                        ascending=False,
                    ).head(3)

                    for _, row in unusual.iterrows():
                        direction = (
                            "above"
                            if row["deviation_pp"] > 0
                            else "below"
                        )
                        st.write(
                            f"- **{row['month'].strftime('%B %Y')}**: "
                            f"{row['attendance_rate_pct']:.2f}% attendance, "
                            f"{abs(row['deviation_pp']):.2f} percentage "
                            f"points {direction} the selected-period "
                            f"weighted average of {baseline:.2f}%. "
                            f"Scheduled days: {row['scheduled_days']:,.0f}; "
                            f"late arrivals: {row['late_arrivals']:,.0f}."
                        )

                    st.caption(
                        "Months are ranked by absolute deviation from "
                        "the selected-period weighted attendance rate. "
                        "This identifies unusual values, not their causes."
                    )
                else:
                    st.info(
                        "At least two valid months are required for "
                        "unusual-month comparisons."
                    )

                # -------------------------------------------------
                # 8. Three numeric insights
                # -------------------------------------------------
                st.markdown("### Three numeric insights")

                if not valid.empty:
                    lowest = valid.loc[
                        valid["attendance_rate_pct"].idxmin()
                    ]
                    highest = valid.loc[
                        valid["attendance_rate_pct"].idxmax()
                    ]

                    insight_cols = st.columns(3)

                    insight_cols[0].metric(
                        "Lowest attendance month",
                        f"{lowest['attendance_rate_pct']:.2f}%",
                        lowest["month"].strftime("%b %Y"),
                    )

                    insight_cols[1].metric(
                        "Highest attendance month",
                        f"{highest['attendance_rate_pct']:.2f}%",
                        highest["month"].strftime("%b %Y"),
                    )

                    late_rate = (
                        100 * total_late / total_scheduled
                        if total_scheduled > 0
                        else 0
                    )

                    insight_cols[2].metric(
                        "Late arrivals per 100 scheduled days",
                        f"{late_rate:.2f}",
                    )
                else:
                    st.info(
                        "No valid monthly records are available "
                        "for numeric insights."
                    )

                # -------------------------------------------------
                # 9. Overtime hours
                # -------------------------------------------------
                st.markdown("### Monthly overtime hours")

                if not overtime.empty:
                    overtime_filtered = overtime[
                        overtime["month"].between(start_ts, end_ts)
                    ].copy()

                    if not overtime_filtered.empty:
                        st.line_chart(
                            overtime_filtered,
                            x="month",
                            y="overtime_hours",
                        )
                    else:
                        st.info(
                            "No overtime records match this date range."
                        )

                    st.caption(
                        "Overtime hours are summed from payroll records. "
                        "They are not split by department because that "
                        "mapping has not yet been validated."
                    )
                else:
                    st.info("No overtime records are available.")

                # -------------------------------------------------
                # 10. Leave trends and summary
                # -------------------------------------------------
                st.markdown("### Leave days by type and status")

                if not filtered_leave.empty:
                    if "leave_days" not in filtered_leave.columns:
                        if "days" in filtered_leave.columns:
                            filtered_leave = filtered_leave.rename(
                                columns={"days": "leave_days"}
                            )
                        else:
                            st.error(
                                "Leave data must contain 'days' "
                                "or 'leave_days'."
                            )
                            filtered_leave = pd.DataFrame()

                if not filtered_leave.empty:
                    leave_summary = (
                        filtered_leave.groupby(
                            ["leave_type", "status"],
                            as_index=False,
                        )
                        .agg(
                            leave_days=("leave_days", "sum"),
                            leave_requests=("leave_requests", "sum"),
                        )
                        .sort_values(
                            "leave_days",
                            ascending=False,
                        )
                    )

                    st.bar_chart(
                        leave_summary,
                        x="leave_type",
                        y="leave_days",
                        color="status",
                    )

                    st.dataframe(
                        leave_summary,
                        use_container_width=True,
                        hide_index=True,
                    )

                    approved = filtered_leave[
                        filtered_leave["status"]
                        .astype(str)
                        .str.lower()
                        .eq("approved")
                    ]

                    approved_days = (
                        approved["leave_days"].sum()
                        if not approved.empty
                        else 0
                    )

                    st.metric(
                        "Approved leave days in selected period",
                        f"{approved_days:,.1f}",
                    )

                    st.caption(
                        "Rejected and cancelled requests remain visible "
                        "in the detailed breakdown; they are not treated "
                        "as approved leave."
                    )
                else:
                    st.info(
                        "No leave records match the selected filters."
                    )

                                # -------------------------------------------------
                # 11. Daily holiday and long-weekend context
                # -------------------------------------------------
                st.markdown("### Holiday and long-weekend context")
                st.caption(
                    "Synthetic/demo daily attendance sample only."
                )

                daily = warehouse_query("""
                    SELECT
                        a.attendance_date,
                        a.department,
                        COUNT(*) AS employee_records,
                        SUM(
                            CASE
                                WHEN COALESCE(a.scheduled, 0) > 0
                                THEN 1 ELSE 0
                            END
                        ) AS scheduled_records,
                        SUM(
                            CASE
                                WHEN COALESCE(a.scheduled, 0) > 0
                                 AND COALESCE(a.present, 0) > 0
                                THEN 1 ELSE 0
                            END
                        ) AS present_records,
                        SUM(
                            CASE
                                WHEN COALESCE(a.late_arrival, 0) > 0
                                THEN 1 ELSE 0
                            END
                        ) AS late_arrivals,
                        COALESCE(BOOL_OR(d.is_holiday), FALSE)
                            AS is_holiday,
                        COALESCE(BOOL_OR(d.is_weekend), FALSE)
                            AS is_weekend,
                        COALESCE(BOOL_OR(d.is_working_day), FALSE)
                            AS is_working_day,
                        COALESCE(BOOL_OR(d.is_month_end), FALSE)
                            AS is_month_end
                    FROM warehouse.demo_attendance_daily_sample a
                    LEFT JOIN warehouse.dim_date d
                        ON d.date = a.attendance_date
                    GROUP BY a.attendance_date, a.department
                    ORDER BY a.attendance_date, a.department
                """)

                if daily is not None and not daily.empty:
                    daily = daily.copy()

                    daily["attendance_date"] = pd.to_datetime(
                        daily["attendance_date"],
                        errors="coerce",
                    )

                    daily = daily.dropna(
                        subset=["attendance_date"]
                    ).copy()

                    daily = daily[
                        daily["attendance_date"].between(
                            start_ts, end_ts
                        )
                    ].copy()

                    if selected_departments:
                        selected_department_names = {
                            department_names.get(dep, dep)
                            for dep in selected_departments
                        }
                        daily = daily[
                            daily["department"].isin(
                                selected_department_names
                            )
                        ].copy()

                    if not daily.empty:
                        for col in [
                            "is_holiday",
                            "is_weekend",
                            "is_working_day",
                            "is_month_end",
                        ]:
                            daily[col] = (
                                daily[col]
                                .fillna(False)
                                .astype(bool)
                            )

                        daily["date_only"] = (
                            daily["attendance_date"].dt.date
                        )

                        daily["attendance_rate_pct"] = (
                            100 * daily["present_records"]
                            / daily["scheduled_records"].where(
                                daily["scheduled_records"] > 0
                            )
                        )

                        calendar_days = (
                            daily[
                                [
                                    "date_only",
                                    "is_holiday",
                                    "is_weekend",
                                ]
                            ]
                            .drop_duplicates(
                                subset=["date_only"]
                            )
                            .copy()
                        )

                        from datetime import timedelta

                        weekend_dates = set(
                            calendar_days.loc[
                                calendar_days["is_weekend"],
                                "date_only",
                            ]
                        )

                        calendar_days["holiday_near_weekend"] = (
                            calendar_days.apply(
                                lambda row: (
                                    bool(row["is_holiday"])
                                    and (
                                        row["date_only"]
                                        - timedelta(days=1)
                                        in weekend_dates
                                        or row["date_only"]
                                        + timedelta(days=1)
                                        in weekend_dates
                                    )
                                ),
                                axis=1,
                            )
                        )

                        holiday_lookup = calendar_days.set_index(
                            "date_only"
                        )["holiday_near_weekend"]

                        daily["holiday_near_weekend"] = (
                            daily["date_only"]
                            .map(holiday_lookup)
                            .fillna(False)
                            .astype(bool)
                        )

                        daily["day_type"] = "Other / unknown"

                        daily.loc[
                            daily["is_working_day"],
                            "day_type",
                        ] = "Working day"

                        daily.loc[
                            daily["is_weekend"],
                            "day_type",
                        ] = "Weekend"

                        daily.loc[
                            daily["is_holiday"],
                            "day_type",
                        ] = "Holiday"

                        daily.loc[
                            daily["holiday_near_weekend"],
                            "day_type",
                        ] = "Holiday near weekend"

                        daily_context = (
                            daily.groupby(
                                "day_type",
                                as_index=False,
                            )
                            .agg(
                                dates=("date_only", "nunique"),
                                scheduled_records=(
                                    "scheduled_records", "sum"
                                ),
                                present_records=(
                                    "present_records", "sum"
                                ),
                                late_arrivals=(
                                    "late_arrivals", "sum"
                                ),
                            )
                        )

                        daily_context["attendance_rate_pct"] = (
                            100 * daily_context["present_records"]
                            / daily_context["scheduled_records"].where(
                                daily_context["scheduled_records"] > 0
                            )
                        )

                        st.dataframe(
                            daily_context,
                            use_container_width=True,
                            hide_index=True,
                        )

                        st.markdown("#### Daily sample detail")

                        st.dataframe(
                            daily[
                                [
                                    "attendance_date",
                                    "department",
                                    "day_type",
                                    "scheduled_records",
                                    "present_records",
                                    "attendance_rate_pct",
                                    "late_arrivals",
                                    "is_holiday",
                                    "is_weekend",
                                    "is_month_end",
                                ]
                            ].sort_values(
                                ["attendance_date", "department"]
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info(
                            "No daily demo records match the selected filters."
                        )
                else:
                    st.info(
                        "The daily attendance demo sample is unavailable."
                    )
    except Exception as exc:
        st.error("Task 6 - Attendance & Leave Trends could not be loaded.")
        st.exception(exc)

elif page == "Task 7 - Attrition Analytics":
    st.header("Task 7 - Attrition Analytics")
    st.caption(
        "Actual exits and attrition are shown separately from model predictions. "
        "Department-level reporting suppresses groups below 10."
    )

    try:
        # Actual monthly exits: only departments meeting the privacy threshold.
        exits = warehouse_query("""
            SELECT
                h.month_start_date,
                h.department_id,
                d.department_name,
                h.exits,
                h.voluntary_exits,
                GREATEST(h.exits - h.voluntary_exits, 0) AS other_exits
            FROM warehouse.fact_headcount_monthly h
            LEFT JOIN warehouse.dim_department d
                ON h.department_id = d.department_id
            WHERE h.headcount_start >= 10
            ORDER BY h.month_start_date, d.department_name
        """)

        rates = warehouse_query("""
            SELECT
                month_start_date,
                department_id,
                headcount_start,
                exits,
                attrition_rate_monthly_pct
            FROM warehouse.metric_m04_monthly_attrition_rate
            ORDER BY month_start_date, department_id
        """)

        risk = warehouse_query("""
            SELECT
                r.as_of_date,
                r.department_id,
                d.department_name,
                r.employees_in_group,
                r.high_risk_employees,
                r.high_risk_share_pct
            FROM warehouse.metric_m27_high_risk_share r
            LEFT JOIN warehouse.dim_department d
                ON r.department_id = d.department_id
            WHERE r.employees_in_group >= 10
            ORDER BY r.as_of_date, r.high_risk_share_pct DESC
        """)

        if exits.empty:
            st.info("No actual exit records meet the reporting threshold.")
        else:
            st.subheader("1. Actual Attrition")
            monthly = (
                exits.groupby("month_start_date", as_index=False)
                .agg(
                    exits=("exits", "sum"),
                    voluntary_exits=("voluntary_exits", "sum"),
                    other_exits=("other_exits", "sum"),
                )
                .sort_values("month_start_date")
            )

            st.markdown("**Monthly exits**")
            st.line_chart(
                monthly.set_index("month_start_date")[["exits"]]
            )

            st.dataframe(monthly, use_container_width=True, hide_index=True)

            st.markdown("**Department comparison**")
            department_summary = (
                exits.groupby(
                    ["department_id", "department_name"],
                    dropna=False,
                    as_index=False,
                )
                .agg(
                    exits=("exits", "sum"),
                    voluntary_exits=("voluntary_exits", "sum"),
                    other_exits=("other_exits", "sum"),
                )
                .sort_values("exits", ascending=False)
            )
            
            st.bar_chart(
                department_summary.set_index("department_name")[["exits"]]
            )

            st.subheader("Key Findings")
            
            total_exits = int(monthly["exits"].sum())
            total_voluntary = int(monthly["voluntary_exits"].sum())
            voluntary_pct = (
                total_voluntary / total_exits * 100
                if total_exits else 0
            )

            top_department = department_summary.iloc[0]
            peak_month = monthly.loc[monthly["exits"].idxmax()]
            peak_month_label = pd.to_datetime(
                peak_month["month_start_date"]
            ).strftime("%B %Y")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total exits", total_exits)
            col1.caption(
                f"Voluntary exits: {total_voluntary} ({voluntary_pct:.1f}%)"
            )
            col2.metric(
                "Top department",
                top_department["department_name"],
            )
            col2.caption(f"Exits: {int(top_department['exits'])}")
            col3.metric("Peak month", peak_month_label)
            col3.caption(f"Exits: {int(peak_month['exits'])}")

            st.dataframe(
                department_summary,
                use_container_width=True,
                hide_index=True,
            )


            st.markdown("**Monthly attrition rate**")
            if not rates.empty:
                rate_trend = (
                    rates.groupby("month_start_date", as_index=False)
                    .agg(
                        attrition_rate_monthly_pct=(
                            "attrition_rate_monthly_pct", "mean"
                        )
                    )
                    .sort_values("month_start_date")
                )
                st.line_chart(
                    rate_trend.set_index("month_start_date")
                )
                st.caption(
                    "The trend is the mean of eligible department-level rates; "
                    "it is not a workforce-weighted overall rate."
                )

            st.subheader("2. Exit Types")
            st.caption(
                "'Other exits' means total exits minus voluntary exits "
                "in the monthly source data."
            )
            st.markdown("**Latest 12 months of exit types**")
            exit_types_recent = monthly.tail(12).copy()

            st.dataframe(
                exit_types_recent[
                    ["month_start_date", "voluntary_exits", "other_exits"]
                ],
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("3. Tenure at Exit")

            from pathlib import Path

            employees_path = (
                Path(__file__).resolve().parent
                / "data"
                / "clean"
                / "employees.parquet"
            )

            if employees_path.exists():
                tenure_df = pd.read_parquet(employees_path)

                required_columns = {
                    "employee_id",
                    "hire_date",
                    "exit_date",
                }

                if required_columns.issubset(tenure_df.columns):
                    tenure_df["hire_date"] = pd.to_datetime(
                        tenure_df["hire_date"], errors="coerce"
                    )
                    tenure_df["exit_date"] = pd.to_datetime(
                        tenure_df["exit_date"], errors="coerce"
                    )

                    tenure_df = tenure_df.dropna(
                        subset=["employee_id", "hire_date", "exit_date"]
                    ).copy()

                    # Deduplicate employee history records.
                    tenure_df = tenure_df.drop_duplicates(
                        subset=["employee_id", "hire_date", "exit_date"]
                    )

                    date_counts = tenure_df.groupby("employee_id").agg(
                        hire_dates=("hire_date", "nunique"),
                        exit_dates=("exit_date", "nunique"),
                    )

                    consistent_ids = date_counts[
                        (date_counts["hire_dates"] == 1)
                        & (date_counts["exit_dates"] == 1)
                    ].index

                    tenure_df = tenure_df[
                        tenure_df["employee_id"].isin(consistent_ids)
                    ].drop_duplicates(subset=["employee_id"])

                    tenure_df["tenure_days_calculated"] = (
                        tenure_df["exit_date"] - tenure_df["hire_date"]
                    ).dt.days

                    tenure_df = tenure_df[
                        tenure_df["tenure_days_calculated"] >= 0
                    ].copy()

                    if not tenure_df.empty:
                        tenure_df["tenure_years_calculated"] = (
                            tenure_df["tenure_days_calculated"] / 365.25
                        )

                        labels = [
                            "Under 1 year",
                            "1–2 years",
                            "2–5 years",
                            "5–10 years",
                            "10+ years",
                        ]

                        tenure_df["tenure_bucket"] = pd.cut(
                            tenure_df["tenure_years_calculated"],
                            bins=[-0.001, 1, 2, 5, 10, float("inf")],
                            labels=labels,
                            right=False,
                        )

                        tenure_counts = (
                            tenure_df["tenure_bucket"]
                            .value_counts(sort=False)
                            .reindex(labels, fill_value=0)
                        )

                        col1, col2, col3 = st.columns(3)
                        col1.metric(
                            "Unique exited employees", f"{len(tenure_df):,}"
                        )
                        col2.metric(
                            "Average tenure",
                            f"{tenure_df['tenure_years_calculated'].mean():.2f} years",
                        )
                        col3.metric(
                            "Median tenure",
                            f"{tenure_df['tenure_years_calculated'].median():.2f} years",
                        )
                        tenure_order = [
                            "Under 1 year",
                            "1–2 years",
                            "2–5 years",
                            "5–10 years",
                            "10+ years",
                        ]

                        tenure_counts = tenure_counts.reindex(
                            tenure_order, fill_value=0
                        )

                        tenure_chart_df = pd.DataFrame({
                            "Tenure bucket": tenure_order,
                            "Employees": [
                                int(tenure_counts.get(bucket, 0))
                                for bucket in tenure_order
                            ],
                        })

                        st.bar_chart(
                            tenure_chart_df.set_index("Tenure bucket"),
                            horizontal=True,
                        )
                        st.caption(
                            "Tenure is calculated from hire_date and exit_date "
                            "in the clean employee dataset. Employee history "
                            "rows are deduplicated. This dataset may have a "
                            "different reporting scope from monthly warehouse "
                            "exit metrics."
                        )
                    else:
                        st.info(
                            "No valid employee exit records are available."
                        )
                else:
                    st.warning(
                        "Required columns are missing: employee_id, "
                        "hire_date, or exit_date."
                    )
            else:
                st.warning(
                    "The clean employees.parquet file was not found."
                )

            st.subheader("4. Predicted, not certain")

            st.warning(
                "These are model estimates, not confirmed departures. "
                "Risk scores must not be treated as proof of an employee's "
                "intent or used alone to make employment decisions."
            )

            if risk.empty:
                st.info(
                    "No prediction groups meet the minimum group size of 10."
                )
            else:
                risk_display = risk[
                    [
                        "as_of_date",
                        "department_name",
                        "employees_in_group",
                        "high_risk_employees",
                        "high_risk_share_pct",
                    ]
                ].copy()

                # Display dates without the midnight timestamp.
                risk_display["as_of_date"] = pd.to_datetime(
                    risk_display["as_of_date"], errors="coerce"
                ).dt.strftime("%Y-%m-%d")

                                # Suppress small high-risk counts and their percentages.
                # The total group size must still meet the minimum of 10.
                
                small_high_risk = (
                    risk_display["high_risk_employees"].between(1, 4)
                )
                risk_display.loc[
                    small_high_risk,
                    ["high_risk_employees", "high_risk_share_pct"],
                ] = pd.NA


                risk_display = risk_display.rename(
                    columns={
                        "as_of_date": "Prediction date",
                        "department_name": "Department",
                        "employees_in_group": "Group size",
                        "high_risk_employees": "High-risk count (suppressed if <5)",
                        "high_risk_share_pct": "High-risk share (%)",
                    }
                )

                st.dataframe(
                    risk_display,
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption(
                  "High-risk counts from 1 to 4 are suppressed. A displayed "
                  "zero means no high-risk people were recorded. Blank values "
                  "mean suppressed. Predictions are estimates only."
                )
    except Exception as exc:
        st.error("Task 7 - Attrition Analytics could not be loaded.")
        st.exception(exc)

elif page == "Task 8 - Team Productivity":
    st.header("Task 8 - Team Productivity Dashboard")
    st.caption("Team delivery across 16 teams and 38 sprints")

    st.markdown("### Metric definitions and rules")
    st.markdown(
        """
        - **Velocity:** Sum of story points for tasks with status `Done`,
          grouped by team and sprint.
        - **Cycle time:** Average recorded cycle time, in days, for `Done`
          tasks with a valid cycle-time value.
        - **On-time delivery:** Completed tasks marked `Y` divided by all
          completed tasks with a `Y` or `N` on-time flag.
        - **Blocked work:** Number of tasks whose current status is `Blocked`.
        - **Reopened work:** Sum of `reopened_count`; also show the number
          of tasks with at least one reopening.
        - **Cancelled tasks:** Excluded from completion-rate denominators
          and velocity. Report cancellation counts separately.
        """
    )

    try:
        with get_connection() as conn:
            task_df = pd.read_sql_query(
                """
                SELECT
                    record->>'task_id' AS task_id,
                    record->>'team_id' AS team_id,
                    record->>'sprint_id' AS sprint_id,
                    record->>'status' AS status,
                    record->>'task_type' AS task_type,
                    NULLIF(record->>'story_points', '')::numeric
                        AS story_points,
                    NULLIF(record->>'cycle_time_days', '')::numeric
                        AS cycle_time_days,
                    NULLIF(record->>'completed_on_time', '')
                        AS completed_on_time,
                    COALESCE(
                        NULLIF(record->>'reopened_count', '')::int, 0
                    ) AS reopened_count,
                    NULLIF(record->>'started_date', '')::date
                        AS started_date,
                    NULLIF(record->>'completed_date', '')::date
                        AS completed_date
                FROM dq_reference.fact_task
                WHERE record->>'team_id' IS NOT NULL
                  AND record->>'sprint_id' IS NOT NULL
                """,
                conn,
            )

        if task_df.empty:
            st.warning("No task records were found.")
        else:
            task_df["story_points"] = pd.to_numeric(
                task_df["story_points"], errors="coerce"
            )
            task_df["cycle_time_days"] = pd.to_numeric(
                task_df["cycle_time_days"], errors="coerce"
            )

            teams = sorted(task_df["team_id"].dropna().unique())
            sprints = sorted(
                task_df["sprint_id"].dropna().unique(),
                key=lambda value: int(value.split("-")[-1])
                if value.split("-")[-1].isdigit()
                else value,
            )

            st.subheader("Sprint selection")
            selected_sprint = st.selectbox(
                "Choose sprint",
                sprints,
                index=0,
                key="task8_sprint_selector",
            )

            sprint_df = task_df[
                task_df["sprint_id"] == selected_sprint
            ].copy()

            def summarize_team(group):
                done = group[group["status"] == "Done"]
                flagged = done[
                    done["completed_on_time"].isin(["Y", "N"])
                ]
                return pd.Series(
                    {
                        "Tasks completed": len(done),
                        "Velocity (points)": done["story_points"].sum(
                            min_count=1
                        ),
                        "Average cycle time (days)": done[
                            "cycle_time_days"
                        ].mean(),
                        "On-time tasks": (
                            flagged["completed_on_time"] == "Y"
                        ).sum(),
                        "On-time rate (%)": (
                            100
                            * (
                                flagged["completed_on_time"] == "Y"
                            ).sum()
                            / len(flagged)
                            if len(flagged)
                            else None
                        ),
                        "Blocked tasks": (
                            group["status"] == "Blocked"
                        ).sum(),
                        "Cancelled tasks": (
                            group["status"] == "Cancelled"
                        ).sum(),
                        "Reopened events": group[
                            "reopened_count"
                        ].sum(),
                        "Tasks reopened": (
                            group["reopened_count"] > 0
                        ).sum(),
                        "Planned non-cancelled tasks": (
                            group["status"] != "Cancelled"
                        ).sum(),
                    }
                )

            team_summary = (
                sprint_df.groupby("team_id", dropna=False)
                .apply(summarize_team, include_groups=False)
                .reset_index()
            )

            st.subheader(f"Team performance — {selected_sprint}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Completed tasks",
                f"{int(team_summary['Tasks completed'].sum()):,}",
            )
            c2.metric(
                "Velocity points",
                f"{team_summary['Velocity (points)'].sum():,.0f}",
            )
            c3.metric(
                "Blocked tasks",
                f"{int(team_summary['Blocked tasks'].sum()):,}",
            )
            c4.metric(
                "Cancelled tasks",
                f"{int(team_summary['Cancelled tasks'].sum()):,}",
            )

            chart_df = team_summary.set_index("team_id")
            st.markdown("**Velocity by team**")
            st.bar_chart(chart_df["Velocity (points)"])

            st.markdown("**Average cycle time by team (days)**")
            st.bar_chart(chart_df["Average cycle time (days)"])

            st.markdown("**On-time delivery rate by team (%)**")
            st.bar_chart(chart_df["On-time rate (%)"])

            st.markdown("**Blocked and reopened work by team**")
            st.bar_chart(
                chart_df[
                    [
                        "Blocked tasks",
                        "Reopened events",
                    ]
                ]
            )

            st.subheader("Team verification table")
            st.dataframe(
                team_summary.round(2),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Hand verification — T01 and T02")
            verify = team_summary[
                team_summary["team_id"].isin(["T01", "T02"])
            ]
            st.dataframe(
                verify.round(2),
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Task-type-adjusted comparison")
            st.caption(
                "Compare teams within the same task type. Story points, "
                "cycle time, blocked tasks, and reopened events are shown "
                "separately for Feature, Bug, Chore, and Spike work."
            )

            type_summary = (
                sprint_df.groupby(
                    ["team_id", "task_type"], dropna=False
                )
                .agg(
                    total_tasks=("task_id", "count"),
                    blocked_tasks=(
                        "status",
                        lambda s: (s == "Blocked").sum(),
                    ),
                    reopened_events=("reopened_count", "sum"),
                )
                .reset_index()
            )

            done_by_type = (
                sprint_df[sprint_df["status"] == "Done"]
                .groupby(["team_id", "task_type"], dropna=False)
                .agg(
                    completed_tasks=("task_id", "nunique"),
                    velocity_points=("story_points", "sum"),
                    avg_cycle_days=("cycle_time_days", "mean"),
                )
                .reset_index()
            )

            type_summary = type_summary.merge(
                done_by_type,
                on=["team_id", "task_type"],
                how="left",
            )

            st.dataframe(
                type_summary.round(2),
                use_container_width=True,
                hide_index=True,
            )

            st.info(
                "Sprint-duration limitation: the task data contract "
                "defines due_date as the sprint end date, and each of the "
                "38 sprints has one distinct due date. An authoritative "
                "sprint start date was not found, so exact sprint duration "
                "and velocity-per-day are not calculated. Compare teams "
                "within the same sprint and task type; account for team size "
                "and workload before drawing health conclusions."
            )

            st.subheader("Team health findings")
            if not team_summary.empty:
                valid_velocity = team_summary.dropna(
                    subset=["Velocity (points)"]
                )
                valid_ontime = team_summary.dropna(
                    subset=["On-time rate (%)"]
                )
                valid_cycle = team_summary.dropna(
                    subset=["Average cycle time (days)"]
                )

                if not valid_velocity.empty:
                    best_velocity = valid_velocity.loc[
                        valid_velocity["Velocity (points)"].idxmax()
                    ]
                    st.write(
                        f"1. Highest velocity in {selected_sprint}: "
                        f"{best_velocity['team_id']} delivered "
                        f"{best_velocity['Velocity (points)']:.0f} points."
                    )

                if not valid_ontime.empty:
                    best_ontime = valid_ontime.loc[
                        valid_ontime["On-time rate (%)"].idxmax()
                    ]
                    st.write(
                        f"2. Highest on-time rate in {selected_sprint}: "
                        f"{best_ontime['team_id']} at "
                        f"{best_ontime['On-time rate (%)']:.1f}%."
                    )

                if not valid_cycle.empty:
                    fastest = valid_cycle.loc[
                        valid_cycle["Average cycle time (days)"].idxmin()
                    ]
                    st.write(
                        f"3. Lowest average cycle time in {selected_sprint}: "
                        f"{fastest['team_id']} at "
                        f"{fastest['Average cycle time (days)']:.2f} days."
                    )

            st.caption(
                "Compare team size, task type, and sprint duration before "
                "drawing conclusions. Velocity alone is not a measure of "
                "team health. These findings describe the selected sprint."
            )

    except Exception as exc:
        st.error("Task 8 - Team Productivity could not be loaded.")
        st.exception(exc)



# ============================================================
# TASK 9 — PAYROLL COST & RECONCILIATION
# ============================================================
elif page == "Task 9 - Payroll Cost & Reconciliation":
    st.header("Task 9 — Payroll Cost & Reconciliation")
    st.caption(
        "Aggregate payroll reporting only. Duplicate payroll rows are excluded; "
        "groups with fewer than 5 paid employees are suppressed."
    )

    try:
        payroll = warehouse_query(
            """
            SELECT
                DATE_TRUNC('month', p.period_end_date)::date AS month,
                p.department_id,
                d.department_name,
                COUNT(DISTINCT p.employee_id) AS employees_paid,
                SUM(p.gross_pay) AS gross_pay,
                SUM(p.net_pay) AS net_pay,
                SUM(p.employer_cost) AS employer_cost,
                SUM(COALESCE(p.overtime_pay, 0)) AS overtime_pay,
                SUM(COALESCE(p.variable_pay, 0)) AS variable_pay
            FROM warehouse.fact_payroll p
            JOIN warehouse.dim_department d
              ON d.department_id = p.department_id
            WHERE p.payroll_item_id NOT IN ('PI-X0001', 'PI-X0002')
              AND p.department_id <> 'D00'
            GROUP BY 1, 2, 3
            ORDER BY 1, 2
            """
        )

        if payroll.empty:
            st.warning("No payroll data is available for this page.")
        else:
            payroll["month"] = pd.to_datetime(payroll["month"])
            numeric_cols = [
                "gross_pay", "net_pay", "employer_cost",
                "overtime_pay", "variable_pay"
            ]
            for col in numeric_cols:
                payroll[col] = pd.to_numeric(payroll[col], errors="coerce").fillna(0)

            # Suppress undersized groups before showing data or charts.
            safe = payroll.loc[payroll["employees_paid"] >= 5].copy()
            safe["cost_per_employee"] = (
                safe["employer_cost"] / safe["employees_paid"]
            )

            departments = sorted(safe["department_name"].dropna().unique())
            selected_departments = st.multiselect(
                "Departments",
                options=departments,
                default=departments,
            )
            months = sorted(safe["month"].dropna().unique())
            if months:
                selected_range = st.date_input(
                    "Month range",
                    value=(months[0].date(), months[-1].date()),
                    min_value=months[0].date(),
                    max_value=months[-1].date(),
                )
            else:
                selected_range = ()

            filtered = safe[safe["department_name"].isin(selected_departments)].copy()

            if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
                start_date, end_date = selected_range
                filtered = filtered[
                    (filtered["month"].dt.date >= start_date)
                    & (filtered["month"].dt.date <= end_date)
                ]

            if filtered.empty:
                st.info("No eligible groups match the selected filters.")
            else:
                totals = filtered.groupby("month", as_index=False).agg(
                    employees_paid=("employees_paid", "sum"),
                    gross_pay=("gross_pay", "sum"),
                    net_pay=("net_pay", "sum"),
                    employer_cost=("employer_cost", "sum"),
                    overtime_pay=("overtime_pay", "sum"),
                    variable_pay=("variable_pay", "sum"),
                )
                overall_employees = filtered["employees_paid"].sum()
                overall_cost = filtered["employer_cost"].sum()
                cost_per_employee = (
                    overall_cost / overall_employees if overall_employees else 0
                )

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Gross pay", f"₹{filtered['gross_pay'].sum():,.2f}")
                c2.metric("Net pay", f"₹{filtered['net_pay'].sum():,.2f}")
                c3.metric("Employer cost", f"₹{overall_cost:,.2f}")
                c4.metric("Cost per employee-month", f"₹{cost_per_employee:,.2f}")

                st.warning(
                    "Finance review pending: June 2026 ledger payroll-related "
                    "expense exceeds the official employer-cost figure by ₹18,450. "
                    "The payroll reconciliation matches the official answer key; "
                    "no payroll or ledger records were changed to resolve this "
                    "exception. Finance should investigate through the approved "
                    "accounting process and preserve the audit trail."
                )

                st.markdown("### Monthly payroll cost trend")
                trend = totals.sort_values("month").set_index("month")[
                    ["gross_pay", "net_pay", "employer_cost"]
                ].rename(columns={
                    "gross_pay": "Gross pay",
                    "net_pay": "Net pay",
                    "employer_cost": "Employer cost",
                })
                st.line_chart(trend)

                st.markdown("### Cost per employee-month trend")
                totals["cost_per_employee"] = (
                    totals["employer_cost"]
                    / totals["employees_paid"].replace(0, pd.NA)
                )
                st.line_chart(
                    totals.sort_values("month").set_index("month")[
                        ["cost_per_employee"]
                    ].rename(columns={"cost_per_employee": "Cost per employee-month"})
                )

                st.markdown("### Department and month breakdown")
                display = filtered.sort_values(
                    ["month", "department_name"]
                ).copy()
                display["month"] = display["month"].dt.strftime("%Y-%m")
                display = display.rename(columns={
                    "month": "Month",
                    "department_name": "Department",
                    "employees_paid": "Employees paid",
                    "gross_pay": "Gross pay",
                    "net_pay": "Net pay",
                    "employer_cost": "Employer cost",
                    "cost_per_employee": "Cost per employee-month",
                })
                st.dataframe(
                    display[
                        ["Month", "Department", "Employees paid", "Gross pay",
                         "Net pay", "Employer cost", "Cost per employee-month"]
                    ].round(2),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Cost per employee is employer cost divided by distinct paid "
                    "employees within the displayed aggregate. Leadership D00 and "
                    "the two confirmed duplicate payroll IDs are excluded."
                )

    except Exception as exc:
        st.error("Task 9 payroll dashboard could not be loaded.")
        st.exception(exc)